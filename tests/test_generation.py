"""
Unit tests for the Generation Agent.

This module tests the message generation functionality including
variant generation, citation extraction, and validation.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from src.agents.generation_agent import (
    MessageGenerator,
    generate_variants,
    generate_variant,
    load_prompt_template,
    extract_citations,
    validate_variant_format,
)


class TestMessageGenerator:
    """Test cases for MessageGenerator class."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock Azure OpenAI client."""
        client = Mock()
        client.generate_completion.return_value = {
            "text": "Subject: Exclusive Premium Access\n\nBody: Dear valued customer, we are excited to offer you exclusive access to our premium features [Source: Premium Widget Features, Advanced Capabilities]. This limited-time opportunity is designed specifically for high-value customers like you [Source: Customer Success Stories, High-Value Testimonials]. Don't miss out on these enhanced capabilities that will transform your experience. Act now to secure your premium access and join our elite customer community.",
            "input_tokens": 450,
            "output_tokens": 185,
            "tokens_used": 635,
            "cost_usd": 0.0245,
            "duration_ms": 1250,
            "model": "gpt-4o-mini",
        }
        return client

    @pytest.fixture
    def sample_segment(self):
        """Sample customer segment for testing."""
        return {
            "name": "High-Value Recent",
            "features": {
                "avg_order_value": 275.0,
                "avg_purchase_frequency": 14.5,
                "engagement_score": 0.48,
            },
        }

    @pytest.fixture
    def sample_content(self):
        """Sample retrieved content for testing."""
        return [
            {
                "document_id": "DOC001",
                "title": "Premium Widget Features",
                "snippet": "Our Premium Widget includes advanced features designed specifically for our most valued customers.",
                "relevance_score": 0.95,
                "paragraph_index": 0,
            },
            {
                "document_id": "DOC002",
                "title": "Customer Success Stories",
                "snippet": "High-value customers have seen remarkable results with our premium offerings.",
                "relevance_score": 0.88,
                "paragraph_index": 1,
            },
        ]

    def test_init_with_client(self, mock_openai_client):
        """Test MessageGenerator initialization with provided client."""
        generator = MessageGenerator(mock_openai_client)
        assert generator.client == mock_openai_client
        assert generator.tones == ["urgent", "informational", "friendly"]

    @patch("src.agents.generation_agent.AzureOpenAIClient")
    def test_init_without_client(self, mock_client_class):
        """Test MessageGenerator initialization without provided client."""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        generator = MessageGenerator()
        assert generator.client == mock_instance
        mock_client_class.assert_called_once()

    def test_generate_variants_success(self, mock_openai_client, sample_segment, sample_content):
        """Test successful generation of 3 variants."""
        generator = MessageGenerator(mock_openai_client)

        with patch.object(generator, "load_prompt_template") as mock_load_template:
            mock_load_template.return_value = "Test template with {segment_name} and {tone}"

            variants = generator.generate_variants(sample_segment, sample_content)

            assert len(variants) == 3
            assert all("variant_id" in v for v in variants)
            assert all("tone" in v for v in variants)
            assert {v["tone"] for v in variants} == {"urgent", "informational", "friendly"}

    def test_generate_variants_invalid_segment(self, mock_openai_client, sample_content):
        """Test generate_variants with invalid segment."""
        generator = MessageGenerator(mock_openai_client)

        with pytest.raises(ValueError, match="Segment must contain 'name' field"):
            generator.generate_variants({}, sample_content)

    def test_generate_variants_empty_content(self, mock_openai_client, sample_segment):
        """Test generate_variants with empty content."""
        generator = MessageGenerator(mock_openai_client)

        with pytest.raises(ValueError, match="Content cannot be empty"):
            generator.generate_variants(sample_segment, [])

    def test_generate_variant_success(self, mock_openai_client, sample_segment, sample_content):
        """Test successful generation of single variant."""
        generator = MessageGenerator(mock_openai_client)

        with patch.object(generator, "load_prompt_template") as mock_load_template:
            mock_load_template.return_value = "Test template"

            variant = generator.generate_variant(sample_segment, sample_content, "urgent")

            assert variant["segment"] == "High-Value Recent"
            assert variant["tone"] == "urgent"
            assert "variant_id" in variant
            assert "subject" in variant
            assert "body" in variant
            assert "citations" in variant
            assert "generated_at" in variant
            assert "generation_metadata" in variant

    def test_generate_variant_invalid_tone(
        self, mock_openai_client, sample_segment, sample_content
    ):
        """Test generate_variant with invalid tone."""
        generator = MessageGenerator(mock_openai_client)

        with pytest.raises(ValueError, match="Invalid tone: invalid"):
            generator.generate_variant(sample_segment, sample_content, "invalid")

    @patch("builtins.open", new_callable=mock_open, read_data="Base template with {segment_name}")
    @patch("os.path.exists")
    def test_load_prompt_template_success(self, mock_exists, mock_file, mock_openai_client):
        """Test successful prompt template loading."""
        mock_exists.return_value = True
        mock_file.side_effect = [
            mock_open(read_data="Base template with {segment_name}").return_value,
            mock_open(read_data="Urgent tone instructions").return_value,
        ]

        generator = MessageGenerator(mock_openai_client)
        template = generator.load_prompt_template("config/prompts/generation_prompt.txt", "urgent")

        assert "Base template with {segment_name}" in template
        assert "Urgent tone instructions" in template

    @patch("os.path.exists")
    def test_load_prompt_template_missing_base(self, mock_exists, mock_openai_client):
        """Test load_prompt_template with missing base template."""
        mock_exists.return_value = False

        generator = MessageGenerator(mock_openai_client)

        with pytest.raises(FileNotFoundError, match="Base template not found"):
            generator.load_prompt_template("missing.txt", "urgent")

    def test_load_prompt_template_invalid_tone(self, mock_openai_client):
        """Test load_prompt_template with invalid tone."""
        generator = MessageGenerator(mock_openai_client)

        with pytest.raises(ValueError, match="Invalid tone: invalid"):
            generator.load_prompt_template("config/prompts/generation_prompt.txt", "invalid")

    def test_extract_citations_success(self, mock_openai_client, sample_content):
        """Test successful citation extraction."""
        generator = MessageGenerator(mock_openai_client)

        body = "Check out our premium features [Source: Premium Widget Features, Advanced Capabilities] and success stories [Source: Customer Success Stories, High-Value Testimonials]."

        citations = generator.extract_citations(body, sample_content)

        assert len(citations) == 2
        assert citations[0]["document_id"] == "DOC001"
        assert citations[0]["title"] == "Premium Widget Features"
        assert citations[1]["document_id"] == "DOC002"
        assert citations[1]["title"] == "Customer Success Stories"

    def test_extract_citations_no_matches(self, mock_openai_client, sample_content):
        """Test citation extraction with no citation patterns."""
        generator = MessageGenerator(mock_openai_client)

        body = "This is a message with no citations."
        citations = generator.extract_citations(body, sample_content)

        assert len(citations) == 0

    def test_extract_citations_unknown_document(self, mock_openai_client, sample_content):
        """Test citation extraction with unknown document reference."""
        generator = MessageGenerator(mock_openai_client)

        body = "Check this out [Source: Unknown Document, Some Section]."
        citations = generator.extract_citations(body, sample_content)

        assert len(citations) == 1
        assert citations[0]["document_id"] == "unknown"
        assert citations[0]["title"] == "Unknown Document"

    def test_validate_variant_format_valid(self, mock_openai_client):
        """Test validation of valid variant."""
        generator = MessageGenerator(mock_openai_client)

        variant = {
            "subject": "Great Offer Just for You",
            "body": " ".join(["Word"] * 175)
            + " [Source: Test Doc, Section]",  # 175 words + citation
            "citations": [{"document_id": "DOC001"}],
        }

        result = generator.validate_variant_format(variant)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        # Citation adds 4 words: "Source:", "Test", "Doc,", "Section]"
        assert result["word_count"] == 179  # 175 + 4 citation words
        assert result["citation_count"] == 1

    def test_validate_variant_format_subject_too_long(self, mock_openai_client):
        """Test validation with subject too long."""
        generator = MessageGenerator(mock_openai_client)

        variant = {
            "subject": "A" * 70,  # Too long
            "body": " ".join(["Word"] * 175) + " [Source: Test Doc, Section]",
            "citations": [{"document_id": "DOC001"}],
        }

        result = generator.validate_variant_format(variant)

        assert result["valid"] is False
        assert any("Subject too long" in error for error in result["errors"])

    def test_validate_variant_format_body_too_short(self, mock_openai_client):
        """Test validation with body too short."""
        generator = MessageGenerator(mock_openai_client)

        variant = {
            "subject": "Short Subject",
            "body": "Too short [Source: Test Doc, Section]",  # Only 4 words
            "citations": [{"document_id": "DOC001"}],
        }

        result = generator.validate_variant_format(variant)

        assert result["valid"] is False
        assert any("Body too short" in error for error in result["errors"])

    def test_validate_variant_format_no_citations(self, mock_openai_client):
        """Test validation with no citations."""
        generator = MessageGenerator(mock_openai_client)

        variant = {
            "subject": "Subject",
            "body": " ".join(["Word"] * 175),  # No citations
            "citations": [],
        }

        result = generator.validate_variant_format(variant)

        assert result["valid"] is False
        assert any("Insufficient citations" in error for error in result["errors"])
        assert any("No properly formatted citations" in error for error in result["errors"])

    def test_parse_generated_message_structured(self, mock_openai_client):
        """Test parsing of well-structured generated message."""
        generator = MessageGenerator(mock_openai_client)

        generated_text = """Subject: Exclusive Premium Access

Body: Dear valued customer, we are excited to offer you exclusive access to our premium features. This limited-time opportunity is designed specifically for high-value customers like you."""

        result = generator._parse_generated_message(generated_text)

        assert result["subject"] == "Exclusive Premium Access"
        assert "Dear valued customer" in result["body"]

    def test_parse_generated_message_unstructured(self, mock_openai_client):
        """Test parsing of unstructured generated message."""
        generator = MessageGenerator(mock_openai_client)

        generated_text = """Exclusive Premium Access
        Dear valued customer, we are excited to offer you exclusive access."""

        result = generator._parse_generated_message(generated_text)

        assert result["subject"] == "Exclusive Premium Access"
        assert "Dear valued customer" in result["body"]


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch("src.agents.generation_agent.MessageGenerator")
    def test_generate_variants_function(self, mock_generator_class):
        """Test generate_variants convenience function."""
        mock_instance = Mock()
        mock_instance.generate_variants.return_value = [{"variant_id": "TEST"}]
        mock_generator_class.return_value = mock_instance

        segment = {"name": "Test"}
        content = [{"document_id": "DOC001"}]

        result = generate_variants(segment, content)

        mock_generator_class.assert_called_once()
        mock_instance.generate_variants.assert_called_once_with(segment, content)
        assert result == [{"variant_id": "TEST"}]

    @patch("src.agents.generation_agent.MessageGenerator")
    def test_generate_variant_function(self, mock_generator_class):
        """Test generate_variant convenience function."""
        mock_instance = Mock()
        mock_instance.generate_variant.return_value = {"variant_id": "TEST"}
        mock_generator_class.return_value = mock_instance

        segment = {"name": "Test"}
        content = [{"document_id": "DOC001"}]
        tone = "urgent"

        result = generate_variant(segment, content, tone)

        mock_generator_class.assert_called_once()
        mock_instance.generate_variant.assert_called_once_with(segment, content, tone)
        assert result == {"variant_id": "TEST"}

    @patch("src.agents.generation_agent.MessageGenerator")
    def test_load_prompt_template_function(self, mock_generator_class):
        """Test load_prompt_template convenience function."""
        mock_instance = Mock()
        mock_instance.load_prompt_template.return_value = "Template"
        mock_generator_class.return_value = mock_instance

        result = load_prompt_template("path/to/template.txt", "urgent")

        mock_generator_class.assert_called_once()
        mock_instance.load_prompt_template.assert_called_once_with("path/to/template.txt", "urgent")
        assert result == "Template"

    @patch("src.agents.generation_agent.MessageGenerator")
    def test_extract_citations_function(self, mock_generator_class):
        """Test extract_citations convenience function."""
        mock_instance = Mock()
        mock_instance.extract_citations.return_value = [{"document_id": "DOC001"}]
        mock_generator_class.return_value = mock_instance

        body = "Test body [Source: Test, Section]"
        content = [{"document_id": "DOC001"}]

        result = extract_citations(body, content)

        mock_generator_class.assert_called_once()
        mock_instance.extract_citations.assert_called_once_with(body, content)
        assert result == [{"document_id": "DOC001"}]

    @patch("src.agents.generation_agent.MessageGenerator")
    def test_validate_variant_format_function(self, mock_generator_class):
        """Test validate_variant_format convenience function."""
        mock_instance = Mock()
        mock_instance.validate_variant_format.return_value = {"valid": True}
        mock_generator_class.return_value = mock_instance

        variant = {"subject": "Test", "body": "Test body", "citations": []}

        result = validate_variant_format(variant)

        mock_generator_class.assert_called_once()
        mock_instance.validate_variant_format.assert_called_once_with(variant)
        assert result == {"valid": True}


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock Azure OpenAI client."""
        client = Mock()
        client.generate_completion.return_value = {
            "text": "Subject: Test\n\nBody: Test body with citation [Source: Test Doc, Section].",
            "input_tokens": 100,
            "output_tokens": 50,
            "tokens_used": 150,
            "cost_usd": 0.01,
            "duration_ms": 500,
            "model": "gpt-4o-mini",
        }
        return client

    def test_citation_extraction_case_insensitive(self, mock_openai_client):
        """Test citation extraction is case insensitive."""
        generator = MessageGenerator(mock_openai_client)

        content = [{"document_id": "DOC001", "title": "Premium Features"}]
        body = "Check this [source: premium features, section] out."

        citations = generator.extract_citations(body, content)

        assert len(citations) == 1
        assert citations[0]["document_id"] == "DOC001"

    def test_citation_extraction_partial_title_match(self, mock_openai_client):
        """Test citation extraction with partial title matching."""
        generator = MessageGenerator(mock_openai_client)

        content = [{"document_id": "DOC001", "title": "Premium Widget Features"}]
        body = "Check this [Source: Premium Widget, Advanced Section] out."

        citations = generator.extract_citations(body, content)

        assert len(citations) == 1
        assert citations[0]["document_id"] == "DOC001"

    def test_empty_generated_text_parsing(self, mock_openai_client):
        """Test parsing of empty generated text."""
        generator = MessageGenerator(mock_openai_client)

        result = generator._parse_generated_message("")

        assert result["subject"] == ""
        assert result["body"] == ""

    def test_malformed_generated_text_parsing(self, mock_openai_client):
        """Test parsing of malformed generated text."""
        generator = MessageGenerator(mock_openai_client)

        generated_text = "Random text without proper structure"
        result = generator._parse_generated_message(generated_text)

        # Should use first part as subject, rest as body
        assert result["subject"] == "Random text without proper structure"
        assert result["body"] == ""
