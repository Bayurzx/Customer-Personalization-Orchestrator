# API Integration Standards

## Overview

This document defines standards and patterns for integrating with Azure AI services and handling API interactions throughout the Customer Personalization Orchestrator.

---

## General API Principles

### 1. Retry Logic

All external API calls must implement retry logic for transient failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_if=retry_if_exception_type((ConnectionError, TimeoutError))
)
def call_external_api(client, request):
    """Call external API with exponential backoff retry."""
    return client.make_request(request)
```

**Retry Strategy**:
- **Max attempts**: 3
- **Backoff**: Exponential (2s, 4s, 8s)
- **Retriable errors**: Connection, timeout, rate limit (429), server errors (5xx)
- **Non-retriable errors**: Authentication (401), forbidden (403), bad request (400)

### 2. Timeout Handling

All API calls must specify timeouts:

```python
from azure.ai.openai import Azure OpenAI

client = AzureOpenAI(
    azure_endpoint=endpoint,
    timeout=30.0  # 30 seconds
)
```

**Timeout Guidelines**:
- **Generation**: 30 seconds (LLM completion)
- **Search**: 5 seconds (content retrieval)
- **Safety check**: 10 seconds (content analysis)

### 3. Error Handling

```python
from azure.core.exceptions import AzureError, HttpResponseError

try:
    result = client.some_operation()
except HttpResponseError as e:
    if e.status_code == 429:
        logger.warning(f"Rate limit hit: {e}")
        time.sleep(60)  # Wait before retry
        raise
    elif e.status_code == 401:
        logger.error("Authentication failed - check credentials")
        raise
    else:
        logger.error(f"API error {e.status_code}: {e.message}")
        raise
