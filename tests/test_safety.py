"""
Unit tests for Azure AI Content Safety integration.

Tests the ContentSafetyClient class and related functions with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from azure.core.exceptions import HttpResponseError, AzureError
import os
import sys
import tempfile
import yaml
import csv

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.integrations.azure_content_safety import (
    ContentSafetyClient,
    get_safety_client,
    analyze_text_safety,
    test_connection,
)

# Import SafetyAgent for testing
from src.agents.safety_agent import (
    SafetyAgent,
    check_safety,
    apply_policy_threshold,
    generate_audit_report,
)


class TestContentSafetyClient:
    """Test cases for ContentSafetyClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.mock_env = {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test-safety.cognitiveservices.azure.com/",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-api-key-12345",
        }

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    def test_client_initialization_success(self):
        """Test successful client initialization with environment variables."""
        client = ContentSafetyClient()
        assert client.endpoint == "https://test.com"
        assert client.api_key == "test-key"
        assert client._request_count == 0
        assert client._total_latency == 0.0

    def test_client_initialization_with_parameters(self):
        """Test client initialization with explicit parameters."""
        client = ContentSafetyClient(endpoint="https://custom.com", api_key="custom-key")
        assert client.endpoint == "https://custom.com"
        assert client.api_key == "custom-key"

    def test_client_initialization_missing_config(self):
        """Test client initialization fails with missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Missing required Azure AI Content Safety configuration"
            ):
                ContentSafetyClient()

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    @patch("azure.ai.contentsafety.ContentSafetyClient")
    def test_analyze_text_success(self, mock_azure_client):
        """Test successful text analysis."""
        # Mock the Azure client and response
        mock_response = Mock()
        mock_response.categories_analysis = [
            Mock(severity=0),  # hate
            Mock(severity=2),  # violence
            Mock(severity=0),  # self_harm
            Mock(severity=0),  # sexual
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

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    @patch("azure.ai.contentsafety.ContentSafetyClient")
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

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    def test_analyze_text_empty_input(self):
        """Test analysis with empty text input."""
        client = ContentSafetyClient()

        with pytest.raises(ValueError, match="Text content cannot be empty"):
            client.analyze_text("")

        with pytest.raises(ValueError, match="Text content cannot be empty"):
            client.analyze_text("   ")

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    @patch("azure.ai.contentsafety.ContentSafetyClient")
    def test_analyze_text_http_error_429(self, mock_azure_client):
        """Test handling of rate limit (429) errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = HttpResponseError(
            message="Rate limit exceeded", response=Mock(status_code=429)
        )
        mock_azure_client.return_value = mock_client_instance

        client = ContentSafetyClient()

        with patch("time.sleep") as mock_sleep:
            with pytest.raises(HttpResponseError):
                client.analyze_text("Test message")
            # Verify sleep was called for rate limiting
            mock_sleep.assert_called_with(60)

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    @patch("azure.ai.contentsafety.ContentSafetyClient")
    def test_analyze_text_http_error_401(self, mock_azure_client):
        """Test handling of authentication (401) errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = HttpResponseError(
            message="Unauthorized", response=Mock(status_code=401)
        )
        mock_azure_client.return_value = mock_client_instance

        client = ContentSafetyClient()

        with pytest.raises(HttpResponseError):
            client.analyze_text("Test message")

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    @patch("azure.ai.contentsafety.ContentSafetyClient")
    def test_analyze_text_azure_error(self, mock_azure_client):
        """Test handling of general Azure errors."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_text.side_effect = AzureError("Service unavailable")
        mock_azure_client.return_value = mock_client_instance

        client = ContentSafetyClient()

        with pytest.raises(AzureError):
            client.analyze_text("Test message")

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
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

    @patch.dict(
        os.environ,
        {
            "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test.com",
            "AZURE_CONTENT_SAFETY_API_KEY": "test-key",
        },
    )
    def test_get_safety_client(self):
        """Test get_safety_client convenience function."""
        client = get_safety_client()
        assert isinstance(client, ContentSafetyClient)
        assert client.endpoint == "https://test.com"
        assert client.api_key == "test-key"

    @patch("src.integrations.azure_content_safety.get_safety_client")
    def test_analyze_text_safety_convenience(self, mock_get_client):
        """Test analyze_text_safety convenience function."""
        mock_client = Mock()
        mock_client.analyze_text.return_value = {"status": "pass", "severity_scores": {"hate": 0}}
        mock_get_client.return_value = mock_client

        result = analyze_text_safety("Test message")

        mock_client.analyze_text.assert_called_once_with("Test message")
        assert result["status"] == "pass"

    @patch("src.integrations.azure_content_safety.ContentSafetyClient")
    def test_test_connection_success(self, mock_client_class):
        """Test successful connection test."""
        mock_client = Mock()
        mock_client.analyze_text.return_value = {"max_severity": 0, "status": "pass"}
        mock_client.get_usage_stats.return_value = {"average_latency_seconds": 0.123}
        mock_client_class.return_value = mock_client

        result = test_connection()

        assert "Connection successful" in result
        assert "0.123s" in result
        assert "Max severity: 0" in result

    @patch("src.integrations.azure_content_safety.ContentSafetyClient")
    def test_test_connection_failure(self, mock_client_class):
        """Test connection test failure."""
        mock_client_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            test_connection()


