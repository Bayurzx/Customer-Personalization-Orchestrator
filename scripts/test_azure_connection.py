#!/usr/bin/env python3
"""
Test Azure service connections for Customer Personalization Orchestrator.

This script tests connectivity to all required Azure services:
- Azure OpenAI
- Azure AI Search  
- Azure AI Content Safety

Run this after provisioning Azure resources to verify everything is working.
"""

import os
import sys
from dotenv import load_dotenv

def test_config():
    """Test that all required environment variables are set."""
    print("🔧 Testing Configuration...")
    
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
    print("\n🤖 Testing Azure OpenAI...")
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        )
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": "Say 'Azure OpenAI connection successful'"}],
            max_completion_tokens=20
            # Note: gpt-5-mini only supports default temperature (1)
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Azure OpenAI: {result}")
        print(f"   Model: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')} (cost-optimized)")
        print(f"   Tokens used: {response.usage.total_tokens}")
        
        # Calculate cost with gpt-5-mini pricing
        input_cost = (response.usage.prompt_tokens / 1000) * 0.00025  # $0.25 per 1M tokens
        output_cost = (response.usage.completion_tokens / 1000) * 0.002  # $2.00 per 1M tokens
        total_cost = input_cost + output_cost
        print(f"   Estimated cost: ${total_cost:.6f} (input: ${input_cost:.6f}, output: ${output_cost:.6f})")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI: {e}")
        return False

def test_search():
    """Test Azure AI Search connection."""
    print("\n🔍 Testing Azure AI Search...")
    
    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        
        client = SearchIndexClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
        )
        
        # List indexes (should work even if empty)
        indexes = list(client.list_indexes())
        print(f"✅ Azure AI Search: Connected successfully")
        print(f"   Endpoint: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
        print(f"   Indexes found: {len(indexes)}")
        
        if indexes:
            for idx in indexes:
                print(f"   - {idx.name}")
        else:
            print("   - No indexes found (this is normal for new service)")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure AI Search: {e}")
        return False

def test_content_safety():
    """Test Azure Content Safety connection."""
    print("\n🛡️ Testing Azure AI Content Safety...")
    
    try:
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.core.credentials import AzureKeyCredential
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        
        client = ContentSafetyClient(
            endpoint=os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_CONTENT_SAFETY_API_KEY"))
        )
        
        # Test with safe content
        request = AnalyzeTextOptions(text="This is a safe test message for content safety.")
        response = client.analyze_text(request)
        
        print(f"✅ Azure AI Content Safety: Connected successfully")
        print(f"   Endpoint: {os.getenv('AZURE_CONTENT_SAFETY_ENDPOINT')}")
        
        # Handle different response formats
        try:
            categories = response.categories_analysis if hasattr(response, 'categories_analysis') else []
            if categories:
                print(f"   Test result - Categories analyzed: {len(categories)}")
                for i, category in enumerate(categories):
                    category_names = ['Hate', 'Violence', 'Self-harm', 'Sexual']
                    if i < len(category_names):
                        print(f"   Test result - {category_names[i]}: {category.severity}")
            else:
                print(f"   Test completed successfully (safe content detected)")
        except Exception as detail_error:
            print(f"   Test completed successfully (response format: {type(response)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure AI Content Safety: {e}")
        return False

def test_integrations():
    """Test that our integration modules can be imported."""
    print("\n📦 Testing Integration Modules...")
    
    try:
        # Test if we can import our integration modules (they may not exist yet)
        sys.path.insert(0, '.')
        
        # These imports will fail if modules don't exist, which is expected for now
        try:
            from src.integrations.azure_openai import get_openai_client
            print("✅ Azure OpenAI integration module found")
        except ImportError:
            print("⚠️ Azure OpenAI integration module not found (will be created in next tasks)")
        
        try:
            from src.integrations.azure_search import get_search_client
            print("✅ Azure Search integration module found")
        except ImportError:
            print("⚠️ Azure Search integration module not found (will be created in next tasks)")
        
        try:
            from src.integrations.azure_content_safety import get_safety_client
            print("✅ Content Safety integration module found")
        except ImportError:
            print("⚠️ Content Safety integration module not found (will be created in next tasks)")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration modules test: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Azure Configuration for Customer Personalization Orchestrator")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Run all tests
    results = []
    results.append(("Configuration", test_config()))
    
    if results[0][1]:  # Only test services if config is valid
        results.append(("Azure OpenAI", test_openai()))
        results.append(("Azure AI Search", test_search()))
        results.append(("Azure AI Content Safety", test_content_safety()))
        results.append(("Integration Modules", test_integrations()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("📋 Test Summary:")
    print("=" * 80)
    
    for service, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {service}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 All tests passed! Your Azure environment is ready.")
        print("\n📋 Next Steps:")
        print("1. ✅ Azure resources provisioned and tested")
        print("2. → Proceed to Task 1.3: Sample Data Preparation")
        print("3. → Continue with remaining implementation tasks")
        
        print(f"\n💰 Cost Monitoring:")
        print(f"- Monitor usage in Azure Portal → Cost Management")
        print(f"- Estimated POC cost: $25-50 for 1 week (using cost-optimized gpt-5-mini)")
        print(f"- gpt-5-mini pricing: $0.25/1M input tokens, $2.00/1M output tokens")
        
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify all Azure resources are created")
        print("2. Check API keys are correct in .env file")
        print("3. Ensure model deployment is complete")
        print("4. Check network connectivity")
        
        sys.exit(1)

if __name__ == "__main__":
    main()