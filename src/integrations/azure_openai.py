"""
Azure OpenAI Integration Module

This module provides a wrapper around the Azure OpenAI API for the Customer Personalization Orchestrator.
It handles authentication, retry logic, and response parsing.
"""

import os
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client() -> AzureOpenAI:
    """
    Create and return an Azure OpenAI client.
    
    Returns:
        AzureOpenAI: Configured client instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    
    if not endpoint or not api_key:
        raise ValueError("Missing required Azure OpenAI configuration")
    
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )

def test_connection() -> str:
    """
    Test the Azure OpenAI connection.
    
    Returns:
        str: Success message if connection works
        
    Raises:
        Exception: If connection fails
    """
    client = get_openai_client()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": "Say 'Connection successful'"}],
        max_tokens=10,
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # Test the connection when run directly
    try:
        result = test_connection()
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")