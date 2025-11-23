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
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    
    if not endpoint or not api_key:
        raise ValueError("Missing required Azure OpenAI configuration")
    
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )

def generate_completion(
    prompt: str,
    system_message: str = "You are a marketing copywriter.",
    max_tokens: int = 400
) -> Dict[str, Any]:
    """
    Generate completion using Responses API.
    
    Args:
        prompt: Input prompt (system_message will be prepended)
        system_message: System message to prepend to prompt
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary with response data
    """
    client = get_openai_client()
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not deployment_name:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME not set")
    
    # Combine system message and prompt for Responses API
    full_prompt = f"{system_message}\n\n{prompt}"
    
    response = client.responses.create(
        model=deployment_name,
        input=full_prompt,
        max_output_tokens=max_tokens
    )
    
    # Extract text from Responses API format
    output_text = ""
    if hasattr(response, 'output_text'):
        output_text = response.output_text or ""
    elif hasattr(response, 'output') and response.output:
        # Handle structured output format
        if isinstance(response.output, list) and len(response.output) > 0:
            first_output = response.output[0]
            if hasattr(first_output, 'content') and first_output.content:
                if isinstance(first_output.content, list) and len(first_output.content) > 0:
                    text_content = first_output.content[0]
                    if hasattr(text_content, 'text') and hasattr(text_content.text, 'value'):
                        output_text = text_content.text.value or ""
    
    return {
        "text": output_text,
        "finish_reason": getattr(response, 'finish_reason', 'completed'),
        "tokens_used": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0,
        "input_tokens": getattr(response.usage, 'input_tokens', 0) if hasattr(response, 'usage') else 0,
        "output_tokens": getattr(response.usage, 'output_tokens', 0) if hasattr(response, 'usage') else 0
    }

def test_connection() -> str:
    """
    Test the Azure OpenAI connection.
    
    Returns:
        str: Success message if connection works
        
    Raises:
        Exception: If connection fails
    """
    result = generate_completion(
        prompt="Say 'Connection successful'",
        max_tokens=20  # Minimum 16 tokens required for Responses API
    )
    
    return result.get("text", "").strip()

if __name__ == "__main__":
    # Test the connection when run directly
    try:
        result = test_connection()
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")