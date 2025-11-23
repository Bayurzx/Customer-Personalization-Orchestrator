"""
Unit tests for Azure AI Content Safety integration.

Tests the ContentSafetyClient class and related functions with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from azure.core.exceptions import HttpResponseError, AzureError
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.integrations.azure_content_safety import (
    ContentSafetyClient,
    get_safety_client,
    analyze_text_safety,
    test_connection
)


class TestContentSafetyClient:
    """Test cases for ContentSafetyClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.mock_env = {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test-safety.cognitiveservices.azure.com/",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-api-key-12345"
        }
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    def test_client_initialization_success(self):
        """Test successful client initialization with environment variables."""
        client = ContentSafetyClient()
        assert client.endpoint == "https://test.com"
        assert client.api_key == "test-key"
        assert client._request_count == 0
        assert client._total_latency == 0.0
    
    def test_client_initialization_with_parameters(self):
        """Test client initialization with explicit parameters."""
        client = ContentSafetyClient(
            endpoint="https://custom.com",
            api_key="custom-key"
        )
        assert client.endpoint == "https://custom.com"
        assert client.api_key == "custom-key"
    
    def test_client_initialization_missing_config(self):
        """Test client initialization fails with missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure AI Content Safety configuration"):
                ContentSafetyClient()
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    @patch('azure.ai.contentsafety.ContentSafetyClient')
    def test_analyze_text_success(self, mock_azure_client):
        """Test successful text analysis."""
        # Mock the Azure client and response
        mock_response = Mock()
        mock_response.categories_analysis = [
            Mock(severity=0),  # hate
            Mock(severity=2),  # violence
            Mock(severity=0),  # self_harm
            Mock(severity=0)   # sexual
        ]
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.return_value = mock_response
        mock_azure_client.return_value = mock_client_instance
        
        # Test the analysis
        client = ContentSafetyClient()
        result = client.analyze_text("This is a test message")
        
        # Verify result structure
        assert "severity_scores" in result
        assert "status" in result
        assert "analyzed_at" in result
        assert "text_length" in result
        assert "max_severity" in result
        assert "blocked_categories" in result
        
        # Verify severity scores
        assert result["severity_scores"]["hate"] == 0
        assert result["severity_scores"]["violence"] == 2
        assert result["severity_scores"]["self_harm"] == 0
        assert result["severity_scores"]["sexual"] == 0
        assert result["max_severity"] == 2
        assert result["status"] == "pass"
        assert result["text_length"] == len("This is a test message")
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    @patch('azure.ai.contentsafety.ContentSafetyClient')
    def test_analyze_text_alternative_response_format(self, mock_azure_client):
        """Test text analysis with alternative response format."""
        # Mock response with individual result attributes
        mock_response = Mock()
        mock_response.categories_analysis = None
        mock_response.hate_result = Mock(severity=4)
        mock_response.violence_result = Mock(severity=0)
        mock_response.self_harm_result = Mock(severity=2)
        mock_response.sexual_result = Mock(severity=0)
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.return_value = mock_response
        mock_azure_client.return_value = mock_client_instance
        
        client = ContentSafetyClient()
        result = client.analyze_text("Test message")
        
        assert result["severity_scores"]["hate"] == 4
        assert result["severity_scores"]["violence"] == 0
        assert result["severity_scores"]["self_harm"] == 2
        assert result["severity_scores"]["sexual"] == 0
        assert result["max_severity"] == 4
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    def test_analyze_text_empty_input(self):
        """Test analysis with empty text input."""
        client = ContentSafetyClient()
        
        with pytest.raises(ValueError, match="Text content cannot be empty"):
            client.analyze_text("")
        
        with pytest.raises(ValueError, match="Text content cannot be empty"):
            client.analyze_text("   ")
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    @patch('azure.ai.contentsafety.ContentSafetyClient')
    def test_analyze_text_http_error_429(self, mock_azure_client):
        """Test handling of rate limit (429) errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = HttpResponseError(
            message="Rate limit exceeded",
            response=Mock(status_code=429)
        )
        mock_azure_client.return_value = mock_client_instance
        
        client = ContentSafetyClient()
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(HttpResponseError):
                client.analyze_text("Test message")
            # Verify sleep was called for rate limiting
            mock_sleep.assert_called_with(60)
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    @patch('azure.ai.contentsafety.ContentSafetyClient')
    def test_analyze_text_http_error_401(self, mock_azure_client):
        """Test handling of authentication (401) errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = HttpResponseError(
            message="Unauthorized",
            response=Mock(status_code=401)
        )
        mock_azure_client.return_value = mock_client_instance
        
        client = ContentSafetyClient()
        
        with pytest.raises(HttpResponseError):
            client.analyze_text("Test message")
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    @patch('azure.ai.contentsafety.ContentSafetyClient')
    def test_analyze_text_azure_error(self, mock_azure_client):
        """Test handling of general Azure errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = AzureError("Service unavailable")
        mock_azure_client.return_value = mock_client_instance
        
        client = ContentSafetyClient()
        
        with pytest.raises(AzureError):
            client.analyze_text("Test message")
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    def test_get_usage_stats(self):
        """Test usage statistics tracking."""
        client = ContentSafetyClient()
        
        # Initial stats
        stats = client.get_usage_stats()
        assert stats["total_requests"] == 0
        assert stats["total_latency_seconds"] == 0.0
        assert stats["average_latency_seconds"] == 0.0
        
        # Simulate some usage
        client._request_count = 5
        client._total_latency = 2.5
        
        stats = client.get_usage_stats()
        assert stats["total_requests"] == 5
        assert stats["total_latency_seconds"] == 2.5
        assert stats["average_latency_seconds"] == 0.5
        assert stats["requests_per_second"] == 2.0


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch.dict(os.environ, {"AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com", "AZURE_CONTENT_SAFETY_API_KEY": "test-key"})
    def test_get_safety_client(self):
        """Test get_safety_client convenience function."""
        client = get_safety_client()
        assert isinstance(client, ContentSafetyClient)
        assert client.endpoint == "https://test.com"
        assert client.api_key == "test-key"
    
    @patch('src.integrations.azure_content_safety.get_safety_client')
    def test_analyze_text_safety_convenience(self, mock_get_client):
        """Test analyze_text_safety convenience function."""
        mock_client = Mock()
        mock_client.analyze_text.return_value = {"status": "pass", "severity_scores": {"hate": 0}}
        mock_get_client.return_value = mock_client
        
        result = analyze_text_safety("Test message")
        
        mock_client.analyze_text.assert_called_once_with("Test message")
        assert result["status"] == "pass"
    
    @patch('src.integrations.azure_content_safety.ContentSafetyClient')
    def test_test_connection_success(self, mock_client_class):
        """Test successful connection test."""
        mock_client = Mock()
        mock_client.analyze_text.return_value = {
            "max_severity": 0,
            "status": "pass"
        }
        mock_client.get_usage_stats.return_value = {
            "average_latency_seconds": 0.123
        }
        mock_client_class.return_value = mock_client
        
        result = test_connection()
        
        assert "Connection successful" in result
        assert "0.123s" in result
        assert "Max severity: 0" in result
    
    @patch('src.integrations.azure_content_safety.ContentSafetyClient')
    def test_test_connection_failure(self, mock_client_class):
        """Test connection test failure."""
        mock_client_class.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            test_connection()


if __name__ == "__main__":
    pytest.main([__file__])