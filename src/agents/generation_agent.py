"""
Module: generation_agent.py
Purpose: Generate personalized message variants using Azure OpenAI with citations.

This module implements the Generation Agent responsible for creating
personalized message variants with proper citations to approved content.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from src.integrations.azure_openai import AzureOpenAIClient

# Configure logger
logger = logging.getLogger(__name__)

# Generation constants
VARIANT_TONES = ["urgent", "informational", "friendly"]
MAX_SUBJECT_LENGTH = 60
MIN_BODY_WORDS = 150
MAX_BODY_WORDS = 250
MIN_CITATIONS = 1


class MessageGenerator:
    """
    Message generation agent for creating personalized variants.
    
    This class handles the generation of personalized message variants
    using Azure OpenAI with proper citations to approved content.
    """
    
    def __init__(self, openai_client: Optional[AzureOpenAIClient] = None):
        """
        Initialize the message generator.
        
        Args:
            openai_client: Optional Azure OpenAI client. If None, creates default client.
        """
        self.client = openai_client or AzureOpenAIClient()
        self.tones = VARIANT_TONES
        logger.info("MessageGenerator initialized")
    
    def generate_variants(
        self, 
        segment: Dict[str, Any], 
        content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate 3 message variants with different tones.
        
        Args:
            segment: Segment information with name and features
            content: Retrieved content snippets for grounding
            
        Returns:
            List of 3 message variants with different tones
            
        Raises:
            ValueError: If segment or content is invalid
        """
        if not segment or 'name' not in segment:
            raise ValueError("Segment must contain 'name' field")
        
        if not content:
            raise ValueError("Content cannot be empty")
        
        logger.info(f"Generating variants for segment: {segment['name']}")
        
        variants = []
        
        for tone in self.tones:
            try:
                variant = self.generate_variant(segment, content, tone)
                variants.append(variant)
                logger.debug(f"Generated {tone} variant: {variant['variant_id']}")
            except Exception as e:
                logger.error(f"Failed to generate {tone} variant: {e}")
                # Continue with other tones rather than failing completely
                continue
        
        logger.info(f"Generated {len(variants)} variants for segment '{segment['name']}'")
        return variants
    
    def generate_variant(
        self, 
        segment: Dict[str, Any], 
        content: List[Dict[str, Any]], 
        tone: str
    ) -> Dict[str, Any]:
        """
        Generate a single message variant with specified tone.
        
        Args:
            segment: Segment information
            content: Retrieved content snippets
            tone: Variant tone (urgent, informational, friendly)
            
        Returns:
            Dictionary containing variant with subject, body, citations
            
        Raises:
            ValueError: If tone is invalid or inputs are malformed
        """
        if tone not in self.tones:
            raise ValueError(f"Invalid tone: {tone}. Must be one of {self.tones}")
        
        # Generate unique variant ID
        variant_id = f"VAR_{uuid4().hex[:8].upper()}"
        
        # Load and format prompt template
        prompt = self._build_prompt(segment, content, tone)
        
        # Generate completion using Azure OpenAI
        start_time = datetime.utcnow()
        response = self.client.generate_completion(
            prompt=prompt,
            system_message="You are an expert marketing copywriter creating personalized email messages.",
            max_tokens=500  # Allow enough tokens for subject + body + citations
        )
        
        # Parse the generated message
        parsed_message = self._parse_generated_message(response['text'])
        
        # Extract citations from the body
        citations = self.extract_citations(parsed_message['body'], content)
        
        # Validate the variant
        validation_result = self.validate_variant_format({
            'subject': parsed_message['subject'],
            'body': parsed_message['body'],
            'citations': citations
        })
        
        if not validation_result['valid']:
            logger.warning(f"Generated variant failed validation: {validation_result['errors']}")
        
        # Create variant object
        variant = {
            "variant_id": variant_id,
            "segment": segment['name'],
            "subject": parsed_message['subject'],
            "body": parsed_message['body'],
            "tone": tone,
            "citations": citations,
            "generated_at": start_time.isoformat(),
            "generation_metadata": {
                "model": response.get('model', 'gpt-4o-mini'),
                "tokens_input": response.get('input_tokens', 0),
                "tokens_output": response.get('output_tokens', 0),
                "tokens_total": response.get('tokens_used', 0),
                "cost_usd": response.get('cost_usd', 0.0),
                "duration_ms": response.get('duration_ms', 0),
                "prompt_template": f"generation_prompt_{tone}"
            },
            "validation": validation_result
        }
        
        logger.info(f"Generated variant {variant_id} ({tone}) - {len(citations)} citations")
        return variant
    
    def load_prompt_template(self, template_path: str, tone: str) -> str:
        """
        Load prompt template from file and apply tone-specific instructions.
        
        Args:
            template_path: Path to base prompt template
            tone: Tone variant (urgent, informational, friendly)
            
        Returns:
            Complete prompt template with tone instructions
            
        Raises:
            FileNotFoundError: If template files don't exist
            ValueError: If tone is invalid
        """
        if tone not in self.tones:
            raise ValueError(f"Invalid tone: {tone}. Must be one of {self.tones}")
        
        # Load base template
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Base template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            base_template = f.read()
        
        # Load tone-specific instructions
        tone_template_path = f"config/prompts/variants/{tone}.txt"
        if not os.path.exists(tone_template_path):
            raise FileNotFoundError(f"Tone template not found: {tone_template_path}")
        
        with open(tone_template_path, 'r', encoding='utf-8') as f:
            tone_instructions = f.read()
        
        # Combine templates
        combined_template = f"{base_template}\n\nTONE INSTRUCTIONS:\n{tone_instructions}"
        
        logger.debug(f"Loaded prompt template for tone: {tone}")
        return combined_template
    
    def extract_citations(self, body: str, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citations from message body using regex and map to source documents.
        
        Args:
            body: Message body text
            content: Retrieved content snippets for mapping
            
        Returns:
            List of citation objects with document metadata
        """
        citations = []
        
        # Regex pattern to match citation format: [Source: Document Title, Section]
        citation_pattern = r'\[Source:\s*([^,]+),\s*([^\]]+)\]'
        
        matches = re.finditer(citation_pattern, body, re.IGNORECASE)
        
        for match in matches:
            title_part = match.group(1).strip()
            section_part = match.group(2).strip()
            
            # Find matching content document
            matched_doc = None
            for doc in content:
                if doc.get('title', '').lower() in title_part.lower() or title_part.lower() in doc.get('title', '').lower():
                    matched_doc = doc
                    break
            
            citation = {
                "document_id": matched_doc.get('document_id') if matched_doc else 'unknown',
                "title": matched_doc.get('title') if matched_doc else title_part,
                "paragraph_index": matched_doc.get('paragraph_index', 0) if matched_doc else 0,
                "text_snippet": section_part,
                "citation_text": match.group(0)
            }
            
            citations.append(citation)
        
        logger.debug(f"Extracted {len(citations)} citations from message body")
        return citations
    
    def validate_variant_format(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate variant format and constraints.
        
        Args:
            variant: Variant dictionary with subject, body, citations
            
        Returns:
            Validation result with valid flag and error messages
        """
        errors = []
        
        # Validate subject length
        subject = variant.get('subject', '')
        if len(subject) > MAX_SUBJECT_LENGTH:
            errors.append(f"Subject too long: {len(subject)} chars (max {MAX_SUBJECT_LENGTH})")
        
        if not subject.strip():
            errors.append("Subject cannot be empty")
        
        # Validate body word count
        body = variant.get('body', '')
        word_count = len(body.split())
        
        if word_count < MIN_BODY_WORDS:
            errors.append(f"Body too short: {word_count} words (min {MIN_BODY_WORDS})")
        elif word_count > MAX_BODY_WORDS:
            errors.append(f"Body too long: {word_count} words (max {MAX_BODY_WORDS})")
        
        if not body.strip():
            errors.append("Body cannot be empty")
        
        # Validate citations
        citations = variant.get('citations', [])
        if len(citations) < MIN_CITATIONS:
            errors.append(f"Insufficient citations: {len(citations)} (min {MIN_CITATIONS})")
        
        # Check for citation format in body
        citation_pattern = r'\[Source:[^\]]+\]'
        if not re.search(citation_pattern, body):
            errors.append("No properly formatted citations found in body")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "word_count": word_count,
            "subject_length": len(subject),
            "citation_count": len(citations)
        }
    
    def _build_prompt(
        self, 
        segment: Dict[str, Any], 
        content: List[Dict[str, Any]], 
        tone: str
    ) -> str:
        """
        Build generation prompt from template and inputs.
        
        Args:
            segment: Segment information
            content: Retrieved content snippets
            tone: Variant tone
            
        Returns:
            Formatted prompt string
        """
        # Load prompt template
        base_template_path = "config/prompts/generation_prompt.txt"
        template = self.load_prompt_template(base_template_path, tone)
        
        # Format segment features for prompt
        segment_features = segment.get('features', {})
        features_text = ', '.join([f"{k}: {v}" for k, v in segment_features.items()])
        
        # Format retrieved content snippets
        content_snippets = []
        for i, doc in enumerate(content, 1):
            snippet_text = f"{i}. [{doc.get('document_id')}] {doc.get('title')}:\n{doc.get('snippet')}"
            content_snippets.append(snippet_text)
        
        retrieved_snippets = '\n\n'.join(content_snippets)
        
        # Format the template
        formatted_prompt = template.format(
            segment_name=segment.get('name', 'Unknown'),
            segment_features=features_text,
            retrieved_snippets=retrieved_snippets,
            tone=tone.title()
        )
        
        return formatted_prompt
    
    def _parse_generated_message(self, generated_text: str) -> Dict[str, str]:
        """
        Parse generated message to extract subject and body.
        
        Args:
            generated_text: Raw generated text from LLM
            
        Returns:
            Dictionary with parsed subject and body
        """
        # Initialize defaults
        subject = ""
        body = ""
        
        # Split by lines and look for Subject: and Body: markers
        lines = generated_text.strip().split('\n')
        
        current_section = None
        body_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section markers
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()  # Remove "Subject:" prefix
                current_section = 'subject'
            elif line.lower().startswith('body:'):
                current_section = 'body'
                body_content = line[5:].strip()  # Remove "Body:" prefix
                if body_content:
                    body_lines.append(body_content)
            elif current_section == 'body' and line:
                body_lines.append(line)
        
        # Join body lines
        if body_lines:
            body = '\n'.join(body_lines)
        
        # Fallback: if no clear structure, try to extract from raw text
        if not subject and not body:
            # Look for first line as potential subject
            if lines:
                subject = lines[0][:MAX_SUBJECT_LENGTH]
                body = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        return {
            "subject": subject,
            "body": body
        }


