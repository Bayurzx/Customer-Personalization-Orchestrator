# Design Document: Customer Personalization Orchestrator

## Architecture Overview

The Customer Personalization Orchestrator is built as a modular, agent-based system where specialized agents handle distinct responsibilities in the personalization pipeline. The system follows an orchestrated pipeline architecture with clear data flow and decision points.

### Design Principles

1. **Agent Modularity**: Each agent (Segmentation, Retrieval, Generation, Safety, Experimentation) operates independently with well-defined interfaces
2. **Configuration-Driven**: Prompts, thresholds, and parameters externalized to config files for rapid iteration
3. **Azure-Native**: Leverage managed Azure services for scalability and enterprise readiness
4. **Observable**: Comprehensive structured logging and audit trails at every stage
5. **Fail-Safe**: Graceful degradation with retry logic and error handling

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                          │
│                      (pipeline.py)                               │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├──► [1] SEGMENTATION AGENT
         │         │
         │         ├─ Input: customers.csv
         │         ├─ Process: K-means clustering or rule-based
         │         └─ Output: segments.json
         │
         ├──► [2] RETRIEVAL AGENT
         │         │
         │         ├─ Input: segment characteristics
         │         ├─ Service: Azure AI Search
         │         └─ Output: retrieved_content (top 3-5 per segment)
         │
         ├──► [3] GENERATION AGENT
         │         │
         │         ├─ Input: segment + retrieved content + prompt template
         │         ├─ Service: Azure OpenAI (GPT-4)
         │         └─ Output: 3 message variants with citations
         │
         ├──► [4] SAFETY AGENT
         │         │
         │         ├─ Input: generated variants
         │         ├─ Service: Azure AI Content Safety
         │         ├─ Process: Screen for Hate/Violence/Self-Harm/Sexual
         │         └─ Output: pass/block decision + audit log
         │
         ├──► [5] EXPERIMENTATION AGENT
         │         │
         │         ├─ Input: approved variants
         │         ├─ Process: Random assignment, simulate send/engagement
         │         └─ Output: experiment results + lift metrics
         │
         └──► [6] REPORTING
                   │
                   ├─ Compile metrics, visualizations, safety audit
                   └─ Generate Jupyter notebook + PDF report
```

---

## Agent Specifications

### 1. Segmentation Agent

**Module**: `src/agents/segmentation_agent.py`

**Purpose**: Group customers into meaningful cohorts based on demographic and behavioral features.

**Algorithm Options**:
- **Simple (Recommended for POC)**: Rule-based segmentation (e.g., RFM analysis)
- **Advanced**: K-means clustering with 3-5 clusters

**Input Schema**:
```python
{
  "customer_id": str,
  "age": int,
  "location": str,
  "tier": str,  # e.g., "Gold", "Silver", "Bronze"
  "purchase_frequency": int,  # purchases per year
  "avg_order_value": float,
  "last_engagement_days": int,
  "historical_open_rate": float,
  "historical_click_rate": float
}
```

**Output Schema**:
```python
{
  "customer_id": str,
  "segment": str,  # e.g., "High-Value Recent"
  "segment_features": {
    "avg_purchase_frequency": float,
    "avg_order_value": float,
    "engagement_score": float
  },
  "confidence": float  # optional for ML-based segmentation
}
```

**Key Functions**:
- `load_customer_data(filepath: str) -> pd.DataFrame`
- `segment_customers(df: pd.DataFrame, method: str) -> pd.DataFrame`
- `generate_segment_summary(segments: pd.DataFrame) -> dict`

**Implementation Approach**:

```python
def segment_customers(df: pd.DataFrame, method: str = "rules") -> pd.DataFrame:
    """
    Segment customers using specified method.
    
    Args:
        df: Customer dataframe with required features
        method: "rules" for rule-based, "kmeans" for clustering
        
    Returns:
        Dataframe with segment assignments
    """
    if method == "rules":
        return _segment_by_rules(df)
    elif method == "kmeans":
        return _segment_by_clustering(df)
    else:
        raise ValueError(f"Unknown segmentation method: {method}")

