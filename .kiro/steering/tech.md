# Technical Steering: Customer Personalization Orchestrator

## Overview

This document defines the technology stack, development tools, coding standards, and technical decisions for the Customer Personalization Orchestrator project as of November 2025.

---

## Technology Stack

### Core Platform
- **Language**: Python 3.9+ (Recommended: Python 3.11 for performance)
- **Package Manager**: `pip` with `requirements.txt` or `pyproject.toml`
- **Virtual Environment**: `venv` (built-in) or `conda`
- **Version Control**: Git + GitHub

### Azure Services (Primary Stack)

| Service | Purpose | Package | Version |
|---------|---------|---------|---------|
| **Azure OpenAI** | Message generation (Responses API) | `openai` | >=1.55.0 |
| **Azure AI Search** | Content retrieval | `azure-search-documents` | >=11.6.0 |
| **Azure AI Content Safety** | Safety enforcement | `azure-ai-contentsafety` | >=1.0.0 |
| **Azure Machine Learning** | Experiment tracking | `azure-ai-ml`, `mlflow` | Latest |
| **Azure Monitor** | Telemetry & logging | `azure-monitor-opentelemetry` | Latest |
| **Azure Key Vault** | Secrets management | `azure-keyvault-secrets` | Latest |

**Authentication Standard**: `DefaultAzureCredential` from `azure-identity>=1.19.0`

### Python Dependencies

```python
# requirements.txt
# Last updated: November 2025
# Python: 3.9+

# Core Data Science
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.7.0
scipy>=1.11.0

# Azure SDK (Modern Stack - November 2025)
openai>=2.6.0                       # Azure OpenAI (unified package) - Latest: 2.8.1
azure-identity>=1.25.0              # Authentication - Latest: 1.25.1
azure-search-documents>=11.6.0      # Azure AI Search - Latest: 11.6.0
azure-ai-contentsafety>=1.0.0       # Content Safety - Latest: 1.0.0
azure-ai-ml>=1.30.0                 # Azure ML - Latest: 1.30.0
azure-keyvault-secrets>=4.10.0      # Key Vault - Latest: 4.10.0
azure-monitor-opentelemetry>=1.8.0  # Monitoring - Latest: 1.8.2

# MLflow for Experiment Tracking
mlflow>=2.9.0
azureml-mlflow>=1.60.0              # Latest: 1.60.0.post1

# Visualization
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.17.0

# Notebook
jupyter>=1.0.0
ipykernel>=6.25.0
nbconvert>=7.8.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.66.0
tenacity>=8.2.0                     # Retry logic

# Testing
pytest>=8.0.0                       # Latest: 8.x
pytest-cov>=4.0.0                   # Latest: 4.x
pytest-mock>=3.11.0

# Code Quality
ruff>=0.1.0                         # Fast linter/formatter (replaces flake8, black)
mypy>=1.5.0                         # Type checking
bandit>=1.7.5                       # Security scanning

# Optional: Development Tools
ipython>=8.12.0
pip-audit>=2.6.0                    # Dependency vulnerability scanning
```

---

## Development Tools

### IDE/Editor

**Recommended**: Visual Studio Code with extensions:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter",
    "charliermarsh.ruff",
    "ms-azuretools.vscode-azureresourcegroups",
    "ms-azuretools.vscode-azurefunctions",
    "github.copilot"
  ]
}
```

**Alternative**: PyCharm Professional (has Azure integration)

### Code Quality Tools

```bash
# Modern Python Linting & Formatting (Ruff - fastest, all-in-one)
ruff check src/ tests/            # Lint
ruff format src/ tests/           # Format (replaces Black)

# Type Checking
mypy src/ --ignore-missing-imports

# Security Scanner
bandit -r src/

# Dependency Vulnerabilities
pip-audit

