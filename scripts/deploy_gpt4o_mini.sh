#!/bin/bash
set -euo pipefail

# Deploy gpt-4o-mini to replace gpt-5-mini
# This script updates the existing Azure OpenAI resource with gpt-4o-mini deployment

# Configuration - update these to match your existing resources
RESOURCE_GROUP="rg-poc"
OPENAI_NAME="openai-cpo1337"  # Update this to match your existing resource name
OLD_DEPLOYMENT="gpt-5-mini"
NEW_DEPLOYMENT="gpt-4o-mini"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "\n${BLUE}📋 $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install it first."
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run: az login"
        exit 1
    fi
    
    # Check if OpenAI resource exists
    if ! az cognitiveservices account show --name "$OPENAI_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Azure OpenAI resource '$OPENAI_NAME' not found in resource group '$RESOURCE_GROUP'"
        log_error "Please update the OPENAI_NAME variable in this script to match your resource"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Deploy gpt-4o-mini model
deploy_gpt4o_mini() {
    log_step "Deploying gpt-4o-mini model..."
    
    # Check if gpt-4o-mini deployment already exists
    if az cognitiveservices account deployment show \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --deployment-name "$NEW_DEPLOYMENT" &> /dev/null; then
        log_success "gpt-4o-mini deployment already exists"
        return 0
    fi
    
    log_info "Creating gpt-4o-mini deployment (this may take a few minutes)..."
    
    # Deploy gpt-4o-mini
    if az cognitiveservices account deployment create \
        --name "$OPENAI_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --deployment-name "$NEW_DEPLOYMENT" \
        --model-name "gpt-4o-mini" \
        --model-version "2024-07-18" \
        --model-format OpenAI \
        --sku-capacity 10 \
        --sku-name Standard > /dev/null; then
        log_success "Successfully deployed gpt-4o-mini"
    else
        log_error "Failed to deploy gpt-4o-mini automatically"
        log_info "You can deploy manually in Azure OpenAI Studio:"
        log_info "1. Go to https://oai.azure.com/"
        log_info "2. Select your resource: $OPENAI_NAME"
        log_info "3. Go to Deployments → Create new deployment"
        log_info "4. Model: gpt-4o-mini, Version: 2024-07-18"
        log_info "5. Deployment name: $NEW_DEPLOYMENT"
        exit 1
    fi
}

# Test the new deployment
test_deployment() {
    log_step "Testing gpt-4o-mini deployment..."
    
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
    
    # Test API call using curl
    log_info "Testing API call to gpt-4o-mini..."
    
    RESPONSE=$(curl -s -X POST "${OPENAI_ENDPOINT}openai/deployments/${NEW_DEPLOYMENT}/chat/completions?api-version=2024-10-21" \
        -H "Content-Type: application/json" \
        -H "api-key: ${OPENAI_API_KEY}" \
        -d '{
            "messages": [
                {"role": "user", "content": "Say \"gpt-4o-mini deployment successful\""}
            ],
            "max_tokens": 20
        }')
    
    if echo "$RESPONSE" | grep -q "gpt-4o-mini deployment successful"; then
        log_success "gpt-4o-mini deployment test passed"
    else
        log_warning "Deployment test may have issues. Response:"
        echo "$RESPONSE"
    fi
}

# Update .env file
update_env_file() {
    log_step "Updating .env file..."
    
    if [[ ! -f .env ]]; then
        log_warning ".env file not found. Please create it manually."
        return 1
    fi
    
    # Update deployment name
    if grep -q "^AZURE_OPENAI_DEPLOYMENT_NAME=" .env; then
        sed -i "s|^AZURE_OPENAI_DEPLOYMENT_NAME=.*|AZURE_OPENAI_DEPLOYMENT_NAME=${NEW_DEPLOYMENT}|" .env
        log_success "Updated AZURE_OPENAI_DEPLOYMENT_NAME in .env"
    else
        echo "AZURE_OPENAI_DEPLOYMENT_NAME=${NEW_DEPLOYMENT}" >> .env
        log_success "Added AZURE_OPENAI_DEPLOYMENT_NAME to .env"
    fi
}

# Optional: Remove old deployment
remove_old_deployment() {
    log_step "Removing old gpt-5-mini deployment (optional)..."
    
    read -p "Do you want to remove the old gpt-5-mini deployment? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if az cognitiveservices account deployment delete \
            --name "$OPENAI_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --deployment-name "$OLD_DEPLOYMENT" \
            --yes > /dev/null; then
            log_success "Removed old gpt-5-mini deployment"
        else
            log_warning "Failed to remove old deployment (it may not exist)"
        fi
    else
        log_info "Keeping old gpt-5-mini deployment"
    fi
}

# Main function
main() {
    echo "🚀 Deploying gpt-4o-mini to Azure OpenAI"
    echo "========================================"
    
    check_prerequisites
    deploy_gpt4o_mini
    test_deployment
    update_env_file
    remove_old_deployment
    
    echo ""
    echo "========================================"
    log_success "gpt-4o-mini deployment complete!"
    echo "========================================"
    
    echo ""
    echo "📋 What was done:"
    echo "✅ Deployed gpt-4o-mini model"
    echo "✅ Tested deployment with API call"
    echo "✅ Updated .env file"
    
    echo ""
    echo "💰 Cost Comparison:"
    echo "📉 gpt-4o-mini: \$0.15/1M input, \$0.60/1M output"
    echo "📈 gpt-5-mini: \$0.25/1M input, \$2.00/1M output"
    echo "💡 gpt-4o-mini is cheaper for output tokens (3.3x less)"
    
    echo ""
    echo "🔧 Next Steps:"
    echo "1. Run: python scripts/test_fixed_openai.py"
    echo "2. Test prompt templates: python scripts/single_prompt_test.py"
    echo "3. Update any remaining references to gpt-5-mini in your code"
    
    echo ""
    log_success "Ready to test with gpt-4o-mini!"
}

# Run main function
main "$@"