"""
Unit tests for Azure OpenAI integration.

Tests the AzureOpenAIClient class with mocked responses to verify:
- Client initialization and configuration
- Response parsing and token tracking
- Retry logic and error handling
- Cost calculation and usage tracking
- Timeout handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from src.integrations.azure_openai import AzureOpenAIClient, get_openai_client, generate_completion
from src.integrations.azure_openai import test_connection as azure_test_connection


class TestAzureOpenAIClient:
    """Test cases for AzureOpenAIClient class."""

    def setup_method(self):
        """Set up test environment variables."""
        self.env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_API_VERSION": "2025-04-01-preview",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o-mini",
        }

        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()

    def teardown_method(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    def test_client_initialization_success(self):
        """Test successful client initialization with valid config."""
        with patch("src.integrations.azure_openai.AzureOpenAI") as mock_azure_openai:
            client = AzureOpenAIClient(timeout=15.0)

            assert client.endpoint == "https://test.openai.azure.com/"
            assert client.api_key == "test-api-key"
            assert client.deployment_name == "gpt-4o-mini"
            assert client.timeout == 15.0
            assert client.total_requests == 0
            assert client.total_input_tokens == 0
            assert client.total_output_tokens == 0

            # Verify AzureOpenAI was called with correct parameters
            mock_azure_openai.assert_called_once_with(
                azure_endpoint="https://test.openai.azure.com/",
                api_key="test-api-key",
                api_version="2025-04-01-preview",
                timeout=15.0,
            )

    def test_client_initialization_missing_config(self):
        """Test client initialization fails with missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure OpenAI configuration"):
                AzureOpenAIClient()

    def test_client_initialization_partial_config(self):
        """Test client initialization fails with partial configuration."""
        partial_env = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-key",
            # Missing AZURE_OPENAI_DEPLOYMENT_NAME
        }

        with patch.dict(os.environ, partial_env, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure OpenAI configuration"):
                AzureOpenAIClient()

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_generate_completion_success(self, mock_azure_openai):
        """Test successful completion generation."""
        # Mock response
        mock_response = Mock()
        mock_response.output_text = "Generated marketing message"
        mock_response.finish_reason = "completed"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 25
        mock_response.usage.total_tokens = 75

        # Mock client
        mock_client_instance = Mock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()

        result = client.generate_completion(
            prompt="Write a marketing message",
            system_message="You are a copywriter",
            max_tokens=100,
        )

        # Verify result
        assert result["text"] == "Generated marketing message"
        assert result["finish_reason"] == "completed"
        assert result["input_tokens"] == 50
        assert result["output_tokens"] == 25
        assert result["tokens_used"] == 75
        assert result["model"] == "gpt-4o-mini"
        assert "cost_usd" in result
        assert "duration_ms" in result

        # Verify API call
        mock_client_instance.responses.create.assert_called_once_with(
            model="gpt-4o-mini",
            input="You are a copywriter\n\nWrite a marketing message",
            max_output_tokens=100,
        )

        # Verify usage tracking
        assert client.total_requests == 1
        assert client.total_input_tokens == 50
        assert client.total_output_tokens == 25

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_generate_completion_structured_response(self, mock_azure_openai):
        """Test parsing of structured response format."""
        # Mock structured response
        mock_text_content = Mock()
        mock_text_content.text = Mock()
        mock_text_content.text.value = "Structured response text"

        mock_content = Mock()
        mock_content.content = [mock_text_content]

        mock_response = Mock()
        mock_response.output_text = None  # No direct output_text
        mock_response.output = [mock_content]
        mock_response.finish_reason = "completed"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 30
        mock_response.usage.output_tokens = 20
        mock_response.usage.total_tokens = 50

        mock_client_instance = Mock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()
        result = client.generate_completion("Test prompt")

        assert result["text"] == "Structured response text"
        assert result["input_tokens"] == 30
        assert result["output_tokens"] == 20

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_generate_completion_min_tokens_validation(self, mock_azure_openai):
        """Test validation of minimum token requirement."""
        client = AzureOpenAIClient()

        with pytest.raises(ValueError, match="max_tokens must be at least 16"):
            client.generate_completion("Test", max_tokens=10)

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_generate_completion_retry_logic(self, mock_azure_openai):
        """Test retry logic on API failures."""
        # Mock client that fails twice then succeeds
        mock_client_instance = Mock()
        mock_client_instance.responses.create.side_effect = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timeout"),
            Mock(
                output_text="Success",
                finish_reason="completed",
                usage=Mock(input_tokens=10, output_tokens=5, total_tokens=15),
            ),
        ]
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()

        # Should succeed after retries
        result = client.generate_completion("Test prompt", max_tokens=20)

        assert result["text"] == "Success"
        assert mock_client_instance.responses.create.call_count == 3

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_generate_completion_retry_exhausted(self, mock_azure_openai):
        """Test behavior when retry attempts are exhausted."""
        # Mock client that always fails
        mock_client_instance = Mock()
        mock_client_instance.responses.create.side_effect = ConnectionError("Persistent failure")
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()

        # Should raise exception after max retries
        with pytest.raises(ConnectionError, match="Persistent failure"):
            client.generate_completion("Test prompt", max_tokens=20)

        # Should have attempted 3 times (original + 2 retries)
        assert mock_client_instance.responses.create.call_count == 3

    def test_calculate_cost_gpt4o_mini(self):
        """Test cost calculation for gpt-4o-mini model."""
        with patch("src.integrations.azure_openai.AzureOpenAI"):
            client = AzureOpenAIClient()

            # Test with 1000 input tokens, 500 output tokens
            cost = client.calculate_cost(1000, 500, "gpt-4o-mini")

            # Expected: (1000/1000 * 0.00015) + (500/1000 * 0.0006) = 0.00015 + 0.0003 = 0.00045
            assert abs(cost - 0.00045) < 0.000001

    def test_calculate_cost_gpt4o(self):
        """Test cost calculation for gpt-4o model."""
        with patch("src.integrations.azure_openai.AzureOpenAI"):
            client = AzureOpenAIClient()

            # Test with 1000 input tokens, 500 output tokens
            cost = client.calculate_cost(1000, 500, "gpt-4o")

            # Expected: (1000/1000 * 0.005) + (500/1000 * 0.015) = 0.005 + 0.0075 = 0.0125
            assert abs(cost - 0.0125) < 0.000001

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation defaults to gpt-4o-mini for unknown models."""
        with patch("src.integrations.azure_openai.AzureOpenAI"):
            client = AzureOpenAIClient()

            cost_unknown = client.calculate_cost(1000, 500, "unknown-model")
            cost_mini = client.calculate_cost(1000, 500, "gpt-4o-mini")

            assert cost_unknown == cost_mini

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_usage_summary(self, mock_azure_openai):
        """Test usage summary calculation."""
        client = AzureOpenAIClient()

        # Simulate some usage
        client.total_requests = 3
        client.total_input_tokens = 150
        client.total_output_tokens = 75

        summary = client.get_usage_summary()

        assert summary["total_requests"] == 3
        assert summary["total_tokens"] == 225
        assert summary["input_tokens"] == 150
        assert summary["output_tokens"] == 75
        assert summary["avg_tokens_per_request"] == 75.0
        assert "total_cost_usd" in summary
        assert summary["total_cost_usd"] > 0

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_test_connection_success(self, mock_azure_openai):
        """Test successful connection test."""
        # Mock successful response
        mock_response = Mock()
        mock_response.output_text = "Connection successful"
        mock_response.finish_reason = "completed"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client_instance = Mock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()
        result = client.test_connection()

        assert result == "Connection successful"

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_test_connection_failure(self, mock_azure_openai):
        """Test connection test failure."""
        mock_client_instance = Mock()
        mock_client_instance.responses.create.side_effect = ConnectionError("Connection failed")
        mock_azure_openai.return_value = mock_client_instance

        client = AzureOpenAIClient()

        with pytest.raises(ConnectionError, match="Connection failed"):
            client.test_connection()


class TestLegacyFunctions:
    """Test cases for legacy functions."""

    def setup_method(self):
        """Set up test environment variables."""
        self.env_vars = {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_API_VERSION": "2025-04-01-preview",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o-mini",
        }

        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()

    def teardown_method(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch("src.integrations.azure_openai.AzureOpenAI")
    def test_get_openai_client_success(self, mock_azure_openai):
        """Test legacy get_openai_client function."""
        client = get_openai_client()

        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com/",
            api_key="test-api-key",
            api_version="2025-04-01-preview",
        )

    def test_get_openai_client_missing_config(self):
        """Test legacy function fails with missing config."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure OpenAI configuration"):
                get_openai_client()

    @patch("src.integrations.azure_openai.get_openai_client")
    def test_generate_completion_legacy(self, mock_get_client):
        """Test legacy generate_completion function."""
        # Mock the Azure OpenAI client and response
        mock_response = Mock()
        mock_response.output_text = "test response"
        mock_response.finish_reason = "completed"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client = Mock()
        mock_client.responses.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = generate_completion("test prompt", "system message", 100)

        mock_get_client.assert_called_once()
        mock_client.responses.create.assert_called_once_with(
            model="gpt-4o-mini", input="system message\n\ntest prompt", max_output_tokens=100
        )
        assert result["text"] == "test response"
        assert result["tokens_used"] == 15

    @patch("src.integrations.azure_openai.generate_completion")
    def test_test_connection_legacy(self, mock_generate):
        """Test legacy test_connection function."""
        mock_generate.return_value = {"text": "Connection successful"}

        result = azure_test_connection()

        mock_generate.assert_called_once_with(prompt="Say 'Connection successful'", max_tokens=20)
        assert result == "Connection successful"


if __name__ == "__main__":
    pytest.main([__file__])
