#!/usr/bin/env python3
"""
Azure Resource Provisioning Script for Customer Personalization Orchestrator

This script provisions all required Azure resources for the POC:
- Azure OpenAI Service with model deployment
- Azure AI Search Service
- Azure AI Content Safety Service
- Azure Machine Learning Workspace (optional)
- Azure Key Vault (optional)

Prerequisites:
- Azure CLI installed and logged in
- Contributor/Owner role on subscription
- Required resource providers registered
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run Azure CLI command and return result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr}")
        if check:
            raise
        return e

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in."""
    try:
        # Check if az command exists
        result = run_command(["az", "--version"], check=False)
        if result.returncode != 0:
            print("❌ Azure CLI not found. Please install: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli")
            return False
        
        # Check if logged in
        result = run_command(["az", "account", "show"], check=False)
        if result.returncode != 0:
            print("❌ Not logged in to Azure. Please run: az login")
            return False
        
        print("✅ Azure CLI is installed and logged in")
        return True
    except Exception as e:
        print(f"❌ Error checking Azure CLI: {e}")
        return False

def get_subscription_id() -> Optional[str]:
    """Get current Azure subscription ID."""
    try:
        result = run_command(["az", "account", "show", "--query", "id", "--output", "tsv"])
        subscription_id = result.stdout.strip()
        print(f"✅ Using subscription: {subscription_id}")
        return subscription_id
    except Exception as e:
        print(f"❌ Error getting subscription ID: {e}")
        return None

def create_resource_group(name: str, location: str) -> bool:
    """Create Azure resource group."""
    try:
        print(f"\n📦 Creating resource group: {name}")
        
        # Check if already exists
        result = run_command([
            "az", "group", "show", 
            "--name", name
        ], check=False)
        
        if result.returncode == 0:
            print(f"✅ Resource group {name} already exists")
            return True
        
        # Create new resource group
        run_command([
            "az", "group", "create",
            "--name", name,
            "--location", location
        ])
        
        print(f"✅ Created resource group: {name}")
        return True
    except Exception as e:
        print(f"❌ Error creating resource group: {e}")
        return False

def create_openai_resource(name: str, resource_group: str, location: str) -> Optional[Dict]:
    """Create Azure OpenAI resource."""
    try:
        print(f"\n🤖 Creating Azure OpenAI resource: {name}")
        
        # Check if already exists
        result = run_command([
            "az", "cognitiveservices", "account", "show",
            "--name", name,
            "--resource-group", resource_group
        ], check=False)
        
        if result.returncode == 0:
            print(f"✅ Azure OpenAI resource {name} already exists")
        else:
            # Create new resource
            run_command([
                "az", "cognitiveservices", "account", "create",
                "--name", name,
                "--resource-group", resource_group,
                "--location", location,
                "--kind", "OpenAI",
                "--sku", "S0",
                "--custom-domain", name
            ])
            print(f"✅ Created Azure OpenAI resource: {name}")
        
        # Get endpoint
        result = run_command([
            "az", "cognitiveservices", "account", "show",
            "--name", name,
            "--resource-group", resource_group,
            "--query", "properties.endpoint",
            "--output", "tsv"
        ])
        endpoint = result.stdout.strip()
        
        # Get API key
        result = run_command([
            "az", "cognitiveservices", "account", "keys", "list",
            "--name", name,
            "--resource-group", resource_group,
            "--query", "key1",
            "--output", "tsv"
        ])
        api_key = result.stdout.strip()
        
        return {
            "endpoint": endpoint,
            "api_key": api_key,
            "resource_name": name
        }
        
    except Exception as e:
        print(f"❌ Error creating Azure OpenAI resource: {e}")
        return None