# Test Coverage
pytest tests/ --cov=src --cov-report=html
```

**Why Ruff?** As of November 2025, Ruff has become the standard for Python linting/formatting:
- 10-100x faster than Black/Flake8
- Replaces Black, Flake8, isort, pyupgrade in one tool
- Compatible with Black's formatting
- Used by major projects (FastAPI, Pydantic, etc.)

---

## Architecture Decisions (ADRs)

### ADR-001: Agent-Based Architecture
**Status**: ✅ Accepted  
**Date**: November 2025  
**Context**: Need modular, testable system with clear separation of concerns  
**Decision**: Implement specialized agents (Segmentation, Retrieval, Generation, Safety, Experimentation)  
**Consequences**: 
- ✅ Easy to test and maintain each agent independently
- ✅ Can parallelize agent execution in future (async/await)
- ⚠️ Requires orchestration layer to coordinate agents
- ⚠️ Inter-agent communication overhead (mitigated by local execution in POC)

### ADR-002: Azure-Native Services
**Status**: ✅ Accepted  
**Date**: November 2025  
**Context**: Need enterprise-grade AI services with compliance and governance  
**Decision**: Use Azure AI Foundry, Azure AI Search, Azure OpenAI, Azure AI Content Safety  
**Consequences**:
- ✅ Enterprise security and compliance built-in
- ✅ Managed services reduce operational burden
- ✅ Unified billing and cost tracking
- ⚠️ Vendor lock-in to Azure ecosystem
- ⚠️ API costs can be significant at scale (mitigated by caching, batching)

### ADR-003: Configuration-Driven Design
**Status**: ✅ Accepted  
**Date**: November 2025  
**Context**: Need rapid iteration on prompts, thresholds, and parameters  
**Decision**: Externalize all prompts (`.txt`), thresholds, and configs to YAML files  
**Consequences**:
- ✅ Non-engineers (marketers, compliance) can update prompts
- ✅ Easy A/B testing of prompt variations
- ✅ No code changes needed for tuning
- ⚠️ Requires validation logic for config files
- ⚠️ Version control complexity for multiple config versions

### ADR-004: Synchronous Pipeline (POC Only)
**Status**: ✅ Accepted (POC), ⏭️ To be reconsidered for Phase 2  
**Date**: November 2025  
**Context**: Need simple, debuggable execution for 1-week POC  
**Decision**: Sequential synchronous execution; no async or distributed processing  
**Consequences**:
- ✅ Simple to debug and reason about execution flow
- ✅ Faster to implement (no async complexity)
- ⚠️ Won't scale to production workloads (Phase 2 will need async/parallel)
- ⚠️ Longer execution time for large datasets (acceptable for POC: 100-500 customers)

### ADR-005: Local File Storage (POC Only)
**Status**: ✅ Accepted (POC), ⏭️ To be reconsidered for Phase 2  
**Date**: November 2025  
**Context**: POC doesn't need production database; focus on algorithm validation  
**Decision**: Use local CSV/JSON files for data persistence  
**Consequences**:
- ✅ No database setup overhead (faster POC delivery)
- ✅ Easy to inspect and debug data files
- ✅ Portable (no external dependencies)
- ⚠️ Not suitable for production (no ACID, no concurrent access)
- ⚠️ Manual file management required

### ADR-006: Unified OpenAI Package (November 2025)
**Status**: ✅ Accepted  
**Date**: November 2025  
**Context**: OpenAI Python package now supports Azure natively  
**Decision**: Use `openai>=1.55.0` package (unified) instead of deprecated `azure-openai`  
**Consequences**:
- ✅ Single package for both OpenAI and Azure OpenAI
- ✅ Better maintained, more features
- ✅ Consistent API across providers
- ⚠️ Migration needed for older code using legacy packages

---

## Code Style Standards

### PEP 8 with Modern Adjustments

```python
# Line length: 100 characters (Ruff default, more readable on modern screens)
MAX_LINE_LENGTH = 100

