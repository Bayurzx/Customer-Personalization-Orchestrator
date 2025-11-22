#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Azure Resource Provisioning Script for Customer Personalization Orchestrator
# This script provisions all required Azure resources for the POC with proper error handling

# Configuration
UNIQUE_SUFFIX="cpo1337"  # Change this to make resources unique
RESOURCE_GROUP="rg-poc"
LOCATION="eastus2"
OPENAI_NAME="openai-${UNIQUE_SUFFIX}"
SEARCH_NAME="search-${UNIQUE_SUFFIX}"
SAFETY_NAME="safety-${UNIQUE_SUFFIX}"
ML_NAME="ml-personalization-poc"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${BLUE}📋 $1${NC}"
}

# Error handler
error_exit() {
    log_error "Script failed at line $1. Exiting."
    exit 1
}

trap 'error_exit $LINENO' ERR

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    log_success "Azure CLI is installed"
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run: az login"
        exit 1
    fi
    log_success "Logged in to Azure"
    
    # Get subscription info
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    SUBSCRIPTION_NAME=$(az account show --query name --output tsv)
    log_success "Using subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
}

# Create resource group
create_resource_group() {
    log_step "Creating resource group: $RESOURCE_GROUP"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Resource group $RESOURCE_GROUP already exists"
    else
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" > /dev/null
        log_success "Created resource group: $RESOURCE_GROUP"
    fi
}