# Convenience functions for direct usage
def generate_variants(segment: Dict[str, Any], content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to generate variants for a segment.
    
    Args:
        segment: Segment information
        content: Retrieved content snippets
        
    Returns:
        List of 3 message variants
    """
    generator = MessageGenerator()
    return generator.generate_variants(segment, content)


def generate_variant(
    segment: Dict[str, Any], 
    content: List[Dict[str, Any]], 
    tone: str
) -> Dict[str, Any]:
    """
    Convenience function to generate a single variant.
    
    Args:
        segment: Segment information
        content: Retrieved content snippets
        tone: Variant tone
        
    Returns:
        Single message variant
    """
    generator = MessageGenerator()
    return generator.generate_variant(segment, content, tone)


def load_prompt_template(template_path: str, tone: str) -> str:
    """
    Convenience function to load prompt template.
    
    Args:
        template_path: Path to base template
        tone: Tone variant
        
    Returns:
        Complete prompt template
    """
    generator = MessageGenerator()
    return generator.load_prompt_template(template_path, tone)


def extract_citations(body: str, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to extract citations from body.
    
    Args:
        body: Message body text
        content: Retrieved content for mapping
        
    Returns:
        List of citation objects
    """
    generator = MessageGenerator()
    return generator.extract_citations(body, content)


def validate_variant_format(variant: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate variant format.
    
    Args:
        variant: Variant to validate
        
    Returns:
        Validation result
    """
    generator = MessageGenerator()
    return generator.validate_variant_format(variant)


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the generation agent
    try:
        # Test segment
        test_segment = {
            "name": "High-Value Recent",
            "features": {
                "avg_order_value": 275.0,
                "avg_purchase_frequency": 14.5,
                "engagement_score": 0.48
            }
        }
        
        # Test content
        test_content = [
            {
                "document_id": "DOC001",
                "title": "Premium Widget Features",
                "snippet": "Our Premium Widget includes advanced features designed specifically for our most valued customers. These exclusive capabilities provide enhanced performance and priority support.",
                "relevance_score": 0.95
            },
            {
                "document_id": "DOC002", 
                "title": "Customer Success Stories",
                "snippet": "High-value customers have seen remarkable results with our premium offerings. Success stories show increased efficiency and satisfaction among our gold-tier members.",
                "relevance_score": 0.88
            }
        ]
        
        print(f"🧪 Testing generation for segment: {test_segment['name']}")
        
        # Test single variant generation
        variant = generate_variant(test_segment, test_content, "urgent")
        print(f"📝 Generated variant: {variant['variant_id']}")
        print(f"   Subject: {variant['subject']}")
        print(f"   Body length: {len(variant['body'].split())} words")
        print(f"   Citations: {len(variant['citations'])}")
        
        # Test validation
        validation = validate_variant_format(variant)
        print(f"✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")
        if not validation['valid']:
            print(f"   Errors: {validation['errors']}")
        
        print("✅ Generation agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test execution failed: {e}")