class TestSafetyAgent:
    """Test cases for SafetyAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        config_data = {
            "safety_policy": {
                "threshold": 4,
                "categories": ["hate", "violence", "self_harm", "sexual"],
                "audit_logging": {"enabled": True, "format": "csv"},
            }
        }
        yaml.dump(config_data, self.temp_config)
        self.temp_config.close()

        # Create temporary audit log file
        self.temp_audit_log = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
        self.temp_audit_log.close()

        # Mock safety client
        self.mock_safety_client = Mock()

    def teardown_method(self):
        """Clean up test fixtures."""
        import os

        try:
            os.unlink(self.temp_config.name)
            os.unlink(self.temp_audit_log.name)
        except:
            pass

    def test_safety_agent_initialization_success(self):
        """Test successful SafetyAgent initialization."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        assert agent.safety_client == self.mock_safety_client
        assert agent.threshold == 4
        assert agent.total_checks == 0
        assert agent.total_passed == 0
        assert agent.total_blocked == 0

    def test_safety_agent_initialization_missing_config(self):
        """Test SafetyAgent initialization with missing config file."""
        with pytest.raises(FileNotFoundError):
            SafetyAgent(
                safety_client=self.mock_safety_client,
                config_path="nonexistent_config.yaml",
                audit_log_path=self.temp_audit_log.name,
            )

    def test_check_safety_pass(self):
        """Test safety check that passes."""
        # Mock safety client response
        self.mock_safety_client.analyze_text.return_value = {
            "severity_scores": {"hate": 0, "violence": 2, "self_harm": 0, "sexual": 0},
            "max_severity": 2,
            "status": "pass",
        }

        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        variant = {
            "variant_id": "TEST001",
            "customer_id": "C001",
            "segment": "Test",
            "body": "This is a safe test message.",
        }

        result = agent.check_safety(variant)

        assert result["status"] == "pass"
        assert result["variant_id"] == "TEST001"
        assert result["hate_severity"] == 0
        assert result["violence_severity"] == 2
        assert result["max_severity"] == 2
        assert result["blocked_categories"] == []
        assert result["block_reason"] is None
        assert agent.total_checks == 1
        assert agent.total_passed == 1
        assert agent.total_blocked == 0

    def test_check_safety_block(self):
        """Test safety check that blocks content."""
        # Mock safety client response with high severity
        self.mock_safety_client.analyze_text.return_value = {
            "severity_scores": {"hate": 6, "violence": 0, "self_harm": 0, "sexual": 0},
            "max_severity": 6,
            "status": "pass",
        }

        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        variant = {
            "variant_id": "TEST002",
            "customer_id": "C002",
            "segment": "Test",
            "body": "This message contains inappropriate content.",
        }

        result = agent.check_safety(variant)

        assert result["status"] == "block"
        assert result["variant_id"] == "TEST002"
        assert result["hate_severity"] == 6
        assert result["max_severity"] == 6
        assert "hate" in result["blocked_categories"]
        assert result["block_reason"] is not None
        assert agent.total_checks == 1
        assert agent.total_passed == 0
        assert agent.total_blocked == 1
        assert agent.blocked_by_category["hate"] == 1

    def test_check_safety_api_error(self):
        """Test safety check with API error (fail closed)."""
        # Mock safety client to raise exception
        self.mock_safety_client.analyze_text.side_effect = Exception("API Error")

        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        variant = {"variant_id": "TEST003", "body": "Test message"}

        result = agent.check_safety(variant)

        assert result["status"] == "block"
        assert result["variant_id"] == "TEST003"
        assert "api_error" in result["blocked_categories"]
        assert "API Error" in result["block_reason"]
        assert agent.total_checks == 1
        assert agent.total_blocked == 1

    def test_check_safety_invalid_input(self):
        """Test safety check with invalid input."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        # Test missing variant_id
        with pytest.raises(ValueError, match="Variant must contain 'variant_id'"):
            agent.check_safety({"body": "test"})

        # Test missing body
        with pytest.raises(ValueError, match="Variant must contain non-empty 'body'"):
            agent.check_safety({"variant_id": "TEST001"})

        # Test empty body
        with pytest.raises(ValueError, match="Variant must contain non-empty 'body'"):
            agent.check_safety({"variant_id": "TEST001", "body": ""})

        # Test non-dict input
        with pytest.raises(ValueError, match="Variant must be a dictionary"):
            agent.check_safety("not a dict")

    def test_apply_policy_threshold_pass(self):
        """Test policy threshold application that passes."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        severity_scores = {"hate": 2, "violence": 0, "self_harm": 4, "sexual": 0}

        result = agent.apply_policy_threshold(severity_scores, threshold=4)

        assert result["status"] == "pass"
        assert result["blocked_categories"] == []
        assert result["block_reason"] is None

    def test_apply_policy_threshold_block(self):
        """Test policy threshold application that blocks."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        severity_scores = {"hate": 6, "violence": 0, "self_harm": 4, "sexual": 6}

        result = agent.apply_policy_threshold(severity_scores, threshold=4)

        assert result["status"] == "block"
        assert "hate" in result["blocked_categories"]
        assert "sexual" in result["blocked_categories"]
        assert "self_harm" not in result["blocked_categories"]  # Equal to threshold, not greater
        assert result["block_reason"] is not None

    def test_generate_audit_report_empty_log(self):
        """Test audit report generation with empty log."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        report = agent.generate_audit_report()

        assert report["total_checks"] == 0
        assert report["passed_checks"] == 0
        assert report["blocked_checks"] == 0
        assert report["pass_rate_percent"] == 0.0
        assert report["threshold_used"] == 4
        assert "generated_at" in report

    def test_generate_audit_report_with_data(self):
        """Test audit report generation with sample data."""
        # Create sample audit log data
        with open(self.temp_audit_log.name, "w", newline="") as f:
            writer = csv.writer(f)
            # Write headers
            writer.writerow(
                [
                    "timestamp",
                    "variant_id",
                    "customer_id",
                    "segment",
                    "status",
                    "hate_severity",
                    "violence_severity",
                    "self_harm_severity",
                    "sexual_severity",
                    "max_severity",
                    "threshold_used",
                    "blocked_categories",
                    "block_reason",
                ]
            )
            # Write sample data
            writer.writerow(
                ["2025-11-23T10:00:00", "VAR001", "C001", "Test", "pass", 0, 2, 0, 0, 2, 4, "", ""]
            )
            writer.writerow(
                [
                    "2025-11-23T10:01:00",
                    "VAR002",
                    "C002",
                    "Test",
                    "block",
                    6,
                    0,
                    0,
                    0,
                    6,
                    4,
                    "hate",
                    "Hate severity above threshold",
                ]
            )

        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        report = agent.generate_audit_report()

        assert report["total_checks"] == 2
        assert report["passed_checks"] == 1
        assert report["blocked_checks"] == 1
        assert report["pass_rate_percent"] == 50.0
        assert report["block_rate_percent"] == 50.0
        assert report["category_blocks"]["hate"] == 1
        assert report["severity_distribution"]["low_2"] == 1
        assert report["severity_distribution"]["high_6"] == 1

    def test_get_statistics(self):
        """Test statistics retrieval."""
        agent = SafetyAgent(
            safety_client=self.mock_safety_client,
            config_path=self.temp_config.name,
            audit_log_path=self.temp_audit_log.name,
        )

        # Simulate some activity
        agent.total_checks = 10
        agent.total_passed = 8
        agent.total_blocked = 2
        agent.blocked_by_category["hate"] = 1
        agent.blocked_by_category["violence"] = 1

        stats = agent.get_statistics()

        assert stats["total_checks"] == 10
        assert stats["total_passed"] == 8
        assert stats["total_blocked"] == 2
        assert stats["pass_rate_percent"] == 80.0
        assert stats["block_rate_percent"] == 20.0
        assert stats["blocked_by_category"]["hate"] == 1
        assert stats["blocked_by_category"]["violence"] == 1
        assert stats["threshold_used"] == 4


