# Architecture Document: Customer Personalization Orchestrator

## System Overview

The Customer Personalization Orchestrator is built as a modular, agent-based system where specialized agents handle distinct responsibilities in the personalization pipeline. The system follows an orchestrated pipeline architecture with clear data flow and decision points.

## Design Principles

1. **Agent Modularity**: Each agent operates independently with well-defined interfaces
2. **Configuration-Driven**: Prompts, thresholds, and parameters externalized to config files
3. **Azure-Native**: Leverage managed Azure services for scalability and enterprise readiness
4. **Observable**: Comprehensive structured logging and audit trails at every stage
5. **Fail-Safe**: Graceful degradation with retry logic and error handling

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
         │         ├─ Process: Rule-based or K-means clustering
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
         │         ├─ Service: Azure OpenAI (gpt-4o-mini)
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
         │         ├─ Process: Random assignment, simulate engagement
         │         └─ Output: experiment results + lift metrics
         │
         └──► [6] REPORTING
                   │
                   ├─ Compile metrics, visualizations, safety audit
                   └─ Generate Jupyter notebook + PDF report
```

## Agent Specifications

### 1. Segmentation Agent

**Module**: `src/agents/segmentation_agent.py`

**Purpose**: Group customers into meaningful cohorts based on demographic and behavioral features.

**Implementation**:
- **Rule-based segmentation**: RFM-style analysis using purchase frequency, order value, and engagement
- **K-means clustering**: Alternative ML-based approach with 3-5 clusters
- **Output**: Customer assignments with segment labels and characteristics

**Key Functions**:
- `segment_customers(df, method="rules")`: Main segmentation function
- `generate_segment_summary(segments)`: Create segment metadata and statistics

### 2. Retrieval Agent

**Module**: `src/agents/retrieval_agent.py`

**Purpose**: Retrieve relevant approved content from indexed corpus to ground message generation.

**Implementation**:
- **Azure AI Search integration**: Semantic search with query construction from segment features
- **Relevance filtering**: Threshold-based filtering (>0.5) to ensure quality
- **Snippet extraction**: Word-boundary aware truncation for prompt inclusion

**Key Functions**:
- `retrieve_for_segment(segment, top_k=5)`: Main retrieval function
- `construct_query_from_segment(segment)`: Dynamic query building
- `extract_snippet(content, max_length=200)`: Content summarization

### 3. Generation Agent

**Module**: `src/agents/generation_agent.py`

**Purpose**: Generate personalized message variants using LLM with citations to retrieved content.

**Implementation**:
- **Azure OpenAI integration**: Uses gpt-4o-mini with Responses API
- **Prompt templating**: Base template with tone variations (urgent, informational, friendly)
- **Citation extraction**: Regex-based parsing and document mapping
- **Validation**: Subject length (≤60 chars), body length (150-250 words), citation requirements

**Key Functions**:
- `generate_variants(segment, content)`: Generate 3 variants with different tones
- `extract_citations(body)`: Parse and map citations to source documents
- `validate_variant_format(variant)`: Ensure output meets requirements

### 4. Safety Agent

**Module**: `src/agents/safety_agent.py`

**Purpose**: Enforce content safety policy by screening all generated variants pre-send.

**Implementation**:
- **Azure AI Content Safety integration**: Screen for hate, violence, self-harm, sexual content
- **Policy enforcement**: Block variants with severity > Medium (4)
- **Audit logging**: Immutable CSV audit trail with complete metadata
- **Fail-closed behavior**: Block on API errors to ensure safety

**Key Functions**:
- `check_safety(variant)`: Screen variant against policy
- `apply_policy_threshold(scores, threshold=4)`: Apply blocking rules
- `generate_audit_report()`: Create compliance summary

### 5. Experimentation Agent

**Module**: `src/agents/experimentation_agent.py`

**Purpose**: Orchestrate A/B/n experiments, assign customers to treatment arms, and calculate lift.

**Implementation**:
- **Experiment design**: 3 treatment arms + 1 control arm
- **Stratified assignment**: Balanced allocation within segments
- **Engagement simulation**: Realistic uplift modeling with noise
- **Statistical analysis**: T-tests, chi-square tests, confidence intervals

**Key Functions**:
- `design_experiment(variants)`: Create experiment structure
- `assign_customers_to_arms(customers, experiment)`: Stratified random assignment
- `simulate_engagement(assignments, config)`: Generate realistic engagement data
- `calculate_metrics(engagement)`: Compute lift and statistical significance

## Data Flow

### Input Data
- **Customer Dataset**: CSV with demographic and behavioral features
- **Approved Content**: JSON documents with marketing content and metadata
- **Configuration**: YAML files with prompts, thresholds, and experiment parameters

### Intermediate Data
- **Segments**: Customer assignments with segment characteristics
- **Retrieved Content**: Relevant content snippets with relevance scores
- **Generated Variants**: Personalized messages with citations and metadata
- **Safety Results**: Screening decisions with severity scores and audit trail
- **Experiment Assignments**: Customer-to-variant mappings with timestamps

### Output Data
- **Experiment Metrics**: Lift analysis with statistical significance
- **Safety Audit**: Complete compliance report
- **Feature Attribution**: Analysis of which customer attributes drive performance
- **Executive Report**: Stakeholder-ready findings and recommendations

## Technology Stack

### Core Technologies
- **Language**: Python 3.11
- **Data Processing**: Pandas, NumPy
- **ML/Clustering**: Scikit-learn
- **Visualization**: Matplotlib, Seaborn, Plotly
- **Notebooks**: Jupyter, Jupytext

### Azure Services
- **Azure OpenAI**: Message generation (gpt-4o-mini, Responses API)
- **Azure AI Search**: Content indexing and retrieval (semantic search)
- **Azure AI Content Safety**: Policy enforcement and screening
- **Azure Machine Learning**: Experiment tracking with MLflow (optional)

### Python Libraries
```python
# Core dependencies
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.7.0

