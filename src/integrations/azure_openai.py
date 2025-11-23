"""
Azure OpenAI Integration Module

This module provides a wrapper around the Azure OpenAI API for the Customer Personalization Orchestrator.
It handles authentication, retry logic, response parsing, token counting, and cost tracking.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    """
    Azure OpenAI client with retry logic, timeout handling, and cost tracking.
    
    This class provides a robust wrapper around the Azure OpenAI API with:
    - Automatic retry logic for transient failures
    - Timeout handling (10 seconds default)
    - Token usage and cost tracking
    - Structured error handling
    """
    
    def __init__(self, timeout: float = 10.0):
        """
        Initialize the Azure OpenAI client.
        
        Args:
            timeout: Request timeout in seconds (default: 10.0)
            
        Raises:
            ValueError: If required environment variables are missing
        """
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.timeout = timeout
        
        # Validate required configuration
        if not self.endpoint or not self.api_key or not self.deployment_name:
            raise ValueError(
                "Missing required Azure OpenAI configuration. "
                "Please set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME"
            )
        
        # Initialize client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            timeout=self.timeout
        )
        
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        
        logger.info(f"Initialized Azure OpenAI client with deployment: {self.deployment_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
        reraise=True
    )
    def generate_completion(
        self,
        prompt: str,
        system_message: str = "You are a marketing copywriter.",
        max_tokens: int = 400
    ) -> Dict[str, Any]:
        """
        Generate completion using Responses API with retry logic.
        
        Args:
            prompt: Input prompt (system_message will be prepended)
            system_message: System message to prepend to prompt
            max_tokens: Maximum tokens to generate (minimum 16 for Responses API)
            
        Returns:
            Dictionary with response data including text, tokens, and cost
            
        Raises:
            ValueError: If max_tokens is less than 16
            Exception: If API call fails after retries
        """
        if max_tokens < 16:
            raise ValueError("max_tokens must be at least 16 for Responses API")
        
        # Combine system message and prompt for Responses API
        full_prompt = f"{system_message}\n\n{prompt}"
        
        start_time = time.time()
        
        try:
            logger.debug(f"Generating completion with {max_tokens} max tokens")
            
            response = self.client.responses.create(
                model=self.deployment_name,
                input=full_prompt,
                max_output_tokens=max_tokens
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            result = self._parse_response(response)
            
            # Track usage
            self._track_usage(result)
            
            # Add metadata
            result.update({
                "duration_ms": duration_ms,
                "model": self.deployment_name,
                "cost_usd": self.calculate_cost(result["input_tokens"], result["output_tokens"])
            })
            
            logger.info(
                f"Generated completion: {result['output_tokens']} tokens, "
                f"{duration_ms}ms, ${result['cost_usd']:.4f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse Azure OpenAI Responses API response.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed response dictionary
        """
        # Extract text from Responses API format
        output_text = ""
        if hasattr(response, 'output_text') and response.output_text:
            output_text = response.output_text
        elif hasattr(response, 'output') and response.output:
            # Handle structured output format
            if isinstance(response.output, list) and len(response.output) > 0:
                first_output = response.output[0]
                if hasattr(first_output, 'content') and first_output.content:
                    if isinstance(first_output.content, list) and len(first_output.content) > 0:
                        text_content = first_output.content[0]
                        if hasattr(text_content, 'text') and hasattr(text_content.text, 'value'):
                            output_text = text_content.text.value or ""
        
        # Extract token usage
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        if hasattr(response, 'usage'):
            input_tokens = getattr(response.usage, 'input_tokens', 0)
            output_tokens = getattr(response.usage, 'output_tokens', 0)
            total_tokens = getattr(response.usage, 'total_tokens', 0)
        
        return {
            "text": output_text,
            "finish_reason": getattr(response, 'finish_reason', 'completed'),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tokens_used": total_tokens  # For backward compatibility
        }
    
    def _track_usage(self, result: Dict[str, Any]) -> None:
        """
        Track token usage for cost calculation.
        
        Args:
            result: Parsed response with token counts
        """
        self.total_input_tokens += result.get("input_tokens", 0)
        self.total_output_tokens += result.get("output_tokens", 0)
        self.total_requests += 1
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
        """
        Calculate cost based on token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name for pricing lookup
            
        Returns:
            Cost in USD
        """
        # Pricing per 1K tokens (as of November 2025)
        PRICING = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/$0.60 per 1M
            "gpt-4o": {"input": 0.005, "output": 0.015},  # $5/$15 per 1M
            "gpt-4": {"input": 0.03, "output": 0.06}  # $30/$60 per 1M
        }
        
        price = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost_input = (input_tokens / 1000) * price["input"]
        cost_output = (output_tokens / 1000) * price["output"]
        return cost_input + cost_output
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get summary of token usage and costs.
        
        Returns:
            Dictionary with usage statistics
        """
        total_cost = self.calculate_cost(self.total_input_tokens, self.total_output_tokens)
        
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_tokens_per_request": (
                (self.total_input_tokens + self.total_output_tokens) / max(1, self.total_requests)
            )
        }
    
    def test_connection(self) -> str:
        """
        Test the Azure OpenAI connection.
        
        Returns:
            Success message if connection works
            
        Raises:
            Exception: If connection fails
        """
        result = self.generate_completion(
            prompt="Say 'Connection successful'",
            max_tokens=20  # Minimum 16 tokens required for Responses API
        )
        
        return result.get("text", "").strip()


def get_openai_client() -> AzureOpenAI:
    """
    Create and return a basic Azure OpenAI client (legacy function).
    
    Returns:
        AzureOpenAI: Configured client instance
        
    Raises:
        ValueError: If required environment variables are missing
        
    Note:
        This function is kept for backward compatibility.
        Use AzureOpenAIClient class for new code.
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
    Generate completion using Responses API (legacy function).
    
    Args:
        prompt: Input prompt (system_message will be prepended)
        system_message: System message to prepend to prompt
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary with response data
        
    Note:
        This function maintains backward compatibility with existing code.
        For new code, use AzureOpenAIClient class which provides retry logic and better error handling.
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
    if hasattr(response, 'output_text') and response.output_text:
        output_text = response.output_text
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
    Test the Azure OpenAI connection (legacy function).
    
    Returns:
        str: Success message if connection works
        
    Raises:
        Exception: If connection fails
        
    Note:
        This function maintains backward compatibility with existing code.
        For new code, use AzureOpenAIClient.test_connection() for better error handling.
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