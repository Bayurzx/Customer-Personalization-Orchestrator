# Azure Environment Variables Setup Guide

## Prerequisites

Before you begin, ensure you have:
- [ ] An active Azure subscription
- [ ] Azure CLI installed ([Download here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- [ ] Contributor or Owner role on the subscription
- [ ] Access to create Azure resources

---

## Step 0: Initial Azure CLI Setup

### Login to Azure

```bash
# Login to Azure
az login

# If you have multiple subscriptions, list them
az account list --output table

# Set the subscription you want to use
az account set --subscription "Your Subscription ID"

# Verify current subscription
az account show --output table
```

### Get Your Subscription ID

```bash
# Get your subscription ID
az account show --query id --output tsv
```

**Copy this value** → This is your `AZURE_SUBSCRIPTION_ID`

**Example output**: `12345678-1234-1234-1234-123456789abc`

---

## Step 1: Create Resource Group

All resources will be organized in a single resource group.

```bash
# Create resource group
az group create \
  --name rg-poc \
  --location eastus2

# Verify creation
az group show --name rg-poc --output table
```

**Set in .env**:
```bash
AZURE_RESOURCE_GROUP=rg-poc
AZURE_REGION=eastus2
```

---

## Step 2: Azure OpenAI Service

### Create Azure OpenAI Resource

```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --location eastus2 \
  --kind OpenAI \
  --sku S0 \
  --custom-domain openai-cpo-poc-1337

# Wait for deployment to complete (may take 2-3 minutes)
```

**Note**: Replace `<your-unique-id>` with something unique (e.g., your initials + random numbers)

### Get Azure OpenAI Endpoint

```bash
# Get endpoint
az cognitiveservices account show \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --query properties.endpoint \
  --output tsv
```

**Example output**: `https://openai-cpo-poc-abc123.openai.azure.com/`

**Set in .env**:
```bash
AZURE_OPENAI_ENDPOINT=https://openai-cpo-poc-1337.openai.azure.com/
```

### Get Azure OpenAI API Key

```bash
# Get API key (Key 1)
az cognitiveservices account keys list \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --query key1 \
  --output tsv
```

**Copy this value** → This is your `AZURE_OPENAI_API_KEY`

**Set in .env**:
```bash
AZURE_OPENAI_API_KEY=<your-key-here>
```

### Deploy a Model (gpt-5-mini - Cost Optimized)

**Option A: Using Azure Portal (Recommended for first time)**

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Click **"Model deployments"** → **"Manage Deployments"**
4. You'll be redirected to **Azure OpenAI Studio**
5. Click **"Deployments"** → **"Create new deployment"**
6. Select model: **gpt-5-mini** (recommended - most cost-effective at $0.25/1M input tokens)
7. Deployment name: `gpt-5-mini` (use this exact name for consistency)
8. Click **"Create"**

**Option B: Using Azure CLI**

```bash
# Deploy gpt-5-mini model (cost-optimized)
az cognitiveservices account deployment create \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --deployment-name gpt-5-mini \
  --model-name gpt-5-mini \
  --model-version "2025-08-07" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name GlobalStandard
```

**Set in .env**:
```bash
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

**Verify deployment**:
```bash
az cognitiveservices account deployment list \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --output table
```

---

## Step 3: Azure AI Search

### Create Azure AI Search Service

```bash
# Create Azure AI Search service
az search service create \
  --name search-cpo-poc-1337 \
  --resource-group rg-poc \
  --location eastus2 \
  --sku Standard \
  --partition-count 1 \
  --replica-count 1

# Wait for deployment (may take 3-5 minutes)
```

### Get Azure AI Search Endpoint

```bash
# Get endpoint
az search service show \
  --name search-cpo-poc-1337 \
  --resource-group rg-poc \
  --query "hostName" \
  --output tsv
```

**Example output**: `search-cpo-poc-abc123.search.windows.net`

**Set in .env**:
```bash
AZURE_SEARCH_ENDPOINT=https://search-cpo-poc-1337.search.windows.net
```

### Get Azure AI Search API Keys

```bash
# Get admin key (for indexing)
az search admin-key show \
  --service-name search-cpo-poc-1337 \
  --resource-group rg-poc \
  --query primaryKey \
  --output tsv
```

**Copy this value** → This is your `AZURE_SEARCH_ADMIN_KEY`

```bash
# Get query key (for searching)
az search query-key list \
  --service-name search-cpo-poc-1337 \
  --resource-group rg-poc \
  --query "[0].key" \
  --output tsv
```

**Copy this value** → This is your `AZURE_SEARCH_QUERY_KEY`

**Set in .env**:
```bash
AZURE_SEARCH_ADMIN_KEY=<your-admin-key-here>
AZURE_SEARCH_QUERY_KEY=<your-query-key-here>
AZURE_SEARCH_INDEX_NAME=approved-content-index
```

---

## Step 4: Azure AI Content Safety

### Create Content Safety Resource

```bash
# Create Content Safety resource
az cognitiveservices account create \
  --name safety-cpo-poc-1337 \
  --resource-group rg-poc \
  --location eastus2 \
  --kind ContentSafety \
  --sku S0

# Wait for deployment
```

### Get Content Safety Endpoint

```bash
# Get endpoint
az cognitiveservices account show \
  --name safety-cpo-poc-1337 \
  --resource-group rg-poc \
  --query properties.endpoint \
  --output tsv
```

**Example output**: `https://safety-cpo-poc-abc123.cognitiveservices.azure.com/`

**Set in .env**:
```bash
AZURE_CONTENT_SAFETY_ENDPOINT=https://safety-cpo-poc-1337.cognitiveservices.azure.com/
```

### Get Content Safety API Key

```bash
# Get API key
az cognitiveservices account keys list \
  --name safety-cpo-poc-1337 \
  --resource-group rg-poc \
  --query key1 \
  --output tsv
```

**Copy this value** → This is your `AZURE_CONTENT_SAFETY_API_KEY`

**Set in .env**:
```bash
AZURE_CONTENT_SAFETY_API_KEY=<your-key-here>
```

---

## Step 5: Azure Machine Learning (Optional)

### Create Azure ML Workspace

```bash
# Create Azure ML workspace
az ml workspace create \
  --name ml-personalization-poc \
  --resource-group rg-poc \
  --location eastus2

# Wait for deployment (may take 2-3 minutes)
```

**Set in .env**:
```bash
AZURE_ML_WORKSPACE_NAME=ml-personalization-poc
```

**Note**: The workspace uses the same subscription ID and resource group, so you can reference them:
```bash
# In your code, use the same values
AZURE_ML_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}
AZURE_ML_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP}
```

---

## Step 6: Azure Key Vault (Optional)

### Create Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name kv-cpo-poc-1337 \
  --resource-group rg-poc \
  --location eastus2 \
  --enable-rbac-authorization false

# Wait for deployment
```

**Note**: Key Vault names must be globally unique and between 3-24 characters.

### Get Key Vault URL

```bash
# Get vault URL
az keyvault show \
  --name kv-cpo-poc-1337 \
  --resource-group rg-poc \
  --query properties.vaultUri \
  --output tsv
```

**Example output**: `https://kv-cpo-poc-abc123.vault.azure.net/`

**Set in .env**:
```bash
AZURE_KEY_VAULT_URL=https://kv-cpo-poc-1337.vault.azure.net/
```

### Set Access Policy for Your User

```bash
# Get your user object ID
USER_OBJECT_ID=$(az ad signed-in-user show --query id --output tsv)

# Grant yourself access to secrets
az keyvault set-policy \
  --name kv-cpo-poc-1337 \
  --resource-group rg-poc \
  --object-id $USER_OBJECT_ID \
  --secret-permissions get list set delete
```

---

## Step 7: Application Insights (Optional)

### Create Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app insights-cpo-poc \
  --location eastus2 \
  --resource-group rg-poc \
  --application-type web

# Wait for deployment
```

### Get Connection String

```bash
# Get connection string
az monitor app-insights component show \
  --app insights-cpo-poc \
  --resource-group rg-poc \
  --query connectionString \
  --output tsv
```

**Copy this value** → This is your `APPLICATIONINSIGHTS_CONNECTION_STRING`

**Set in .env**:
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=<your-connection-string-here>
```

---

## Step 8: Verify All Resources

### List All Resources in Your Resource Group

```bash
az resource list \
  --resource-group rg-poc \
  --output table
```

**You should see**:
- Azure OpenAI account
- Azure AI Search service
- Content Safety account
- Azure ML workspace (optional)
- Key Vault (optional)
- Application Insights (optional)

---

## Step 9: Create Your .env File

### Copy the Template

```bash
# In your project directory
cp .env.sample .env
```

### Fill in Your Values

Open `.env` in your editor and fill in all the values you collected:

```bash
# Edit with your favorite editor
nano .env
# or
code .env
# or
vim .env
```

### Example Completed .env

```bash
# AZURE AUTHENTICATION
AZURE_SUBSCRIPTION_ID=12345678-1234-1234-1234-123456789abc
AZURE_RESOURCE_GROUP=rg-poc
AZURE_REGION=eastus2

# AZURE OPENAI
AZURE_OPENAI_ENDPOINT=https://openai-cpo-poc-abc123.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_API_KEY=abc123def456...

# AZURE AI SEARCH
AZURE_SEARCH_ENDPOINT=https://search-cpo-poc-abc123.search.windows.net
AZURE_SEARCH_INDEX_NAME=approved-content-index
AZURE_SEARCH_ADMIN_KEY=abc123def456...
AZURE_SEARCH_QUERY_KEY=xyz789uvw012...

# AZURE AI CONTENT SAFETY
AZURE_CONTENT_SAFETY_ENDPOINT=https://safety-cpo-poc-abc123.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_API_KEY=abc123def456...

# OPTIONAL: Azure ML
AZURE_ML_WORKSPACE_NAME=ml-personalization-poc

# OPTIONAL: Key Vault
AZURE_KEY_VAULT_URL=https://kv-cpo-poc-abc123.vault.azure.net/

# OPTIONAL: Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# PROJECT CONFIG
LOG_LEVEL=INFO
SAFETY_THRESHOLD=4
MAX_TOKENS=1000
TEMPERATURE=0.7
```

---

## Step 10: Test Your Configuration

### Create a Test Script

Create `scripts/test_azure_connection.py`:

```python
#!/usr/bin/env python3
"""
Test Azure service connections.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_config():
    """Test that all required environment variables are set."""
    required_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_ADMIN_KEY",
        "AZURE_CONTENT_SAFETY_ENDPOINT",
        "AZURE_CONTENT_SAFETY_API_KEY",
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_openai():
    """Test Azure OpenAI connection."""
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        )
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        print(f"✅ Azure OpenAI: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Azure OpenAI: {e}")
        return False

def test_search():
    """Test Azure AI Search connection."""
    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        
        client = SearchIndexClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
        )
        
        # List indexes (should work even if empty)
        indexes = list(client.list_indexes())
        print(f"✅ Azure AI Search: Connected ({len(indexes)} indexes)")
        return True
    except Exception as e:
        print(f"❌ Azure AI Search: {e}")
        return False

def test_content_safety():
    """Test Azure Content Safety connection."""
    try:
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.core.credentials import AzureKeyCredential
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        
        client = ContentSafetyClient(
            endpoint=os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_CONTENT_SAFETY_API_KEY"))
        )
        
        # Test with safe content
        request = AnalyzeTextOptions(text="This is a test message.")
        response = client.analyze_text(request)
        
        print(f"✅ Azure Content Safety: Connected (test passed)")
        return True
    except Exception as e:
        print(f"❌ Azure Content Safety: {e}")
        return False

def main():
    print("Testing Azure Configuration...\n")
    
    results = []
    results.append(("Configuration", test_config()))
    
    if results[0][1]:  # Only test services if config is valid
        results.append(("Azure OpenAI", test_openai()))
        results.append(("Azure AI Search", test_search()))
        results.append(("Content Safety", test_content_safety()))
    
    print("\n" + "="*50)
    print("Summary:")
    for service, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {service}")
    
    all_passed = all(result[1] for result in results)
    print("="*50)
    
    if all_passed:
        print("\n🎉 All tests passed! Your Azure environment is ready.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Run the Test

```bash
# Make executable
chmod +x scripts/test_azure_connection.py

# Run test
python scripts/test_azure_connection.py
```

**Expected output**:
```
Testing Azure Configuration...

✅ All required environment variables are set
✅ Azure OpenAI: test successful
✅ Azure AI Search: Connected (0 indexes)
✅ Azure Content Safety: Connected (test passed)

==================================================
Summary:
✅ PASS: Configuration
✅ PASS: Azure OpenAI
✅ PASS: Azure AI Search
✅ PASS: Content Safety
==================================================

🎉 All tests passed! Your Azure environment is ready.
```

---

## Troubleshooting

### Issue: "Resource name already exists"

**Solution**: Azure resource names must be globally unique. Add a unique suffix:
```bash
# Use your initials + random numbers
openai-cpo-poc-jd123
search-cpo-poc-jd123
```

### Issue: "Subscription not registered for namespace"

**Solution**: Register required resource providers:
```bash
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Search
az provider register --namespace Microsoft.MachineLearningServices
```

### Issue: "Location not supported"

**Solution**: Some services aren't available in all regions. Try `eastus`, `westus2`, or `westeurope`:
```bash
# Check available locations for a service
az cognitiveservices account list-skus --kind OpenAI --location eastus2
```

### Issue: "Insufficient quota"

**Solution**: Request quota increase:
1. Go to Azure Portal → Quotas
2. Select service (e.g., Azure OpenAI)
3. Request increase

---

## Security Best Practices

### 1. Verify .env is in .gitignore

```bash
# Check if .env is ignored
cat .gitignore | grep ".env"

# If not found, add it
echo ".env" >> .gitignore
```

### 2. Never Commit Secrets

```bash
# Install git-secrets to prevent accidental commits
pip install detect-secrets

# Scan for secrets
detect-secrets scan
```

### 3. Rotate Keys Regularly

```bash
# Regenerate Azure OpenAI key (example)
az cognitiveservices account keys regenerate \
  --name openai-cpo-poc-1337 \
  --resource-group rg-poc \
  --key-name key1
```

---

## Cost Estimation (POC)

Based on November 2025 pricing:

| Service | Tier | Estimated Cost (1 week) |
|---------|------|------------------------|
| Azure OpenAI (gpt-5-mini) | S0 | $5-15 (cost-optimized at $0.25/1M input tokens) |
| Azure AI Search | Standard | ~$75/month (~$18/week) |
| Content Safety | S0 | ~$5 (low volume) |
| Azure ML | Basic | Free tier available |
| Application Insights | Basic | ~$5 |
| **Total Estimated** | | **$50-100 for 1 week POC** |

### Set Budget Alert

```bash
# Create budget alert at $100
az consumption budget create \
  --budget-name personalization-poc-budget \
  --amount 100 \
  --category cost \
  --time-grain monthly \
  --start-date 2025-11-01 \
  --end-date 2025-12-31 \
  --resource-group rg-poc
```

---

## Next Steps

1. ✅ All Azure resources created
2. ✅ All environment variables in `.env`
3. ✅ Connection test passed
4. → **Proceed to Day 1: Implementation** (see `tasks.md`)

---

**Questions or Issues?**
- Azure Support: https://portal.azure.com → Support
- Documentation: https://learn.microsoft.com/azure
- Project Slack: #personalization-dev