# Type hints: Required for all public functions and methods
def generate_variant(
    segment: Dict[str, Any],
    content: List[Dict[str, str]],
    tone: str
) -> Dict[str, Any]:
    """
    Generate a personalized message variant.
    
    Args:
        segment: Customer segment information with features
        content: List of retrieved content snippets
        tone: Variant tone (urgent, informational, friendly)
        
    Returns:
        Dictionary containing variant with subject, body, citations
        
    Raises:
        ValueError: If tone is invalid
        APIError: If OpenAI API call fails
    """
    pass

# Naming conventions
class ContentRetriever:          # PascalCase for classes
    def __init__(self):
        self.cache = {}           # snake_case for attributes
        self._connection = None   # _prefix for private
        
    def retrieve_content(self):   # snake_case for methods
        pass

# Constants
MAX_TOKENS = 1000                 # UPPER_SNAKE_CASE
API_VERSION = "2025-11-01-preview"

# Function names
def segment_customers():          # snake_case
    pass

def _normalize_features():       # _prefix for private functions
    pass
```

### Docstring Standard: Google Style

```python
def calculate_lift(treatment_rate: float, control_rate: float) -> float:
    """
    Calculate relative lift between treatment and control.
    
    Uses the formula: lift = (treatment - control) / control * 100%
    
    Args:
        treatment_rate: Metric value for treatment arm (e.g., 0.30 = 30%)
        control_rate: Metric value for control arm (e.g., 0.25 = 25%)
        
    Returns:
        Relative lift percentage (e.g., 20.0 for 20% lift)
        
    Raises:
        ValueError: If control_rate is zero (division by zero)
        TypeError: If inputs are not numeric
        
    Example:
        >>> calculate_lift(0.30, 0.25)
        20.0
    """
    if control_rate == 0:
        raise ValueError("Control rate cannot be zero")
    return (treatment_rate - control_rate) / control_rate * 100
```

---

## Error Handling Standards

### Custom Exceptions

```python
"""
Custom exceptions for the Customer Personalization Orchestrator.
"""

class CPOError(Exception):
    """Base exception for all CPO errors."""
    pass

class ConfigurationError(CPOError):
    """Raised when configuration is invalid or missing."""
    pass

class AzureAPIError(CPOError):
    """Raised when Azure API call fails."""
    def __init__(self, service: str, operation: str, message: str):
        self.service = service
        self.operation = operation
        self.message = message
        super().__init__(f"{service}.{operation}: {message}")

class SafetyViolationError(CPOError):
    """Raised when content fails safety screening."""
    def __init__(self, variant_id: str, reason: str):
        self.variant_id = variant_id
        self.reason = reason
        super().__init__(f"Variant {variant_id} blocked: {reason}")
```

### Retry Logic Standard

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# Standard retry decorator for Azure API calls
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_if_exception_type=(ConnectionError, TimeoutError),
    reraise=True
)
def call_azure_api(func, *args, **kwargs):
    """
    Call Azure API with exponential backoff retry.
    
    Retry Strategy:
    - Attempt 1: Immediate
    - Attempt 2: Wait 2 seconds
    - Attempt 3: Wait 4 seconds
    - Attempt 4: Wait 8 seconds (then fail)
    
    Only retries on transient errors (connection, timeout).
    """
    return func(*args, **kwargs)
```

### Graceful Degradation Pattern

```python
def process_batch(customers: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Process customers with error isolation.
    
    Strategy:
    - If one customer fails, log error and continue
    - Collect all errors for final summary
    - Don't let single failure block entire pipeline
    
    Returns:
        Tuple of (successful_results, error_records)
    """
    results = []
    errors = []
    
    for customer in customers:
        try:
            result = process_single_customer(customer)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {customer['id']}: {e}")
            errors.append({
                "customer_id": customer["id"],
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            continue  # Don't stop the batch
    
    if errors:
        logger.warning(f"Batch completed with {len(errors)} errors")
    
    return results, errors
```

---

## Logging Standards

### Structured JSON Logging

