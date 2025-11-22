# Azure Services Integration Guide

## Overview
This document defines the standard integration patterns, configuration keys, and SDK usage for the Azure services used in the Customer Personalization Orchestrator.

**Project Context**: November 2025
**Authentication Standard**: `DefaultAzureCredential` (Azure Identity)
**Primary Region**: East US 2 (Recommended for AI capacity)

---

## 1. Azure OpenAI Service / AI Foundry
**Role**: Generative Engine (Agents & Variants)

The core engine for the Generation Agent. We use the **Generative AI** capabilities to produce message variants and the **Embeddings** capabilities (optional) if vector search is enabled.

### Configuration
- **Resource Type**: `Microsoft.CognitiveServices/accounts`
- **Python Package**: `openai>=1.55.0` (Using Azure Provider)
- **API Version**: `2025-11-01-preview`
- **Recommended Models**: `gpt-5-mini` (cost-optimized at $0.25/1M input tokens, $2.00/1M output tokens)

### Environment Variables
```bash
AZURE_OPENAI_ENDPOINT="https://<resource-name>.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-5-mini"
AZURE_OPENAI_API_VERSION="2025-11-01-preview"
```

### Implementation Pattern
```python
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

def get_openai_client():
    # Secure AD Auth (Preferred over API Keys)
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), 
        "https://cognitiveservices.azure.com/.default"
    )
    
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-11-01-preview")
    )
```

---

## 2. Azure AI Search (formerly Cognitive Search)
**Role**: Retrieval & Grounding (RAG)

Used by the Retrieval Agent to index approved content and perform semantic searches to ground the LLM generation.

### Configuration
- **Resource Type**: `Microsoft.Search/searchServices`
- **Python Package**: `azure-search-documents>=11.6.0`
- **Endpoint Format**: `https://<service-name>.search.windows.net`
- **Features Used**: Semantic Search, Vector Search (Optional)

### Environment Variables
```bash
AZURE_SEARCH_ENDPOINT="https://<service-name>.search.windows.net"
AZURE_SEARCH_INDEX_NAME="approved-content-index"
```

### Implementation Pattern
```python
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

def get_search_client():
    return SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        credential=DefaultAzureCredential()
    )
```

---

## 3. Azure AI Content Safety
**Role**: Guardrails & Policy Enforcement

Used by the Safety Agent to screen prompts and generated variants for Hate, Violence, Self-Harm, and Sexual content.

### Configuration
- **Resource Type**: `Microsoft.CognitiveServices/accounts`
- **Python Package**: `azure-ai-contentsafety>=1.0.0`
- **API Version**: `2024-09-01`
- **Block Strategy**: Severity Threshold > Medium (4)

### Environment Variables
```bash
AZURE_CONTENT_SAFETY_ENDPOINT="https://<resource-name>.cognitiveservices.azure.com/"
```

### Implementation Pattern
```python
import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.identity import DefaultAzureCredential

def get_safety_client():
    return ContentSafetyClient(
        endpoint=os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT"),
        credential=DefaultAzureCredential()
    )
```

---

## 4. Azure Machine Learning (AML)
**Role**: Experiment Tracking & Model Registry

Used by the Experimentation Agent to log runs, metrics (lift, engagement), and parameters. Integration is via **MLflow**.

### Configuration
- **Resource Type**: `Microsoft.MachineLearningServices/workspaces`
- **Python Packages**: `azure-ai-ml`, `mlflow`, `azureml-mlflow`
- **Usage**: Log metrics, artifacts (reports), and parameters.

### Environment Variables
```bash
AZURE_ML_SUBSCRIPTION_ID="<guid>"
AZURE_ML_RESOURCE_GROUP="<rg-name>"
AZURE_ML_WORKSPACE_NAME="<ws-name>"
```

### Implementation Pattern
```python
import os
import mlflow
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

def setup_mlflow_tracking():
    # Connect to AML Workspace
    ml_client = MLClient(
        DefaultAzureCredential(),
        os.getenv("AZURE_ML_SUBSCRIPTION_ID"),
        os.getenv("AZURE_ML_RESOURCE_GROUP"),
        os.getenv("AZURE_ML_WORKSPACE_NAME"),
    )
    
    # Set MLflow Tracking URI to Azure ML
    mlflow.set_tracking_uri(ml_client.workspaces.get(ml_client.workspace_name).mlflow_tracking_uri)
    mlflow.set_experiment("customer-personalization-poc")
```

---

## 5. Azure Monitor & Application Insights
**Role**: Telemetry & System Logs

Used for structured logging of the application's performance and behavior (API latency, errors, operation counts).

### Configuration
- **Resource Type**: `Microsoft.Insights/components`
- **Python Package**: `azure-monitor-opentelemetry` (Modern standard)
- **Connection String**: Stored in Key Vault or Env Var.

### Implementation Pattern
```python
import os
from azure.monitor.opentelemetry import configure_azure_monitor

def configure_telemetry():
    configure_azure_monitor(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )
```

---

## 6. Azure Key Vault
**Role**: Secrets Management

Used to securely retrieve connection strings or API keys if Managed Identity is not feasible for a specific component (e.g., legacy third-party integration, though not expected for this Azure-native stack).

### Configuration
- **Resource Type**: `Microsoft.KeyVault/vaults`
- **Python Package**: `azure-keyvault-secrets`

### Environment Variables
```bash
AZURE_KEY_VAULT_URL="https://<vault-name>.vault.azure.net/"
```

### Implementation Pattern
```python
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(secret_name: str) -> str:
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    if not vault_url:
        raise ValueError("AZURE_KEY_VAULT_URL not set")
        
    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    return client.get_secret(secret_name).value
```

---

## Service Limits & Quotas (POC Level)

| Service | Tier | Limit | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Azure OpenAI** | S0 (Standard) | TPM (Tokens Per Minute) varies | Implement **exponential backoff** (see `api-standards.md`). Batch processing with pauses. |
| **AI Search** | Standard | Storage/Index count | N/A for POC dataset size (50 docs). |
| **Content Safety** | S0 | 10 QPS (Queries Per Second) | Limit concurrency to 5 threads in `safety_agent.py`. |

## Future Scale Services (Reference Only)

*These services are part of the long-term architecture but **NOT** implemented in the Week 1 POC.*

1.  **Azure Cosmos DB**: Future storage for customer profiles and high-volume logs.
2.  **Azure Stream Analytics**: Future real-time event processing.
3.  **Azure AI Foundry Observability**: Future advanced LLM drift detection (beyond basic MLflow).

---

## Provisioning Quick Reference (Azure CLI)

```bash
# Login
az login

# Create Resource Group
az group create --name rg-personalization-poc --location eastus2

# Create AI Search
az search service create --name search-cpo-poc --resource-group rg-personalization-poc --sku Standard

# Create OpenAI (Note: Requires application approval in some subs)
az cognitiveservices account create --name openai-cpo-poc --resource-group rg-personalization-poc --kind OpenAI --sku S0 --location eastus2

# Create Content Safety
az cognitiveservices account create --name safety-cpo-poc --resource-group rg-personalization-poc --kind ContentSafety --sku S0 --location eastus2

# Create Key Vault
az keyvault create --name kv-cpo-poc --resource-group rg-personalization-poc --location eastus2