class TestSafetyAgentConvenienceFunctions:
    """Test cases for SafetyAgent convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        config_data = {
            "safety_policy": {
                "threshold": 4,
                "categories": ["hate", "violence", "self_harm", "sexual"],
            }
        }
        yaml.dump(config_data, self.temp_config)
        self.temp_config.close()

    def teardown_method(self):
        """Clean up test fixtures."""
        import os

        try:
            os.unlink(self.temp_config.name)
        except:
            pass

    @patch("src.agents.safety_agent.get_safety_client")
    def test_check_safety_convenience_function(self, mock_get_client):
        """Test check_safety convenience function."""
        mock_client = Mock()
        mock_client.analyze_text.return_value = {
            "severity_scores": {"hate": 0, "violence": 0, "self_harm": 0, "sexual": 0},
            "max_severity": 0,
        }
        mock_get_client.return_value = mock_client

        variant = {"variant_id": "TEST001", "body": "Safe test message"}

        with patch("src.agents.safety_agent.SafetyAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.check_safety.return_value = {"status": "pass"}
            mock_agent_class.return_value = mock_agent

            result = check_safety(variant, config_path=self.temp_config.name)

            mock_agent_class.assert_called_once_with(config_path=self.temp_config.name)
            mock_agent.check_safety.assert_called_once_with(variant)
            assert result["status"] == "pass"

    def test_apply_policy_threshold_convenience_function(self):
        """Test apply_policy_threshold convenience function."""
        severity_scores = {"hate": 2, "violence": 6, "self_harm": 0, "sexual": 0}

        with patch("src.agents.safety_agent.SafetyAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.apply_policy_threshold.return_value = {
                "status": "block",
                "blocked_categories": ["violence"],
            }
            mock_agent_class.return_value = mock_agent

            result = apply_policy_threshold(severity_scores, threshold=4)

            mock_agent.apply_policy_threshold.assert_called_once_with(severity_scores, 4)
            assert result["status"] == "block"

    def test_generate_audit_report_convenience_function(self):
        """Test generate_audit_report convenience function."""
        audit_log_path = "test_audit.log"

        with patch("src.agents.safety_agent.SafetyAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.generate_audit_report.return_value = {
                "total_checks": 5,
                "pass_rate_percent": 80.0,
            }
            mock_agent_class.return_value = mock_agent

            result = generate_audit_report(audit_log_path=audit_log_path)

            mock_agent_class.assert_called_once_with(audit_log_path=audit_log_path)
            mock_agent.generate_audit_report.assert_called_once()
            assert result["total_checks"] == 5


if __name__ == "__main__":
    pytest.main([__file__])
