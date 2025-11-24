"""
Azure AI Content Safety Integration Module

This module provides a wrapper around the Azure AI Content Safety API for the Customer Personalization Orchestrator.
It handles content analysis and safety policy enforcement with retry logic and comprehensive error handling.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.exceptions import AzureError, HttpResponseError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class ContentSafetyClient:
    """
    Azure AI Content Safety client with retry logic and comprehensive error handling.

    This class provides a robust interface to Azure AI Content Safety API with:
    - Automatic retry logic for transient failures
    - Comprehensive error handling
    - Structured response parsing
    - Performance tracking
    """

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the Content Safety client.

        Args:
            endpoint: Azure Content Safety endpoint (defaults to env var)
            api_key: API key (defaults to env var)

        Raises:
            ValueError: If required configuration is missing
        """
        self.endpoint = endpoint or os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_CONTENT_SAFETY_API_KEY")

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Missing required Azure AI Content Safety configuration. "
                "Set AZURE_CONTENT_SAFETY_ENDPOINT and AZURE_CONTENT_SAFETY_API_KEY environment variables."
            )

        self._client = None
        self._request_count = 0
        self._total_latency = 0.0

    @property
    def client(self):
        """Get or create the Azure Content Safety client."""
        if self._client is None:
            # Import the actual Azure client to avoid naming conflict
            from azure.ai.contentsafety import ContentSafetyClient as AzureContentSafetyClient

            self._client = AzureContentSafetyClient(
                endpoint=self.endpoint, credential=AzureKeyCredential(self.api_key)
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for safety violations with retry logic.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing safety analysis results with severity scores

        Raises:
            AzureError: If API call fails after retries
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        start_time = time.time()

        try:
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)

            # Track performance
            latency = time.time() - start_time
            self._request_count += 1
            self._total_latency += latency

            # Parse response
            result = self._parse_safety_response(response, text)

            logger.debug(
                f"Safety analysis completed in {latency:.3f}s. "
                f"Status: {result['status']}, Categories: {result['severity_scores']}"
            )

            return result

        except HttpResponseError as e:
            if e.status_code == 429:
                logger.warning(f"Rate limit hit: {e}")
                time.sleep(60)  # Wait before retry
                raise
            elif e.status_code == 401:
                logger.error("Authentication failed - check API key")
                raise
            else:
                logger.error(f"HTTP error {e.status_code}: {e.message}")
                raise
        except AzureError as e:
            logger.error(f"Azure service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during safety analysis: {e}")
            raise

    def _parse_safety_response(self, response, original_text: str) -> Dict[str, Any]:
        """
        Parse Azure Content Safety API response into standardized format.

        Args:
            response: Raw API response
            original_text: Original text that was analyzed

        Returns:
            Standardized safety analysis result
        """
        # Initialize result structure
        result = {
            "text_length": len(original_text),
            "analyzed_at": datetime.utcnow().isoformat(),
            "severity_scores": {"hate": 0, "violence": 0, "self_harm": 0, "sexual": 0},
            "status": "pass",
            "blocked_categories": [],
            "max_severity": 0,
        }

        # Parse categories analysis
        if hasattr(response, "categories_analysis") and response.categories_analysis:
            categories = response.categories_analysis
            category_names = ["hate", "violence", "self_harm", "sexual"]

            for i, category in enumerate(categories):
                if i < len(category_names):
                    category_name = category_names[i]
                    severity = getattr(category, "severity", 0)
                    result["severity_scores"][category_name] = severity

                    # Track maximum severity
                    if severity > result["max_severity"]:
                        result["max_severity"] = severity

        # Alternative parsing for different response formats
        elif hasattr(response, "hate_result"):
            result["severity_scores"]["hate"] = getattr(response.hate_result, "severity", 0)
            result["severity_scores"]["violence"] = (
                getattr(response.violence_result, "severity", 0)
                if hasattr(response, "violence_result")
                else 0
            )
            result["severity_scores"]["self_harm"] = (
                getattr(response.self_harm_result, "severity", 0)
                if hasattr(response, "self_harm_result")
                else 0
            )
            result["severity_scores"]["sexual"] = (
                getattr(response.sexual_result, "severity", 0)
                if hasattr(response, "sexual_result")
                else 0
            )

            result["max_severity"] = max(result["severity_scores"].values())

        return result

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this client instance.

        Returns:
            Dict containing usage metrics
        """
        avg_latency = self._total_latency / max(1, self._request_count)

        return {
            "total_requests": self._request_count,
            "total_latency_seconds": round(self._total_latency, 3),
            "average_latency_seconds": round(avg_latency, 3),
            "requests_per_second": round(self._request_count / max(1, self._total_latency), 2),
        }


# Convenience functions for backward compatibility
def get_safety_client() -> ContentSafetyClient:
    """
    Create and return an Azure AI Content Safety client.

    Returns:
        ContentSafetyClient: Configured client instance

    Raises:
        ValueError: If required environment variables are missing
    """
    return ContentSafetyClient()


def analyze_text_safety(text: str) -> Dict[str, Any]:
    """
    Analyze text for safety violations (convenience function).

    Args:
        text: Text content to analyze

    Returns:
        Dict containing safety analysis results

    Raises:
        Exception: If API call fails
    """
    client = get_safety_client()
    return client.analyze_text(text)


def test_connection() -> str:
    """
    Test the Azure AI Content Safety connection.

    Returns:
        str: Success message if connection works

    Raises:
        Exception: If connection fails
    """
    client = ContentSafetyClient()
    result = client.analyze_text("This is a safe test message for connection testing.")

    stats = client.get_usage_stats()
    return (
        f"Connection successful. Analysis completed in {stats['average_latency_seconds']:.3f}s. "
        f"Max severity: {result['max_severity']}"
    )


if __name__ == "__main__":
    # Test the connection when run directly
    try:
        result = test_connection()
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
