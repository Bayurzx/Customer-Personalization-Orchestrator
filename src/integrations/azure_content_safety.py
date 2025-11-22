"""
Azure AI Content Safety Integration Module

This module provides a wrapper around the Azure AI Content Safety API for the Customer Personalization Orchestrator.
It handles content analysis and safety policy enforcement.
"""

import os
from typing import Dict, Any, Optional
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_safety_client() -> ContentSafetyClient:
    """
    Create and return an Azure AI Content Safety client.
    
    Returns:
        ContentSafetyClient: Configured client instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
    api_key = os.getenv("AZURE_CONTENT_SAFETY_API_KEY")
    
    if not endpoint or not api_key:
        raise ValueError("Missing required Azure AI Content Safety configuration")
    
    return ContentSafetyClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )

def analyze_text_safety(text: str) -> Dict[str, Any]:
    """
    Analyze text for safety violations.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Dict containing safety analysis results
        
    Raises:
        Exception: If API call fails
    """
    client = get_safety_client()
    request = AnalyzeTextOptions(text=text)
    response = client.analyze_text(request)
    
    # Parse response based on actual API format
    result = {
        "text": text,
        "safe": True,
        "categories": []
    }
    
    if hasattr(response, 'categories_analysis'):
        categories = response.categories_analysis
        category_names = ['hate', 'violence', 'self_harm', 'sexual']
        
        for i, category in enumerate(categories):
            if i < len(category_names):
                severity = category.severity
                result['categories'].append({
                    'category': category_names[i],
                    'severity': severity
                })
                
                # Mark as unsafe if any category exceeds threshold
                if severity > 4:  # Medium threshold
                    result['safe'] = False
    
    return result

def test_connection() -> str:
    """
    Test the Azure AI Content Safety connection.
    
    Returns:
        str: Success message if connection works
        
    Raises:
        Exception: If connection fails
    """
    result = analyze_text_safety("This is a safe test message.")
    return f"Connection successful. Analysis completed for test message."

if __name__ == "__main__":
    # Test the connection when run directly
    try:
        result = test_connection()
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")