# Create Azure OpenAI resource
create_openai_resource() {
    log_step "Creating Azure OpenAI resource: $OPENAI_NAME"
    
    if az cognitiveservices account show --name "$OPENAI_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Azure OpenAI resource $OPENAI_NAME already exists"
    else
        log_info "Creating Azure OpenAI resource (this may take a few minutes)..."
        az cognitiveservices account create \
            --name "$OPENAI_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --kind OpenAI \
            --sku S0 \
            --custom-domain "$OPENAI_NAME" \
            --yes > /dev/null
        log_success "Created Azure OpenAI resource: $OPENAI_NAME"
    fi
    
    # Get endpoint and key
    OPENAI_ENDPOINT=$(az cognitiveservices account show \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.endpoint" \
        --output tsv)
    
    OPENAI_API_KEY=$(az cognitiveservices account keys list \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "key1" \
        --output tsv)
    
    log_success "OpenAI endpoint: $OPENAI_ENDPOINT"
}

# Deploy OpenAI model
deploy_openai_model() {
    log_step "Deploying gpt-5-mini model..."
    
    # Check if deployment already exists
    if az cognitiveservices account deployment show \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --deployment-name "gpt-5-mini" &> /dev/null; then
        log_success "Model deployment gpt-5-mini already exists"
    else
        log_info "Deploying gpt-5-mini model (this may take a few minutes)..."
        if az cognitiveservices account deployment create \
            --name "$OPENAI_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --deployment-name "gpt-5-mini" \
            --model-name "gpt-5-mini" \
            --model-version "2024-08-06" \
            --model-format OpenAI \
            --sku-capacity 10 \
            --sku-name Standard > /dev/null; then
            log_success "Deployed gpt-5-mini model"
        else
            log_warning "Failed to deploy model automatically. You may need to deploy manually in Azure OpenAI Studio"
        fi
    fi
}

# Create Azure AI Search service
create_search_service() {
    log_step "Creating Azure AI Search service: $SEARCH_NAME"
    
    if az search service show --name "$SEARCH_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Azure AI Search service $SEARCH_NAME already exists"
    else
        log_info "Creating Azure AI Search service (this may take a few minutes)..."
        az search service create \
            --name "$SEARCH_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --sku Standard \
            --partition-count 1 \
            --replica-count 1 > /dev/null
        log_success "Created Azure AI Search service: $SEARCH_NAME"
    fi
    
    # Get endpoint and keys
    SEARCH_HOSTNAME=$(az search service show \
        --name "$SEARCH_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "hostName" \
        --output tsv)
    SEARCH_ENDPOINT="https://$SEARCH_HOSTNAME"
    
    SEARCH_ADMIN_KEY=$(az search admin-key show \
        --service-name "$SEARCH_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "primaryKey" \
        --output tsv)
    
    SEARCH_QUERY_KEY=$(az search query-key list \
        --service-name "$SEARCH_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "[0].key" \
        --output tsv)
    
    log_success "Search endpoint: $SEARCH_ENDPOINT"
}

# Create Azure AI Content Safety resource
create_content_safety_resource() {
    log_step "Creating Azure AI Content Safety resource: $SAFETY_NAME"
    
    if az cognitiveservices account show --name "$SAFETY_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Azure AI Content Safety resource $SAFETY_NAME already exists"
    else
        log_info "Creating Azure AI Content Safety resource..."
        az cognitiveservices account create \
            --name "$SAFETY_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --kind ContentSafety \
            --sku S0 \
            --yes > /dev/null
        log_success "Created Azure AI Content Safety resource: $SAFETY_NAME"
    fi
    
    # Get endpoint and key
    SAFETY_ENDPOINT=$(az cognitiveservices account show \
        --name "$SAFETY_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.endpoint" \
        --output tsv)
    
    SAFETY_API_KEY=$(az cognitiveservices account keys list \
        --name "$SAFETY_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "key1" \
        --output tsv)
    
    log_success "Content Safety endpoint: $SAFETY_ENDPOINT"
}

# Create Azure ML workspace (optional)
create_ml_workspace() {
    log_step "Creating Azure ML workspace: $ML_NAME (optional)"
    
    # Check if ML extension is installed
    if ! az extension show --name ml &> /dev/null; then
        log_info "Installing Azure ML CLI extension..."
        az extension add --name ml --yes > /dev/null
    fi
    
    if az ml workspace show --name "$ML_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Azure ML workspace $ML_NAME already exists"
    else
        log_info "Creating Azure ML workspace..."
        if az ml workspace create \
            --name "$ML_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" > /dev/null; then
            log_success "Created Azure ML workspace: $ML_NAME"
        else
            log_warning "Failed to create Azure ML workspace (optional). You can create this manually later if needed"
            ML_NAME=""  # Clear the name so we don't try to use it later
        fi
    fi
}

# Update .env file
update_env_file() {
    log_step "Updating .env file with resource information"
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        touch .env
    fi
    
    # Function to update or add environment variable
    update_env_var() {
        local key=$1
        local value=$2
        
        if grep -q "^${key}=" .env; then
            # Update existing line
            sed -i "s|^${key}=.*|${key}=${value}|" .env
        else
            # Add new line
            echo "${key}=${value}" >> .env
        fi
    }
    
    # Update all variables
    update_env_var "AZURE_SUBSCRIPTION_ID" "$SUBSCRIPTION_ID"
    update_env_var "AZURE_RESOURCE_GROUP" "$RESOURCE_GROUP"
    update_env_var "AZURE_REGION" "$LOCATION"
    update_env_var "AZURE_OPENAI_ENDPOINT" "$OPENAI_ENDPOINT"
    update_env_var "AZURE_OPENAI_API_KEY" "$OPENAI_API_KEY"
    update_env_var "AZURE_OPENAI_DEPLOYMENT_NAME" "gpt-5-mini"
    update_env_var "AZURE_OPENAI_API_VERSION" "2024-10-21"
    update_env_var "AZURE_SEARCH_ENDPOINT" "$SEARCH_ENDPOINT"
    update_env_var "AZURE_SEARCH_ADMIN_KEY" "$SEARCH_ADMIN_KEY"
    update_env_var "AZURE_SEARCH_QUERY_KEY" "$SEARCH_QUERY_KEY"
    update_env_var "AZURE_SEARCH_INDEX_NAME" "approved-content-index"
    update_env_var "AZURE_CONTENT_SAFETY_ENDPOINT" "$SAFETY_ENDPOINT"
    update_env_var "AZURE_CONTENT_SAFETY_API_KEY" "$SAFETY_API_KEY"
    
    if [[ -n "$ML_NAME" ]]; then
        update_env_var "AZURE_ML_WORKSPACE_NAME" "$ML_NAME"
    fi
    
    log_success "Updated .env file with resource information"
}

# Create Azure config YAML
create_azure_config() {
    log_step "Creating config/azure_config.yaml"
    
    # Ensure config directory exists
    mkdir -p config
    
    cat > config/azure_config.yaml << EOF
azure_openai:
  endpoint: \${AZURE_OPENAI_ENDPOINT}
  deployment_name: \${AZURE_OPENAI_DEPLOYMENT_NAME}
  api_version: \${AZURE_OPENAI_API_VERSION}
  max_completion_tokens: 1000
  # Note: gpt-5-mini has limited parameter support
  # temperature, top_p, frequency_penalty, presence_penalty not supported

azure_search:
  endpoint: \${AZURE_SEARCH_ENDPOINT}
  index_name: \${AZURE_SEARCH_INDEX_NAME}
  api_version: "2024-11-01-preview"

azure_content_safety:
  endpoint: \${AZURE_CONTENT_SAFETY_ENDPOINT}
  api_version: "2024-09-01"

authentication:
  method: api_key  # For POC, production should use managed_identity
  note: "Using API keys for POC. Production should use Managed Identity."
EOF

    if [[ -n "$ML_NAME" ]]; then
        cat >> config/azure_config.yaml << EOF

azure_ml:
  subscription_id: \${AZURE_SUBSCRIPTION_ID}
  resource_group: \${AZURE_RESOURCE_GROUP}
  workspace_name: \${AZURE_ML_WORKSPACE_NAME}
EOF
    fi
    
    log_success "Created config/azure_config.yaml"
}

# Main function
main() {
    echo "🚀 Azure Resource Provisioning for Customer Personalization Orchestrator"
    echo "================================================================================"
    
    check_prerequisites
    create_resource_group
    create_openai_resource
    deploy_openai_model
    create_search_service
    create_content_safety_resource
    create_ml_workspace
    update_env_file
    create_azure_config
    
    # Summary
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}🎉 Azure Resource Provisioning Complete!${NC}"
    echo "================================================================================"
    
    echo ""
    echo "📋 Created Resources:"
    echo "✅ Azure OpenAI: $OPENAI_NAME"
    echo "   Endpoint: $OPENAI_ENDPOINT"
    echo "✅ Azure AI Search: $SEARCH_NAME"
    echo "   Endpoint: $SEARCH_ENDPOINT"
    echo "✅ Azure AI Content Safety: $SAFETY_NAME"
    echo "   Endpoint: $SAFETY_ENDPOINT"
    if [[ -n "$ML_NAME" ]]; then
        echo "✅ Azure ML Workspace: $ML_NAME"
    fi
    
    echo ""
    echo "📁 Updated Files:"
    echo "✅ .env - Environment variables"
    echo "✅ config/azure_config.yaml - Service configuration"
    
    echo ""
    echo "🔧 Next Steps:"
    echo "1. Run: python scripts/test_azure_connection.py"
    echo "2. Verify all services are working"
    echo "3. Proceed to Task 1.3: Sample Data Preparation"
    
    echo ""
    echo "💰 Estimated Cost: \$25-50 for 1 week POC (with gpt-5-mini)"
    echo "💡 Monitor usage in Azure Portal → Cost Management"
}

# Run main function
main "$@"