# Azure SDKs
openai>=2.6.0                       # Azure OpenAI integration
azure-identity>=1.25.0              # Authentication
azure-search-documents>=11.6.0      # Azure AI Search
azure-ai-contentsafety>=1.0.0       # Content Safety

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.66.0
tenacity>=8.2.0                     # Retry logic

# Testing
pytest>=8.0.0
pytest-cov>=4.0.0
```

## Configuration Architecture

### Configuration Files
- **`config/azure_config.yaml`**: Azure service endpoints and API versions
- **`config/safety_thresholds.yaml`**: Content safety policies and thresholds
- **`config/experiment_config.yaml`**: Experiment design and parameters
- **`config/prompts/`**: LLM prompt templates and tone variations

### Environment Variables
- **Azure Credentials**: Service endpoints and API keys
- **Feature Flags**: Enable/disable optional components
- **Runtime Settings**: Logging levels, timeout values

## Security Architecture

### Authentication
- **Managed Identity**: Preferred for production deployments
- **API Keys**: Fallback for development and POC
- **Azure Key Vault**: Secure secrets management (optional)

### Data Protection
- **PII Anonymization**: Customer IDs hashed in logs
- **Audit Trails**: Immutable logging for compliance
- **Fail-Closed Safety**: Block on errors to prevent unsafe content

### Network Security
- **HTTPS Only**: All API communications encrypted
- **Private Endpoints**: Optional for production deployments
- **Network Isolation**: VNet integration for enterprise deployments

## Error Handling & Resilience

### Retry Strategy
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_if_exception_type((ConnectionError, TimeoutError))
)
def call_azure_api(client, request):
    return client.request(request)
```

### Graceful Degradation
- **Agent Isolation**: Single agent failure doesn't stop pipeline
- **Fallback Mechanisms**: Mock data for testing when services unavailable
- **Circuit Breakers**: Prevent cascade failures in production

### Monitoring & Observability
- **Structured Logging**: JSON format with correlation IDs
- **Performance Metrics**: API latency, token usage, costs
- **Health Checks**: Service availability monitoring
- **Alerting**: Critical error notifications

## Scalability Considerations

### Current Limitations (POC)
- **Sequential Processing**: No async/concurrent execution
- **Local File Storage**: CSV/JSON files instead of database
- **Single Region**: No multi-region deployment
- **Manual Scaling**: No auto-scaling capabilities

### Production Scaling (Future)
- **Async Processing**: Concurrent agent execution
- **Database Storage**: Azure Cosmos DB for persistence
- **Container Deployment**: Azure Container Apps or AKS
- **Auto-scaling**: Based on load and queue depth
- **Multi-region**: Global deployment with data residency

## Performance Characteristics

### Current Performance (POC)
- **Processing Rate**: ~400 customers/minute
- **Generation Time**: ~2 seconds per variant
- **Safety Screening**: ~0.7 seconds per variant
- **End-to-end Pipeline**: <1 hour for 500 customers

### Cost Analysis (gpt-4o-mini)
- **Input Tokens**: $0.15 per 1M tokens
- **Output Tokens**: $0.60 per 1M tokens
- **Per Customer**: ~$0.01 (full pipeline)
- **500 Customer Experiment**: ~$5-10 total

## Testing Strategy

### Unit Testing
- **Agent Testing**: Mock external dependencies
- **Integration Testing**: Real Azure service calls
- **Property-Based Testing**: Validate universal properties
- **Coverage Target**: >80% across all modules

### Test Organization
```
tests/
├── test_segmentation.py      # Segmentation agent tests
├── test_retrieval.py         # Retrieval agent tests
├── test_generation.py        # Generation agent tests
├── test_safety.py            # Safety agent tests
├── test_experimentation.py   # Experimentation agent tests
└── test_integration.py       # End-to-end tests
```

## Deployment Architecture

### Development Environment
- **Local Development**: Python virtual environment
- **Azure Services**: Development tier resources
- **Configuration**: `.env` file with API keys

### Production Environment (Future)
- **Container Platform**: Azure Container Apps
- **Service Mesh**: Istio for service communication
- **Configuration**: Azure App Configuration
- **Secrets**: Azure Key Vault
- **Monitoring**: Azure Monitor + Application Insights

## API Design

### Agent Interface Pattern
```python
class BaseAgent:
    def __init__(self, config: dict):
        self.config = config
    
    def process(self, input_data: dict) -> dict:
        """Main processing method - implemented by each agent"""
        raise NotImplementedError
    
    def validate_input(self, input_data: dict) -> bool:
        """Input validation - implemented by each agent"""
        raise NotImplementedError
```

### Error Response Format
```python
{
    "success": False,
    "error": {
        "type": "ValidationError",
        "message": "Invalid input format",
        "details": {...},
        "timestamp": "2025-11-24T10:00:00Z"
    }
}
```

## Future Architecture Evolution

### Phase 2: Production Deployment
- Real-time campaign execution
- Advanced segmentation models
- Cost optimization features
- Basic monitoring dashboards

### Phase 3: Scale & Optimization
- Multi-channel support (SMS, push)
- Real-time content indexing
- Advanced explainability (SHAP values)
- Performance optimization

### Phase 4: Enterprise Features
- Multi-tenant architecture
- Advanced RBAC and governance
- Compliance dashboards
- Model versioning and rollback

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Next Review**: Post-POC Phase