```python
import logging
import json
from datetime import datetime

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Just the message (JSON)
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_event(event_type: str, data: dict):
    """
    Log structured event in JSON format.
    
    Args:
        event_type: Event type (e.g., "variant_generated", "safety_check")
        data: Event data (must be JSON-serializable)
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "data": data
    }
    logger.info(json.dumps(log_entry))

# Usage
log_event("variant_generated", {
    "variant_id": "VAR001",
    "segment": "High-Value",
    "tokens_used": 250,
    "cost_usd": 0.0075,
    "latency_ms": 1250
})
```

### Logging Levels

- **DEBUG**: Detailed diagnostic info (disabled in production)
- **INFO**: General informational messages (pipeline progress)
- **WARNING**: Unexpected but handled conditions (high block rate)
- **ERROR**: Errors that don't stop execution (single customer failure)
- **CRITICAL**: Errors that stop execution (config missing)

### What to Log / Not Log

✅ **DO LOG**:
- Anonymized customer IDs (hashed)
- Timestamps of operations
- Operation types and durations
- Success/failure status
- API latency and token usage
- Error messages (sanitized)

❌ **DO NOT LOG**:
- API keys or secrets
- PII (emails, names, addresses)
- Full message content (privacy)
- Unanonymized customer identifiers
- Azure credentials

---

## Testing Standards

### Test Organization

```python
# tests/test_generation.py
import pytest
from unittest.mock import Mock, patch
from src.agents.generation_agent import generate_variants

# Fixtures for common test data
@pytest.fixture
def sample_segment():
    return {
        "segment_id": "SEG001",
        "name": "High-Value Recent",
        "features": {
            "avg_order_value": 250.0,
            "purchase_frequency": 12
        }
    }

@pytest.fixture
def sample_content():
    return [
        {
            "document_id": "DOC001",
            "title": "Premium Features",
            "snippet": "Our premium features include..."
        }
    ]

# Test naming: test_<function>_<scenario>_<expected>
def test_generate_variants_with_valid_input_returns_three_variants(
    sample_segment, 
    sample_content
):
    """Test that generate_variants returns 3 variants for valid input."""
    with patch('src.integrations.azure_openai.get_openai_client'):
        variants = generate_variants(sample_segment, sample_content)
        assert len(variants) == 3
        assert all('subject' in v for v in variants)
        assert all('body' in v for v in variants)

def test_generate_variants_with_empty_content_raises_error(sample_segment):
    """Test that generate_variants raises error with empty content."""
    with pytest.raises(ValueError, match="Content cannot be empty"):
        generate_variants(sample_segment, [])
```

### Mock Azure Services

```python
from unittest.mock import Mock

class MockOpenAIClient:
    """Mock Azure OpenAI client for testing."""
    
    def chat_completions_create(self, **kwargs):
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test generated message"))]
        mock_response.usage = Mock(total_tokens=100)
        return mock_response

class MockSearchClient:
    """Mock Azure AI Search client for testing."""
    
    def search(self, query, **kwargs):
        return [
            {
                "document_id": "DOC001",
                "title": "Mock Document",
                "content": "Mock content for testing",
                "@search.score": 0.95
            }
        ]
```

### Coverage Requirements

- **Unit Tests**: >70% code coverage
- **Integration Tests**: Critical paths (end-to-end pipeline)
- **Test Types**:
  - Unit: Individual functions and methods
  - Integration: Azure service interactions
  - End-to-End: Full pipeline execution

---

## Performance Optimization

### API Call Optimization

```python
# Batch processing with rate limiting
import time

def process_in_batches(items: List, batch_size: int = 10):
    """Process items in batches to manage API rate limits."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        yield batch
        
        # Rate limiting pause (1 second between batches)
        if i + batch_size < len(items):
            time.sleep(1)

# Usage
for batch in process_in_batches(variants, batch_size=10):
    results = safety_client.check_batch(batch)
```

### Caching Strategy