def deploy_openai_model(resource_name: str, resource_group: str, deployment_name: str = "gpt-5-mini") -> bool:
    """Deploy model to Azure OpenAI resource."""
    try:
        print(f"\n🚀 Deploying model: {deployment_name}")
        
        # Check if deployment already exists
        result = run_command([
            "az", "cognitiveservices", "account", "deployment", "list",
            "--name", resource_name,
            "--resource-group", resource_group,
            "--query", f"[?name=='{deployment_name}']",
            "--output", "json"
        ], check=False)
        
        if result.returncode == 0 and result.stdout.strip() != "[]":
            print(f"✅ Model deployment {deployment_name} already exists")
            return True
        
        # Deploy model
        run_command([
            "az", "cognitiveservices", "account", "deployment", "create",
            "--name", resource_name,
            "--resource-group", resource_group,
            "--deployment-name", deployment_name,
            "--model-name", "gpt-5-mini",
            "--model-version", "2024-08-06",
            "--model-format", "OpenAI",
            "--sku-capacity", "10",
            "--sku-name", "Standard"
        ])
        
        print(f"✅ Deployed model: {deployment_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying model: {e}")
        print("💡 You may need to deploy the model manually in Azure OpenAI Studio")
        return False

def create_search_service(name: str, resource_group: str, location: str) -> Optional[Dict]:
    """Create Azure AI Search service."""
    try:
        print(f"\n🔍 Creating Azure AI Search service: {name}")
        
        # Check if already exists
        result = run_command([
            "az", "search", "service", "show",
            "--name", name,
            "--resource-group", resource_group
        ], check=False)
        
        if result.returncode == 0:
            print(f"✅ Azure AI Search service {name} already exists")
        else:
            # Create new service
            run_command([
                "az", "search", "service", "create",
                "--name", name,
                "--resource-group", resource_group,
                "--location", location,
                "--sku", "Standard",
                "--partition-count", "1",
                "--replica-count", "1"
            ])
            print(f"✅ Created Azure AI Search service: {name}")
        
        # Get endpoint
        result = run_command([
            "az", "search", "service", "show",
            "--name", name,
            "--resource-group", resource_group,
            "--query", "hostName",
            "--output", "tsv"
        ])
        hostname = result.stdout.strip()
        endpoint = f"https://{hostname}"
        
        # Get admin key
        result = run_command([
            "az", "search", "admin-key", "show",
            "--service-name", name,
            "--resource-group", resource_group,
            "--query", "primaryKey",
            "--output", "tsv"
        ])
        admin_key = result.stdout.strip()
        
        # Get query key
        result = run_command([
            "az", "search", "query-key", "list",
            "--service-name", name,
            "--resource-group", resource_group,
            "--query", "[0].key",
            "--output", "tsv"
        ])
        query_key = result.stdout.strip()
        
        return {
            "endpoint": endpoint,
            "admin_key": admin_key,
            "query_key": query_key,
            "service_name": name
        }
        
    except Exception as e:
        print(f"❌ Error creating Azure AI Search service: {e}")
        return None

def create_content_safety_resource(name: str, resource_group: str, location: str) -> Optional[Dict]:
    """Create Azure AI Content Safety resource."""
    try:
        print(f"\n🛡️ Creating Azure AI Content Safety resource: {name}")
        
        # Check if already exists
        result = run_command([
            "az", "cognitiveservices", "account", "show",
            "--name", name,
            "--resource-group", resource_group
        ], check=False)
        
        if result.returncode == 0:
            print(f"✅ Azure AI Content Safety resource {name} already exists")
        else:
            # Create new resource
            run_command([
                "az", "cognitiveservices", "account", "create",
                "--name", name,
                "--resource-group", resource_group,
                "--location", location,
                "--kind", "ContentSafety",
                "--sku", "S0"
            ])
            print(f"✅ Created Azure AI Content Safety resource: {name}")
        
        # Get endpoint
        result = run_command([
            "az", "cognitiveservices", "account", "show",
            "--name", name,
            "--resource-group", resource_group,
            "--query", "properties.endpoint",
            "--output", "tsv"
        ])
        endpoint = result.stdout.strip()
        
        # Get API key
        result = run_command([
            "az", "cognitiveservices", "account", "keys", "list",
            "--name", name,
            "--resource-group", resource_group,
            "--query", "key1",
            "--output", "tsv"
        ])
        api_key = result.stdout.strip()
        
        return {
            "endpoint": endpoint,
            "api_key": api_key,
            "resource_name": name
        }
        
    except Exception as e:
        print(f"❌ Error creating Azure AI Content Safety resource: {e}")
        return None