except AzureError as e:
    logger.error(f"Azure service error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 4. Request/Response Logging

Log all API interactions for debugging and audit:

```python
import time
import json

def log_api_call(service: str, operation: str, request_data: dict, response_data: dict, duration_ms: int):
    """Log API call details."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": service,
        "operation": operation,
        "duration_ms": duration_ms,
        "request_size_bytes": len(json.dumps(request_data)),
        "response_size_bytes": len(json.dumps(response_data)),
        "status": "success" if response_data else "error"
    }
    logger.info(json.dumps(log_entry))

# Usage
start = time.time()
response = client.call_api(request)
duration = int((time.time() - start) * 1000)
log_api_call("azure_openai", "generate_completion", request, response, duration)
```

---

## Azure OpenAI API Standards

### Request Format

```python
messages = [
    {
        "role": "system",
        "content": "You are a marketing copywriter."
    },
    {
        "role": "user",
        "content": prompt_text
    }
]

response = client.chat.completions.create(
    model=deployment_name,
    messages=messages,
    max_tokens=1000,
    temperature=0.7,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop=None
)
```

### Response Parsing

```python
def parse_openai_response(response) -> dict:
    """Parse Azure OpenAI response."""
    return {
        "text": response.choices[0].message.content,
        "finish_reason": response.choices[0].finish_reason,
        "tokens": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        },
        "model": response.model,
        "created_at": response.created
    }
```

### Token Tracking

```python
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.total_input += prompt_tokens
        self.total_output += completion_tokens
    
    def calculate_cost(self, model: str = "gpt-4") -> float:
        """Calculate cost based on token usage."""
        PRICING = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        
        price = PRICING.get(model, PRICING["gpt-4"])
        cost_input = (self.total_input / 1000) * price["input"]
        cost_output = (self.total_output / 1000) * price["output"]
        return cost_input + cost_output
    
    def get_summary(self) -> dict:
        return {
            "total_tokens": self.total_input + self.total_output,
            "input_tokens": self.total_input,
            "output_tokens": self.total_output,
            "estimated_cost_usd": self.calculate_cost()
        }
```

### Rate Limiting

```python
class OpenAIRateLimiter:
    """Rate limiter for Azure OpenAI API."""
    
    def __init__(self, rpm: int = 60, tpm: int = 90000):
        self.rpm = rpm  # Requests per minute
        self.tpm = tpm  # Tokens per minute
        self.request_times = deque()
        self.token_times = deque(maxlen=tpm)
    
    def wait_if_needed(self, estimated_tokens: int = 1000):
        """Wait if approaching rate limits."""
        now = time.time()
        
        # Clean old requests (outside 1-minute window)
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # Check if at request limit
        if len(self.request_times) >= self.rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        # Check if at token limit
        if len(self.token_times) + estimated_tokens > self.tpm:
            logger.warning("Token rate limit: sleeping 60s")
            time.sleep(60)
            self.token_times.clear()
        
        # Record this request
        self.request_times.append(now)
        for _ in range(estimated_tokens):
            self.token_times.append(now)
```

---

## Azure Cognitive Search API Standards

### Index Operations

```python
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex

def create_or_update_index(index_client: SearchIndexClient, index: SearchIndex):
    """Create or update search index."""
    try:
        # Try to get existing index
        existing_index = index_client.get_index(index.name)
        logger.info(f"Index '{index.name}' already exists, updating...")
        index_client.create_or_update_index(index)
    except Exception:
        logger.info(f"Creating new index '{index.name}'...")
        index_client.create_index(index)
```

### Document Indexing

```python
def index_documents_batch(search_client, documents: List[dict], batch_size: int = 100):
    """Index documents in batches."""
    total_indexed = 0
    total_failed = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        try:
            result = search_client.upload_documents(documents=batch)
            
            succeeded = len([r for r in result if r.succeeded])
            failed = len([r for r in result if not r.succeeded])
            
            total_indexed += succeeded
            total_failed += failed
            
            logger.info(f"Batch {i//batch_size + 1}: {succeeded} indexed, {failed} failed")
            
        except Exception as e:
            logger.error(f"Batch indexing error: {e}")
            total_failed += len(batch)
    
    return {"indexed": total_indexed, "failed": total_failed}
```

### Search Operations

```python
def search_with_filters(
    search_client,
    query: str,
    filter_expr: str = None,
    top: int = 5,
    select: List[str] = None
) -> List[dict]:
    """Search with filtering and field selection."""
    try:
        results = search_client.search(
            search_text=query,
            filter=filter_expr,
            top=top,
            select=select,
            query_type="semantic",
            semantic_configuration_name="default",
            include_total_count=True
        )
        
        documents = []
        for result in results:
            doc = dict(result)
            doc["@search.score"] = result.get("@search.score")
            doc["@search.reranker_score"] = result.get("@search.reranker_score")
            documents.append(doc)
        
        logger.info(f"Search '{query}': {len(documents)} results")
        return documents
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise
```

### Query Construction

```python
def construct_search_query(segment: dict) -> str:
    """Construct search query from segment features."""
    query_parts = []
    
    # Add segment characteristics
    if segment.get("tier") == "Gold":
        query_parts.append("premium exclusive")
    
    if segment.get("name") == "At-Risk":
        query_parts.append("retention engagement")
    
    # Add behavioral signals
    if segment.get("purchase_frequency", 0) > 10:
        query_parts.append("frequent buyer")
    
    query = " ".join(query_parts)
    logger.debug(f"Constructed query for {segment['name']}: {query}")
    return query
```

---

## Azure Content Safety API Standards

### Text Analysis

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions

def analyze_text_safety(
    safety_client: ContentSafetyClient,
    text: str,
    categories: List[str] = None
) -> dict:
    """Analyze text for safety violations."""
    if categories is None:
        categories = ["Hate", "Violence", "SelfHarm", "Sexual"]
    
    try:
        request = AnalyzeTextOptions(text=text)
        response = safety_client.analyze_text(request)
        
        result = {
            "hate": response.hate_result.severity if response.hate_result else 0,
            "violence": response.violence_result.severity if response.violence_result else 0,
            "self_harm": response.self_harm_result.severity if response.self_harm_result else 0,
            "sexual": response.sexual_result.severity if response.sexual_result else 0
        }
        
        logger.debug(f"Safety check: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Content safety error: {e}")
        raise
```

### Batch Analysis

```python
def batch_safety_check(
    safety_client: ContentSafetyClient,
    texts: List[str],
    max_concurrent: int = 5
) -> List[dict]:
    """Analyze multiple texts with concurrency control."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_text = {
            executor.submit(analyze_text_safety, safety_client, text): text
            for text in texts
        }
        
        for future in as_completed(future_to_text):
            text = future_to_text[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Safety check failed for text: {e}")
                results.append(None)
    
    return results
```

### Policy Application

```python
def apply_safety_policy(severity_scores: dict, threshold: int = 4) -> dict:
    """Apply safety policy to severity scores."""
    blocked_categories = []
    
    for category, severity in severity_scores.items():
        if severity > threshold:
            blocked_categories.append(category)
    
    status = "block" if blocked_categories else "pass"
    
    return {
        "status": status,
        "blocked_categories": blocked_categories,
        "severity_scores": severity_scores,
        "threshold": threshold,
        "block_reason": f"Categories {blocked_categories} exceeded threshold {threshold}" if blocked_categories else None
    }
```

---

## Authentication Patterns

### Managed Identity (Recommended)

```python
from azure.identity import DefaultAzureCredential

# Automatically tries: Managed Identity -> Azure CLI -> Environment Variables
credential = DefaultAzureCredential()

# Use with any Azure SDK
client = AzureOpenAI(
    azure_endpoint=endpoint,
    credential=credential
)
```

### API Key (Fallback)

```python
import os
from azure.core.credentials import AzureKeyCredential

api_key = os.getenv("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError("AZURE_OPENAI_API_KEY not set")

credential = AzureKeyCredential(api_key)

client = AzureOpenAI(
    azure_endpoint=endpoint,
    credential=credential
)
```

### Environment Variable Management

```python
from dotenv import load_dotenv
import os

# Load from .env file
load_dotenv()

# Validate required variables
required_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_CONTENT_SAFETY_ENDPOINT"
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
```

---

## API Response Caching

### Simple In-Memory Cache

```python
from functools import lru_cache
import hashlib
import json

def hash_request(request_data: dict) -> str:
    """Create hash of request for cache key."""
    return hashlib.md5(json.dumps(request_data, sort_keys=True).encode()).hexdigest()

@lru_cache(maxsize=128)
def cached_search(query_hash: str, client, query: str, top: int):
    """Cache search results."""
    return client.search(query, top=top)

# Usage
query_hash = hash_request({"query": query, "top": top})
results = cached_search(query_hash, search_client, query, top)
```

### File-Based Cache (for development)

```python
import json
import os
from pathlib import Path

class FileCache:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str):
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, key: str, value: dict):
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(value, f, indent=2)
    
    def clear(self):
        for file in self.cache_dir.glob("*.json"):
            file.unlink()

# Usage
cache = FileCache()
cache_key = hash_request(request_data)

result = cache.get(cache_key)
if result is None:
    result = expensive_api_call()
    cache.set(cache_key, result)
```

---

## API Health Checks

### Service Health Monitoring

```python
def check_service_health(services: dict) -> dict:
    """Check health of all Azure services."""
    health_status = {}
    
    for service_name, client in services.items():
        try:
            # Perform lightweight operation
            if service_name == "openai":
                client.models.list()
            elif service_name == "search":
                client.get_index_statistics()
            elif service_name == "content_safety":
                # Content Safety doesn't have a health endpoint,
                # so we do a minimal analysis
                pass
            
            health_status[service_name] = "healthy"
            logger.info(f"✓ {service_name} is healthy")
            
        except Exception as e:
            health_status[service_name] = f"unhealthy: {str(e)}"
            logger.error(f"✗ {service_name} is unhealthy: {e}")
    
    return health_status
```

---

## Best Practices Summary

1. **Always implement retry logic** for transient failures
2. **Set appropriate timeouts** for all API calls
3. **Log all API interactions** for debugging and audit
4. **Track token usage and costs** for OpenAI calls
5. **Use Managed Identity** for authentication in production
6. **Implement rate limiting** to avoid hitting quotas
7. **Cache results** where appropriate to reduce costs
8. **Handle errors gracefully** with specific error types
9. **Validate responses** before processing
10. **Monitor service health** proactively