```python
from functools import lru_cache
import hashlib
import json

class CachedRetriever:
    """Content retriever with LRU cache."""
    
    def __init__(self, search_client):
        self.client = search_client
        self._cache = {}
    
    def retrieve_for_segment(self, segment: Dict) -> List[Dict]:
        """Retrieve with caching."""
        cache_key = self._make_key(segment)
        
        if cache_key in self._cache:
            logger.debug(f"Cache hit for segment: {segment['name']}")
            return self._cache[cache_key]
        
        # Cache miss - fetch from search
        results = self.client.search(...)
        self._cache[cache_key] = results
        return results
    
    def _make_key(self, segment: Dict) -> str:
        """Generate cache key from segment features."""
        key_data = json.dumps(segment['features'], sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
```

### Token Usage Tracking

```python
class TokenTracker:
    """Track API token usage and costs."""
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0
    
    def record_call(self, tokens: int, model: str = "gpt-4o-mini"):
        """Record a single API call."""
        self.total_tokens += tokens
        self.call_count += 1
        
        # GPT-4o-mini pricing (November 2025 estimates)
        cost_per_token = 0.00015  # ~$0.15 per 1K tokens
        self.total_cost += tokens * cost_per_token
    
    def summary(self) -> dict:
        """Get usage summary."""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 2),
            "avg_tokens_per_call": self.total_tokens / max(1, self.call_count)
        }
```

---

## Security Best Practices

### API Key Management

```python
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# NEVER hardcode credentials
# ❌ BAD
api_key = "abc123..."

# ✅ GOOD: Use environment variables
api_key = os.getenv("AZURE_OPENAI_API_KEY")

# ✅ BEST: Use Managed Identity (production)
credential = DefaultAzureCredential()

# ✅ ALSO GOOD: Use Key Vault (if Managed Identity not available)
vault_client = SecretClient(
    vault_url=os.getenv("AZURE_KEY_VAULT_URL"),
    credential=DefaultAzureCredential()
)
api_key = vault_client.get_secret("openai-api-key").value
```

### PII Anonymization

```python
import hashlib

def anonymize_customer_id(customer_id: str, salt: str = "project-salt") -> str:
    """
    Anonymize customer ID using SHA-256 hash.
    
    Args:
        customer_id: Original customer identifier
        salt: Project-specific salt
        
    Returns:
        Anonymized ID (first 8 characters of hash)
    """
    combined = f"{salt}:{customer_id}"
    hash_obj = hashlib.sha256(combined.encode())
    return hash_obj.hexdigest()[:8]

# Usage in logs
logger.info(f"Processing customer {anonymize_customer_id(customer_id)}")
# Output: "Processing customer a3f5d8e9"
```

---

## Deployment Strategy

### Local Development

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run pipeline
python scripts/run_experiment.py
```

### Docker (Future Phase 2)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run pipeline
CMD ["python", "scripts/run_experiment.py"]
```

---

## Technical Debt & Future Work

### Known Limitations (POC)
1. ❌ No async/concurrent processing (sequential execution)
2. ❌ No production database (local files)
3. ❌ No distributed tracing (basic logging only)
4. ❌ Limited error recovery (basic retry only)
5. ❌ No cost optimization (no caching at scale)

### Phase 2 Improvements
1. ✅ Async agent execution with `asyncio`
2. ✅ Azure Cosmos DB for persistence
3. ✅ Azure Monitor integration with OpenTelemetry
4. ✅ Comprehensive error handling and circuit breakers
5. ✅ API response caching with Redis
6. ✅ Batch processing optimization

### Phase 3 Scale
1. ✅ Azure Container Apps or AKS deployment
2. ✅ Auto-scaling based on load
3. ✅ Multi-region deployment
4. ✅ Advanced monitoring dashboards (Azure AI Foundry Observability)
5. ✅ Cost optimization strategies

---

## Contact & Support

**Technical Lead**: [Your Name]  
**Azure Support**: https://portal.azure.com → Support  
**Documentation**: `.kiro/specs/` and `.kiro/steering/`  
**Internal Slack**: #personalization-dev

---

**Last Updated**: November 21, 2025  
**Next Review**: End of POC Week  
**Document Owner**: Technical Lead