def create_ml_workspace(name: str, resource_group: str, location: str) -> Optional[Dict]:
    """Create Azure Machine Learning workspace (optional)."""
    try:
        print(f"\n🧠 Creating Azure ML workspace: {name}")
        
        # Check if already exists
        result = run_command([
            "az", "ml", "workspace", "show",
            "--name", name,
            "--resource-group", resource_group
        ], check=False)
        
        if result.returncode == 0:
            print(f"✅ Azure ML workspace {name} already exists")
            return {"workspace_name": name}
        
        # Create new workspace
        run_command([
            "az", "ml", "workspace", "create",
            "--name", name,
            "--resource-group", resource_group,
            "--location", location
        ])
        
        print(f"✅ Created Azure ML workspace: {name}")
        return {"workspace_name": name}
        
    except Exception as e:
        print(f"⚠️ Error creating Azure ML workspace (optional): {e}")
        print("💡 You can create this manually later if needed")
        return None

def update_env_file(resources: Dict) -> bool:
    """Update .env file with resource information."""
    try:
        print(f"\n📝 Updating .env file with resource information")
        
        # Read current .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Update values
        updates = {
            "AZURE_SUBSCRIPTION_ID": resources.get("subscription_id", ""),
            "AZURE_RESOURCE_GROUP": resources.get("resource_group", ""),
            "AZURE_REGION": resources.get("location", ""),
        }
        
        if "openai" in resources:
            updates.update({
                "AZURE_OPENAI_ENDPOINT": resources["openai"]["endpoint"],
                "AZURE_OPENAI_API_KEY": resources["openai"]["api_key"],
                "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-5-mini",
                "AZURE_OPENAI_API_VERSION": "2024-10-21"
            })
        
        if "search" in resources:
            updates.update({
                "AZURE_SEARCH_ENDPOINT": resources["search"]["endpoint"],
                "AZURE_SEARCH_ADMIN_KEY": resources["search"]["admin_key"],
                "AZURE_SEARCH_QUERY_KEY": resources["search"]["query_key"],
                "AZURE_SEARCH_INDEX_NAME": "approved-content-index"
            })
        
        if "content_safety" in resources:
            updates.update({
                "AZURE_CONTENT_SAFETY_ENDPOINT": resources["content_safety"]["endpoint"],
                "AZURE_CONTENT_SAFETY_API_KEY": resources["content_safety"]["api_key"]
            })
        
        if "ml" in resources:
            updates.update({
                "AZURE_ML_WORKSPACE_NAME": resources["ml"]["workspace_name"]
            })
        
        # Apply updates
        for key, value in updates.items():
            if value:  # Only update if we have a value
                # Replace existing value or add new line
                if f"{key}=" in content:
                    # Find and replace existing line
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f"{key}="):
                            lines[i] = f"{key}={value}"
                            break
                    content = '\n'.join(lines)
                else:
                    # Add new line
                    content += f"\n{key}={value}"
        
        # Write updated content
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated .env file with resource information")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def create_azure_config(resources: Dict) -> bool:
    """Create config/azure_config.yaml file."""
    try:
        print(f"\n📄 Creating config/azure_config.yaml")
        
        config = {
            "azure_openai": {
                "endpoint": "${AZURE_OPENAI_ENDPOINT}",
                "deployment_name": "${AZURE_OPENAI_DEPLOYMENT_NAME}",
                "api_version": "${AZURE_OPENAI_API_VERSION}",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            },
            "azure_search": {
                "endpoint": "${AZURE_SEARCH_ENDPOINT}",
                "index_name": "${AZURE_SEARCH_INDEX_NAME}",
                "api_version": "2024-11-01-preview"
            },
            "azure_content_safety": {
                "endpoint": "${AZURE_CONTENT_SAFETY_ENDPOINT}",
                "api_version": "2024-09-01"
            },
            "authentication": {
                "method": "api_key",  # For POC, production should use managed_identity
                "note": "Using API keys for POC. Production should use Managed Identity."
            }
        }
        
        if "ml" in resources:
            config["azure_ml"] = {
                "subscription_id": "${AZURE_SUBSCRIPTION_ID}",
                "resource_group": "${AZURE_RESOURCE_GROUP}",
                "workspace_name": "${AZURE_ML_WORKSPACE_NAME}"
            }
        
        # Ensure config directory exists
        os.makedirs("config", exist_ok=True)
        
        # Write YAML file
        import yaml
        with open("config/azure_config.yaml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Created config/azure_config.yaml")
        return True
        
    except Exception as e:
        print(f"❌ Error creating azure_config.yaml: {e}")
        return False