def _segment_by_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Rule-based segmentation using RFM-like logic."""
    segments = []
    
    for _, customer in df.iterrows():
        # High-Value Recent: High spending + recent activity
        if (customer['avg_order_value'] > 200 and 
            customer['last_engagement_days'] < 30):
            segment = "High-Value Recent"
        
        # At-Risk: Previously active, declining engagement
        elif (customer['purchase_frequency'] > 6 and 
              customer['last_engagement_days'] > 30):
            segment = "At-Risk"
        
        # New Customer: Low purchase frequency
        elif customer['purchase_frequency'] < 3:
            segment = "New Customer"
        
        else:
            segment = "Standard"
        
        segments.append({
            "customer_id": customer['customer_id'],
            "segment": segment
        })
    
    return pd.DataFrame(segments)
```

---

### 2. Retrieval Agent

**Module**: `src/agents/retrieval_agent.py`

**Purpose**: Retrieve relevant approved content from indexed corpus to ground message generation.

**Azure Service**: Azure AI Search

**Index Schema**:
```json
{
  "document_id": "string",
  "title": "string",
  "category": "string",  # e.g., "Product", "Promotion"
  "content": "string",
  "audience": "string",  # e.g., "High-Value", "New Customer"
  "keywords": ["string"],
  "approval_date": "datetime",
  "source_url": "string"
}
```

**Retrieval Strategy**:
1. Construct query from segment characteristics (e.g., "high value premium products")
2. Use Azure AI Search's semantic search with query boosting
3. Return top 3-5 results ranked by relevance score
4. Extract snippets (150-200 words) for prompt inclusion

**Output Schema**:
```python
{
  "query": str,
  "results": [
    {
      "document_id": str,
      "title": str,
      "snippet": str,
      "relevance_score": float,
      "paragraph_index": int
    }
  ]
}
```

**Key Functions**:
- `index_content(documents: List[dict]) -> None`
- `retrieve_for_segment(segment_features: dict, top_k: int = 5) -> List[dict]`
- `extract_snippet(document: str, max_length: int = 200) -> str`

**Implementation Approach**:

```python
from azure.search.documents import SearchClient

class ContentRetriever:
    def __init__(self, search_client: SearchClient):
        self.client = search_client
    
    def retrieve_for_segment(
        self, 
        segment: dict, 
        top_k: int = 5
    ) -> List[dict]:
        """
        Retrieve relevant content for a segment.
        
        Args:
            segment: Segment information with features
            top_k: Number of results to return
            
        Returns:
            List of retrieved content with snippets
        """
        # Construct search query from segment
        query = self._construct_query(segment)
        
        # Search with semantic ranking
        results = self.client.search(
            search_text=query,
            top=top_k,
            query_type="semantic",
            semantic_configuration_name="default",
            select=["document_id", "title", "content", "category"]
        )
        
        # Extract snippets and format results
        retrieved = []
        for result in results:
            snippet = self._extract_snippet(result['content'])
            retrieved.append({
                "document_id": result['document_id'],
                "title": result['title'],
                "snippet": snippet,
                "relevance_score": result['@search.score'],
                "paragraph_index": 0  # Simplified for POC
            })
        
        return retrieved
    
    def _construct_query(self, segment: dict) -> str:
        """Construct search query from segment characteristics."""
        terms = [segment['name']]
        
        # Add feature-based terms
        if segment.get('features', {}).get('avg_order_value', 0) > 200:
            terms.append("premium")
        
        return " ".join(terms)
```

---

### 3. Generation Agent

**Module**: `src/agents/generation_agent.py`

**Purpose**: Generate personalized message variants using LLM with citations to retrieved content.

**Azure Service**: Azure OpenAI (GPT-4 or GPT-4 Turbo)

**Prompt Template Structure**:
```
You are a marketing copywriter creating personalized email messages.

CUSTOMER SEGMENT: {segment_name}
SEGMENT CHARACTERISTICS: {segment_features}

APPROVED CONTENT TO REFERENCE:
{retrieved_snippets}

TASK:
Generate an email with the following:
1. Subject line (max 60 characters)
2. Email body (150-200 words)
3. Include citations using format: [Source: Document Title, Section]

TONE: {tone}  # varies per variant: urgent, informational, friendly

REQUIREMENTS:
- Personalize based on segment characteristics
- Reference approved content with proper citations
- Include clear call-to-action
- Maintain professional, on-brand voice

OUTPUT FORMAT:
Subject: ...
Body: ...
```

**Variant Generation Strategy**:
- Generate 3 variants per segment
- Vary tone: Urgent (scarcity/time-sensitive), Informational (educational), Friendly (conversational)
- Include 2-3 citations per message body
- Track prompt tokens and generation costs

**Output Schema**:
```python
{
  "variant_id": str,
  "segment": str,
  "subject": str,
  "body": str,
  "tone": str,
  "citations": [
    {
      "document_id": str,
      "title": str,
      "paragraph_index": int
    }
  ],
  "generated_at": datetime,
  "tokens_used": int,
  "cost_usd": float
}
```

**Key Functions**:
- `load_prompt_template(template_path: str, tone: str) -> str`
- `generate_variant(segment: dict, content: List[dict], tone: str) -> dict`
- `extract_citations(body: str) -> List[dict]`
- `validate_variant_format(variant: dict) -> bool`

**Implementation Approach**:

```python
from azure.ai.openai import AzureOpenAI

class MessageGenerator:
    def __init__(self, openai_client: AzureOpenAI):
        self.client = openai_client
        self.tones = ["urgent", "informational", "friendly"]
    
    def generate_variants(
        self, 
        segment: dict, 
        content: List[dict]
    ) -> List[dict]:
        """
        Generate 3 variants with different tones.
        
        Args:
            segment: Segment information
            content: Retrieved content snippets
            
        Returns:
            List of 3 message variants
        """
        variants = []
        
        for tone in self.tones:
            prompt = self._build_prompt(segment, content, tone)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a marketing copywriter."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            variant = self._parse_response(
                response.choices[0].message.content,
                segment,
                tone,
                content
            )
            
            variant['tokens_used'] = response.usage.total_tokens
            variant['cost_usd'] = self._calculate_cost(variant['tokens_used'])
            
            variants.append(variant)
        
        return variants
    
    def _build_prompt(
        self, 
        segment: dict, 
        content: List[dict], 
        tone: str
    ) -> str:
        """Build generation prompt from template."""
        template = self._load_template(tone)
        
        # Format retrieved content
        content_text = "\n\n".join([
            f"[{c['document_id']}] {c['title']}:\n{c['snippet']}"
            for c in content
        ])
        
        return template.format(
            segment_name=segment['name'],
            segment_features=str(segment.get('features', {})),
            retrieved_snippets=content_text,
            tone=tone
        )
```

---

### 4. Safety Agent

**Module**: `src/agents/safety_agent.py`

**Purpose**: Enforce content safety policy by screening all generated variants pre-send.

**Azure Service**: Azure AI Content Safety

**Safety Categories**:
- Hate: Hate speech, discrimination
- Violence: Violent content, threats
- Self-Harm: Self-injury, suicide
- Sexual: Sexual content, exploitation

**Severity Levels** (Azure AI Content Safety):
- Safe (0)
- Low (2)
- Medium (4)
- High (6)

**Policy Threshold**: Block if ANY category severity > Medium (>4)

**Safety Check Flow**:
```
Variant → Content Safety API → Response
  ↓
Parse severity scores
  ↓
If any score > threshold:
  → Block variant
  → Log: variant_id, category, severity, timestamp
  → Update audit log
Else:
  → Approve variant
  → Log: variant_id, "pass", timestamp
```

**Output Schema**:
```python
{
  "variant_id": str,
  "status": str,  # "pass" or "block"
  "hate_severity": int,
  "violence_severity": int,
  "self_harm_severity": int,
  "sexual_severity": int,
  "block_reason": str,  # if blocked
  "checked_at": datetime
}
```

**Audit Log Format** (CSV):
```csv
timestamp,variant_id,segment,status,hate,violence,self_harm,sexual,block_reason
2025-11-20T10:30:00Z,VAR001,High-Value,pass,0,0,0,0,
2025-11-20T10:30:05Z,VAR002,At-Risk,block,6,2,0,0,Hate severity above threshold
```

**Key Functions**:
- `check_safety(variant: dict) -> dict`
- `apply_policy_threshold(scores: dict, threshold: int = 4) -> str`
- `log_safety_decision(variant_id: str, result: dict) -> None`
- `generate_audit_report() -> str`

**Implementation Approach**:

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions

class SafetyEnforcer:
    def __init__(self, safety_client: ContentSafetyClient, threshold: int = 4):
        self.client = safety_client
        self.threshold = threshold
        self.audit_log = []
    
    def check_safety(self, variant: dict) -> dict:
        """
        Check variant safety against policy.
        
        Args:
            variant: Message variant to check
            
        Returns:
            Safety check result with pass/block decision
        """
        try:
            request = AnalyzeTextOptions(text=variant['body'])
            response = self.client.analyze_text(request)
            
            # Parse severity scores
            categories = response.categories_analysis
            result = {
                "variant_id": variant['variant_id'],
                "hate_severity": categories[0].severity,
                "violence_severity": categories[1].severity,
                "self_harm_severity": categories[2].severity,
                "sexual_severity": categories[3].severity
            }
            
            # Apply threshold
            max_severity = max([
                result['hate_severity'],
                result['violence_severity'],
                result['self_harm_severity'],
                result['sexual_severity']
            ])
            
            if max_severity > self.threshold:
                result['status'] = 'block'
                result['block_reason'] = self._get_block_reason(result)
            else:
                result['status'] = 'pass'
                result['block_reason'] = None
            
            result['checked_at'] = datetime.utcnow()
            
            # Log decision
            self._log_decision(result, variant.get('segment'))
            
            return result
            
        except Exception as e:
            # Fail closed - block on error
            logger.error(f"Safety check failed: {e}")
            return {
                "variant_id": variant['variant_id'],
                "status": "block",
                "block_reason": f"API error: {str(e)}",
                "checked_at": datetime.utcnow()
            }
```

---

### 5. Experimentation Agent

**Module**: `src/agents/experimentation_agent.py`

**Purpose**: Orchestrate A/B/n experiments, assign customers to treatment arms, simulate engagement, and calculate lift.

**Experiment Design**:
- **Control Arm**: Generic baseline message (same for all segments)
- **Treatment Arms**: 3-4 message variants (personalized per segment)
- **Assignment**: Stratified random assignment within segments

**Assignment Strategy**:
```python
def assign_customers(customers: List[dict], variants: List[dict]) -> List[dict]:
    """
    Stratified random assignment:
    1. Group customers by segment
    2. Within each segment, randomly assign to:
       - Control (25%)
       - Treatment 1 (25%)
       - Treatment 2 (25%)
       - Treatment 3 (25%)
    """
    assignments = []
    for segment in segments:
        segment_customers = filter_by_segment(customers, segment)
        shuffle(segment_customers)
        
        n = len(segment_customers)
        control_size = n // 4
        
        assignments.extend([
            {"customer_id": c, "arm": "control", "variant_id": "control"} 
            for c in segment_customers[:control_size]
        ])
        assignments.extend([
            {"customer_id": c, "arm": f"treatment_{i}", "variant_id": v} 
            for i, (c, v) in enumerate(zip(segment_customers[control_size:], variants))
        ])
    
    return assignments
```

**Engagement Simulation**:
```python
def simulate_engagement(assignments: List[dict], baseline_rates: dict) -> List[dict]:
    """
    Option A: Use historical engagement labels from dataset
    Option B: Simulate with uplift bias for personalized variants
    
    Simulation model:
    - Control: baseline_open_rate, baseline_click_rate
    - Treatment: baseline * (1 + uplift_factor)
    - uplift_factor ~ N(0.10, 0.05)  # 10% mean lift, 5% std
    """
    engagement = []
    for assignment in assignments:
        if assignment["arm"] == "control":
            open_prob = baseline_rates["open_rate"]
            click_prob = baseline_rates["click_rate"]
        else:
            uplift = random.gauss(0.10, 0.05)
            open_prob = baseline_rates["open_rate"] * (1 + uplift)
            click_prob = baseline_rates["click_rate"] * (1 + uplift)
        
        engagement.append({
            "customer_id": assignment["customer_id"],
            "variant_id": assignment["variant_id"],
            "opened": random.random() < open_prob,
            "clicked": random.random() < click_prob,
            "converted": False  # placeholder for future
        })
    
    return engagement
```

**Metrics Calculation**:
```python
def calculate_lift(treatment_metric: float, control_metric: float) -> float:
    """
    Relative lift formula:
    lift = (treatment - control) / control * 100%
    """
    return (treatment_metric - control_metric) / control_metric * 100

def calculate_statistical_significance(treatment_data, control_data):
    """
    Two-sample t-test for continuous metrics (e.g., click rate)
    Chi-square test for binary outcomes (e.g., opened yes/no)
    """
    from scipy import stats
    
    # For proportions (open rate, click rate)
    t_stat, p_value = stats.ttest_ind(treatment_data, control_data)
    
    return {
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": p_value < 0.05
    }
```

**Output Schema**:
```python
{
  "experiment_id": str,
  "arms": [
    {
      "arm_name": str,  # "control", "treatment_1", etc.
      "sample_size": int,
      "open_rate": float,
      "click_rate": float,
      "conversion_rate": float
    }
  ],
  "lift_analysis": [
    {
      "treatment_arm": str,
      "metric": str,  # "open_rate", "click_rate"
      "lift_percent": float,
      "p_value": float,
      "significant": bool
    }
  ],
  "segment_breakdown": [
    {
      "segment": str,
      "best_performing_arm": str,
      "lift_percent": float
    }
  ]
}
```

**Key Functions**:
- `design_experiment(variants: List[dict]) -> dict`
- `assign_customers_to_arms(customers: List[dict], experiment: dict) -> List[dict]`
- `simulate_engagement(assignments: List[dict]) -> List[dict]`
- `calculate_metrics(engagement: List[dict]) -> dict`
- `calculate_lift_and_significance(metrics: dict) -> dict`

---

## Data Flow Sequence Diagram

```
User/Script           Orchestrator         Segmentation    Retrieval    Generation    Safety    Experimentation    Reporting
    |                      |                     |             |             |            |             |               |
    |--run_experiment----->|                     |             |             |            |             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--load_customers---->|             |             |            |             |               |
    |                      |<---segments---------|             |             |            |             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--retrieve_content------------------>            |            |             |               |
    |                      |<---content_snippets----------------|            |            |             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--generate_variants----------------------->     |            |             |               |
    |                      |<---variants (3 per segment)------------------|  |            |             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--check_safety (per variant)---------------------->          |             |               |
    |                      |<---pass/block decisions-----------------------------|        |             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--design_experiment (approved variants only)---------------->|             |               |
    |                      |<---experiment_results---------------------------------------|             |               |
    |                      |                     |             |             |            |             |               |
    |                      |--generate_report----------------------------------------------------------------->        |
    |                      |<---report.ipynb + report.pdf-----------------------------------------------------------|
    |                      |                     |             |             |            |             |               |
    |<--experiment_complete|                     |             |             |            |             |               |
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | **3.11** | Primary development language |
| **Orchestration** | Custom Python scripts | - | Pipeline coordination |
| **Data Processing** | Pandas, NumPy | Latest | Data manipulation and analysis |
| **ML/Clustering** | Scikit-learn | Latest | K-means clustering for segmentation |

### Azure Services

| Service | Purpose | API Version |
|---------|---------|-------------|
| **Azure OpenAI** | Message generation with GPT-4 | 2025-11-01-preview |
| **Azure AI Search** | Content indexing and retrieval | 2024-11-01-preview |
| **Azure AI Content Safety** | Safety policy enforcement | Latest Stable |
| **Azure Monitor** (Optional) | Logging and telemetry | Latest |
| **Azure ML** (Optional) | Experiment tracking with MLflow | Latest |

### Python Libraries

```python
# Core
python>=3.11
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.4.0

# Azure SDKs
azure-ai-openai>=1.50.0
azure-search-documents>=11.6.0
azure-ai-contentsafety>=1.0.0
azure-identity>=1.16.0

# Visualization
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.20.0

# Notebook
jupyter>=1.0.0
ipykernel>=6.29.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.66.0

# Testing
pytest>=8.0.0
pytest-cov>=5.0.0
```

---

## Configuration Files

### 1. Azure Configuration (`config/azure_config.yaml`)

```yaml
azure_openai:
  endpoint: https://<resource-name>.openai.azure.com/
  api_version: "2025-11-01-preview"
  deployment_name: gpt-4  # or gpt-4-turbo
  max_tokens: 1000
  temperature: 0.7
  top_p: 0.9

azure_search:
  endpoint: https://<search-service>.search.windows.net
  api_version: "2024-11-01-preview"
  index_name: approved-content
  semantic_configuration: default

azure_content_safety:
  endpoint: https://<resource-name>.cognitiveservices.azure.com/
  api_version: "2023-10-01"

authentication:
  method: managed_identity  # or api_key, azure_cli
```

### 2. Safety Thresholds (`config/safety_thresholds.yaml`)

```yaml
safety_policy:
  threshold: 4  # Block if severity > Medium (4)
  categories:
    - hate
    - violence
    - self_harm
    - sexual
  
  severity_levels:
    safe: 0
    low: 2
    medium: 4
    high: 6
  
  audit_logging:
    enabled: true
    log_file: logs/safety_audit.log
    format: csv
```

### 3. Experiment Configuration (`config/experiment_config.yaml`)

```yaml
experiment:
  name: personalization_poc_v1
  description: A/B/n test of personalized variants vs generic control
  
  design:
    num_treatment_arms: 3  # per segment
    control_arm: true
    assignment_strategy: stratified_random
    
  sample_allocation:
    control_percent: 25
    treatment_percent: 75  # split across 3 arms
  
  metrics:
    primary: click_rate
    secondary:
      - open_rate
      - conversion_rate
  
  statistical_testing:
    alpha: 0.05  # significance level
    test_type: t-test  # or chi-square
    
  simulation:
    use_historical_data: false  # true if available
    baseline_open_rate: 0.25
    baseline_click_rate: 0.05
    expected_uplift: 0.10  # 10% mean uplift
    uplift_std: 0.05
```

---

## Error Handling and Resilience

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def call_azure_api(client, request):
    """
    Retry logic for Azure API calls:
    - Max 3 attempts
    - Exponential backoff: 2s, 4s, 8s
    - Reraise exception if all retries fail
    """
    return client.request(request)
```

### Graceful Degradation

```python
def process_customer_batch(customers: List[dict]) -> List[dict]:
    """
    Process customers with error isolation:
    - If one customer fails, log error and continue
    - Collect all errors for final summary
    - Don't let single failure block entire pipeline
    """
    results = []
    errors = []
    
    for customer in customers:
        try:
            result = process_single_customer(customer)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {customer['id']}: {e}")
            errors.append({"customer_id": customer["id"], "error": str(e)})
            continue
    
    if errors:
        logger.warning(f"Completed with {len(errors)} errors")
    
    return results, errors
```

---

## Security Considerations

### PII Handling

1. **Anonymization**: Use hashed customer IDs in logs, never email/name
2. **Data Minimization**: Only load features needed for segmentation
3. **Secure Storage**: No customer data persisted long-term in POC

### API Key Management

```python
# Read from environment variables
import os
from azure.identity import DefaultAzureCredential

# Option 1: Environment variables
openai_key = os.getenv("AZURE_OPENAI_API_KEY")

# Option 2: Azure Managed Identity (recommended for production)
credential = DefaultAzureCredential()
```

### Audit Trail Integrity

```python
import json
from datetime import datetime
import hashlib

def log_audit_entry(variant_id: str, decision: dict):
    """
    Create append-only, immutable audit log entry
    - Include timestamp
    - Hash entry for integrity verification
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "variant_id": variant_id,
        "decision": decision
    }
    
    # Calculate hash for integrity
    entry_hash = hashlib.sha256(json.dumps(entry).encode()).hexdigest()
    entry["hash"] = entry_hash
    
    # Append to log file (never overwrite)
    with open("logs/safety_audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

---

## Testing Strategy

### Unit Tests

- **Segmentation**: Test clustering convergence, segment assignment
- **Retrieval**: Mock Azure AI Search, test query construction
- **Generation**: Mock OpenAI API, validate prompt formatting, citation extraction
- **Safety**: Mock Content Safety API, test threshold application
- **Experimentation**: Test random assignment distribution, lift calculation

### Integration Tests

- **End-to-End Pipeline**: Run full workflow on small sample dataset (10 customers)
- **Azure Service Integration**: Test actual API calls (use test accounts)
- **Configuration Loading**: Verify YAML parsing and validation

### Sample Test Cases

```python
def test_segmentation_assigns_all_customers():
    customers = load_sample_customers(n=50)
    segments = segment_customers(customers)
    assert len(segments) == len(customers)
    assert all(s["segment"] in ["High-Value", "At-Risk", "New"] for s in segments)

def test_safety_blocks_high_severity():
    variant = {"body": "This is offensive content"}
    result = check_safety(variant)
    assert result["status"] == "block"
    assert result["hate_severity"] > 4

def test_lift_calculation():
    treatment_rate = 0.30
    control_rate = 0.25
    lift = calculate_lift(treatment_rate, control_rate)
    assert lift == 20.0  # 20% lift
```

---

## Monitoring and Observability

### Key Metrics to Track

1. **Pipeline Execution**:
   - Total runtime
   - Customers processed
   - Variants generated

2. **Azure Service Metrics**:
   - API call latency (p50, p95, p99)
   - API error rate
   - Token usage and costs

3. **Safety Metrics**:
   - Pass rate
   - Block rate by category
   - Most common block reasons

4. **Experiment Metrics**:
   - Lift by segment
   - Statistical significance
   - Best-performing variants

### Logging Structure

```python
import logging
import json

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)

def log_structured(event: str, data: dict):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "data": data
    }
    logging.info(json.dumps(log_entry))

# Usage
log_structured("variant_generated", {
    "variant_id": "VAR001",
    "segment": "High-Value",
    "tokens": 250,
    "cost_usd": 0.005
})
```

---

## Deployment and Operationalization Considerations

### Phase 1: POC (Week 1)
- Local Python execution
- Jupyter notebooks for reporting
- Manual triggering via scripts

### Phase 2: Production Readiness (Future)
- Containerize with Docker
- Deploy to Azure Container Instances or AKS
- Integrate with email service provider (SendGrid, Mailchimp)
- Schedule with Azure Functions or Logic Apps

### Phase 3: Enterprise Scale (Future)
- Multi-tenant architecture
- Real-time content updates
- Continuous evaluation with Azure AI Foundry Observability
- Cost optimization (caching, batching)
- CI/CD pipeline with GitHub Actions

---

## Architecture Decision Records (ADRs)

### ADR-001: Agent-Based Architecture
**Status**: Accepted  
**Context**: Need modular, testable system with clear separation of concerns  
**Decision**: Implement specialized agents (Segmentation, Retrieval, Generation, Safety, Experimentation)  
**Consequences**: 
- ✅ Easy to test and maintain
- ✅ Can parallelize agent execution in future
- ⚠️ Requires orchestration layer
- ⚠️ Inter-agent communication overhead

### ADR-002: Azure-Native Services
**Status**: Accepted  
**Context**: Need enterprise-grade AI services with compliance  
**Decision**: Use Azure OpenAI, Azure AI Search, Azure AI Content Safety  
**Consequences**:
- ✅ Enterprise security and compliance
- ✅ Managed services reduce operational burden
- ⚠️ Vendor lock-in to Azure
- ⚠️ API costs can be significant at scale

### ADR-003: Configuration-Driven Design
**Status**: Accepted  
**Context**: Need rapid iteration on prompts and parameters  
**Decision**: Externalize all prompts, thresholds, and configs to YAML/text files  
**Consequences**:
- ✅ Non-engineers can update prompts
- ✅ Easy A/B testing of prompts
- ⚠️ Requires validation logic
- ⚠️ Version control complexity

### ADR-004: Synchronous Pipeline (POC)
**Status**: Accepted (POC only)  
**Context**: Need simple, debuggable execution for POC  
**Decision**: Sequential synchronous execution; no async or distributed processing  
**Consequences**:
- ✅ Simple to debug and reason about
- ✅ Faster to implement
- ⚠️ Won't scale to production (Phase 2 will need async)
- ⚠️ Longer execution time for large datasets

### ADR-005: Local Data Storage (POC)
**Status**: Accepted (POC only)  
**Context**: POC doesn't need production database  
**Decision**: Use local CSV/JSON files for data persistence  
**Consequences**:
- ✅ No database setup overhead
- ✅ Easy to inspect and debug
- ⚠️ Not suitable for production
- ⚠️ No concurrent access support

---

## Component Interaction Details

### Orchestrator Module

**File**: `src/orchestrator/pipeline.py`

```python
"""
Main orchestration pipeline for Customer Personalization Orchestrator.
"""

import logging
from typing import Dict, List
from datetime import datetime

from src.agents.segmentation_agent import SegmentationAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.generation_agent import GenerationAgent
from src.agents.safety_agent import SafetyAgent
from src.agents.experimentation_agent import ExperimentationAgent

logger = logging.getLogger(__name__)

class PersonalizationPipeline:
    """
    Main pipeline orchestrating all agents.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Configuration dictionary with all settings
        """
        self.config = config
        self.segmentation = SegmentationAgent()
        self.retrieval = RetrievalAgent(config['azure_search'])
        self.generation = GenerationAgent(config['azure_openai'])
        self.safety = SafetyAgent(config['azure_content_safety'])
        self.experimentation = ExperimentationAgent()
        
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "customers_processed": 0,
            "variants_generated": 0,
            "variants_blocked": 0,
            "total_cost_usd": 0.0
        }
    
    def run(self, customer_data_path: str) -> Dict:
        """
        Execute full pipeline.
        
        Args:
            customer_data_path: Path to customer CSV file
            
        Returns:
            Dictionary with experiment results
        """
        self.metrics['start_time'] = datetime.utcnow()
        logger.info("Pipeline execution started")
        
        # Step 1: Segmentation
        logger.info("Step 1: Segmentation")
        segments = self.segmentation.segment_customers(customer_data_path)
        self.metrics['customers_processed'] = len(segments)
        logger.info(f"Segmented {len(segments)} customers into {segments['segment'].nunique()} segments")
        
        # Step 2: Content Retrieval
        logger.info("Step 2: Content Retrieval")
        retrieved_content = {}
        for segment_name in segments['segment'].unique():
            segment_features = self._get_segment_features(segments, segment_name)
            content = self.retrieval.retrieve_for_segment(segment_features)
            retrieved_content[segment_name] = content
            logger.info(f"Retrieved {len(content)} content pieces for {segment_name}")
        
        # Step 3: Message Generation
        logger.info("Step 3: Message Generation")
        variants = []
        for segment_name, content in retrieved_content.items():
            segment_features = self._get_segment_features(segments, segment_name)
            segment_variants = self.generation.generate_variants(segment_features, content)
            variants.extend(segment_variants)
            self.metrics['variants_generated'] += len(segment_variants)
            logger.info(f"Generated {len(segment_variants)} variants for {segment_name}")
        
        # Step 4: Safety Screening
        logger.info("Step 4: Safety Screening")
        approved_variants = []
        for variant in variants:
            safety_result = self.safety.check_safety(variant)
            if safety_result['status'] == 'pass':
                approved_variants.append(variant)
            else:
                self.metrics['variants_blocked'] += 1
                logger.warning(f"Blocked variant {variant['variant_id']}: {safety_result['block_reason']}")
        
        pass_rate = len(approved_variants) / len(variants) if variants else 0
        logger.info(f"Safety screening: {len(approved_variants)}/{len(variants)} passed ({pass_rate:.1%})")
        
        # Step 5: Experimentation
        logger.info("Step 5: Experimentation")
        experiment_results = self.experimentation.run_experiment(
            customers=segments,
            variants=approved_variants,
            config=self.config['experiment']
        )
        logger.info(f"Experiment complete: {len(experiment_results['arms'])} arms evaluated")
        
        # Calculate total cost
        self.metrics['total_cost_usd'] = sum(v.get('cost_usd', 0) for v in variants)
        
        self.metrics['end_time'] = datetime.utcnow()
        runtime = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        logger.info(f"Pipeline execution completed in {runtime:.1f} seconds")
        
        return {
            "experiment_results": experiment_results,
            "metrics": self.metrics,
            "safety_report": self.safety.generate_audit_report()
        }
    
    def _get_segment_features(self, segments_df, segment_name: str) -> Dict:
        """Extract features for a segment."""
        segment_data = segments_df[segments_df['segment'] == segment_name]
        return {
            "name": segment_name,
            "size": len(segment_data),
            "features": {
                "avg_order_value": segment_data['avg_order_value'].mean(),
                "avg_purchase_frequency": segment_data['purchase_frequency'].mean(),
                "avg_engagement_recency": segment_data['last_engagement_days'].mean()
            }
        }
```

---

## Configuration Management

### Configuration Loader

**File**: `src/orchestrator/config.py`

```python
"""
Configuration management for the pipeline.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """Load and validate configuration files."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all configuration files.
        
        Returns:
            Dictionary with all configurations
        """
        config = {
            "azure_openai": self._load_yaml("azure_config.yaml")['azure_openai'],
            "azure_search": self._load_yaml("azure_config.yaml")['azure_search'],
            "azure_content_safety": self._load_yaml("azure_config.yaml")['azure_content_safety'],
            "safety_thresholds": self._load_yaml("safety_thresholds.yaml"),
            "experiment": self._load_yaml("experiment_config.yaml")['experiment']
        }
        
        # Load prompts
        config['prompts'] = self._load_prompts()
        
        # Validate configuration
        self._validate(config)
        
        return config
    
    def _load_yaml(self, filename: str) -> Dict:
        """Load YAML configuration file."""
        path = self.config_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path) as f:
            return yaml.safe_load(f)
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates."""
        prompts_dir = self.config_dir / "prompts"
        prompts = {}
        
        for prompt_file in prompts_dir.glob("*.txt"):
            with open(prompt_file) as f:
                prompts[prompt_file.stem] = f.read()
        
        return prompts
    
    def _validate(self, config: Dict):
        """Validate configuration completeness."""
        required_keys = [
            "azure_openai", "azure_search", "azure_content_safety",
            "safety_thresholds", "experiment", "prompts"
        ]
        
        missing = [k for k in required_keys if k not in config]
        if missing:
            raise ValueError(f"Missing required configuration keys: {missing}")
```

---

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
import hashlib
import json

class CachedRetriever:
    """Retrieval agent with caching."""
    
    def __init__(self, base_retriever):
        self.retriever = base_retriever
        self._cache = {}
    
    def retrieve_for_segment(self, segment: Dict) -> List[Dict]:
        """Retrieve with caching."""
        # Create cache key from segment features
        cache_key = self._make_cache_key(segment)
        
        if cache_key in self._cache:
            logger.debug(f"Cache hit for segment: {segment['name']}")
            return self._cache[cache_key]
        
        # Cache miss - retrieve from search
        results = self.retriever.retrieve_for_segment(segment)
        self._cache[cache_key] = results
        
        return results
    
    def _make_cache_key(self, segment: Dict) -> str:
        """Generate cache key from segment."""
        key_data = json.dumps(segment['features'], sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
```

### Batch Processing

```python
def process_in_batches(items: List, batch_size: int = 10):
    """Process items in batches to manage API rate limits."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        yield batch
        
        # Rate limiting pause
        time.sleep(1)  # 1 second between batches
```

---

## API Integration Patterns

### Azure OpenAI Client Wrapper

```python
from azure.ai.openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustOpenAIClient:
    """OpenAI client with retry and error handling."""
    
    def __init__(self, endpoint: str, deployment: str):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2025-11-01-preview",
            azure_ad_token_provider=DefaultAzureCredential()
        )
        self.deployment = deployment
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(self, messages: List[Dict], **kwargs) -> Dict:
        """Generate with automatic retry."""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                **kwargs
            )
            
            return {
                "text": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
```

---

## Data Flow Examples

### Example 1: Single Customer Journey

```
Customer CUST001 (Gold tier, recent purchase)
  ↓
Segmentation Agent → "High-Value Recent" segment
  ↓
Retrieval Agent → Fetches 5 relevant content pieces about premium features
  ↓
Generation Agent → Creates 3 variants (urgent, informational, friendly)
  Variant 1: "Exclusive offer ending soon!" (urgent tone)
  Variant 2: "New features you'll love" (informational)
  Variant 3: "Thanks for being a valued customer" (friendly)
  ↓
Safety Agent → Screens all 3 variants
  Variant 1: PASS (all severity scores = 0)
  Variant 2: PASS (all severity scores = 0)
  Variant 3: PASS (all severity scores = 0)
  ↓
Experimentation Agent → Assigns to Treatment Arm 2 (gets Variant 2)
  ↓
Engagement Simulation → Opens email (simulated)
  ↓
Results → Contributes to Treatment Arm 2 metrics
```

### Example 2: Blocked Content Flow

```
Variant VAR042 generated for "At-Risk" segment
  ↓
Safety Agent checks content
  ↓
Detection: Hate severity = 6 (High)
  ↓
Decision: BLOCK
  ↓
Audit Log: timestamp, VAR042, At-Risk, block, 6, 0, 0, 0, "Hate severity above threshold"
  ↓
Variant excluded from experiment
  ↓
Customer receives control message instead
```

---

## Open Questions and Future Considerations

### Open Questions

1. **Segmentation Method**: Rule-based (RFM) vs K-means clustering?
   - **Decision**: Start with rule-based for simplicity, validate with stakeholders

2. **Engagement Simulation**: Use historical data or synthetic?
   - **Decision**: If historical data available, use it; otherwise simulate with realistic distributions

3. **Report Format**: Jupyter notebook, PDF, or both?
   - **Decision**: Both - notebook for interactivity, PDF for stakeholder distribution

4. **Cost Tracking**: Log token usage and estimate costs?
   - **Decision**: Yes - track all API calls for cost transparency

### Future Considerations

**Phase 2 Enhancements**:
- Async agent execution for better performance
- Real-time email integration
- Advanced ML segmentation models
- Cost optimization (caching, batching)

**Phase 3 Scale**:
- Multi-tenant architecture
- Real-time content updates
- Continuous evaluation with Azure AI Foundry Observability
- Advanced explainability (SHAP values)

**Enterprise Readiness**:
- SSO and RBAC integration
- Compliance reporting dashboards
- Multi-channel support (SMS, push)
- Integration with marketing automation platforms

---

## Success Criteria

This design is successful if:

1. ✅ All 6 agents implemented and functional
2. ✅ End-to-end pipeline executes in <1 hour for 100-500 customers
3. ✅ >90% safety pass rate
4. ✅ Demonstrates >10% lift in at least one metric
5. ✅ Complete audit trail and experiment report generated
6. ✅ Code is modular, documented, and testable

---

**Document Status**: Final v1.0  
**Last Updated**: November 21, 2025  
**Architecture Review**: Approved  
**Security Review**: Approved  
**Next Review**: End of Day 5 (Project Completion)