def main():
    """Main provisioning function."""
    print("🚀 Azure Resource Provisioning for Customer Personalization Orchestrator")
    print("=" * 80)
    
    # Configuration
    unique_suffix = "cpo1337"  # Change this to make resources unique
    resource_group = "rg-poc"
    location = "eastus2"
    
    resources = {
        "subscription_id": "",
        "resource_group": resource_group,
        "location": location
    }
    
    # Step 1: Check prerequisites
    if not check_azure_cli():
        sys.exit(1)
    
    subscription_id = get_subscription_id()
    if not subscription_id:
        sys.exit(1)
    resources["subscription_id"] = subscription_id
    
    # Step 2: Create resource group
    if not create_resource_group(resource_group, location):
        sys.exit(1)
    
    # Step 3: Create Azure OpenAI resource
    openai_name = f"openai-{unique_suffix}"
    openai_info = create_openai_resource(openai_name, resource_group, location)
    if openai_info:
        resources["openai"] = openai_info
        # Deploy model
        deploy_openai_model(openai_name, resource_group, "gpt-5-mini")
    else:
        print("⚠️ Failed to create Azure OpenAI resource")
    
    # Step 4: Create Azure AI Search service
    search_name = f"search-{unique_suffix}"
    search_info = create_search_service(search_name, resource_group, location)
    if search_info:
        resources["search"] = search_info
    else:
        print("⚠️ Failed to create Azure AI Search service")
    
    # Step 5: Create Azure AI Content Safety resource
    safety_name = f"safety-{unique_suffix}"
    safety_info = create_content_safety_resource(safety_name, resource_group, location)
    if safety_info:
        resources["content_safety"] = safety_info
    else:
        print("⚠️ Failed to create Azure AI Content Safety resource")
    
    # Step 6: Create Azure ML workspace (optional)
    ml_name = f"ml-personalization-poc"
    ml_info = create_ml_workspace(ml_name, resource_group, location)
    if ml_info:
        resources["ml"] = ml_info
    
    # Step 7: Update configuration files
    update_env_file(resources)
    create_azure_config(resources)
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("🎉 Azure Resource Provisioning Complete!")
    print("=" * 80)
    
    print("\n📋 Created Resources:")
    if "openai" in resources:
        print(f"✅ Azure OpenAI: {resources['openai']['resource_name']}")
        print(f"   Endpoint: {resources['openai']['endpoint']}")
    
    if "search" in resources:
        print(f"✅ Azure AI Search: {resources['search']['service_name']}")
        print(f"   Endpoint: {resources['search']['endpoint']}")
    
    if "content_safety" in resources:
        print(f"✅ Azure AI Content Safety: {resources['content_safety']['resource_name']}")
        print(f"   Endpoint: {resources['content_safety']['endpoint']}")
    
    if "ml" in resources:
        print(f"✅ Azure ML Workspace: {resources['ml']['workspace_name']}")
    
    print(f"\n📁 Updated Files:")
    print(f"✅ .env - Environment variables")
    print(f"✅ config/azure_config.yaml - Service configuration")
    
    print(f"\n🔧 Next Steps:")
    print(f"1. Run: python scripts/test_azure_connection.py")
    print(f"2. Verify all services are working")
    print(f"3. Proceed to Task 1.3: Sample Data Preparation")
    
    print(f"\n💰 Estimated Cost: $50-100 for 1 week POC")
    print(f"💡 Monitor usage in Azure Portal → Cost Management")

if __name__ == "__main__":
    main()