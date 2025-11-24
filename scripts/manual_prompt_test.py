#!/usr/bin/env python3
"""
Manual test script for prompt templates with Azure OpenAI.

This script demonstrates the prompt templates working with actual Azure OpenAI API calls.
Use this for manual validation of prompt quality and output format.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.azure_openai import get_openai_client


def load_prompt_template(tone: str = None) -> str:
    """
    Load the base prompt template and optionally append tone instructions.

    Args:
        tone: Optional tone variant ('urgent', 'informational', 'friendly')

    Returns:
        Complete prompt template string
    """
    # Load base template
    base_path = project_root / "config" / "prompts" / "generation_prompt.txt"
    with open(base_path, "r") as f:
        base_template = f.read()

    # Add tone instructions if specified
    if tone:
        tone_path = project_root / "config" / "prompts" / "variants" / f"{tone}.txt"
        if tone_path.exists():
            with open(tone_path, "r") as f:
                tone_instructions = f.read()
            base_template += "\n\n" + tone_instructions

    return base_template


def create_sample_data() -> Dict:
    """Create sample segment and content data for testing."""
    return {
        "segment_name": "High-Value Recent",
        "segment_features": """avg_order_value: 275.00
purchase_frequency: 14.5 per year
engagement_score: 0.48
tier: Gold
last_engagement_days: 5""",
        "retrieved_snippets": """[DOC001] Premium Widget Features: Our Premium Widget includes advanced features designed specifically for our most valued customers. These features include priority support, exclusive access to new capabilities, and enhanced performance optimization that delivers 40% faster processing.

[DOC002] Customer Success Stories: High-value customers report significant ROI improvements when using our premium features. Sarah from TechCorp increased her team's productivity by 35% within the first month of upgrading to premium features.

[DOC003] Exclusive Benefits Program: Gold tier customers enjoy exclusive benefits including early access to new features, dedicated account management, and priority technical support with guaranteed 2-hour response times.""",
        "tone": "urgent",  # Will be replaced per test
    }


def test_prompt_with_openai(tone: str, sample_data: Dict) -> Dict:
    """
    Test a prompt template with Azure OpenAI.

    Args:
        tone: Tone variant to test
        sample_data: Sample segment and content data

    Returns:
        Dictionary with test results
    """
    try:
        # Load and format prompt
        template = load_prompt_template(tone)
        sample_data["tone"] = tone
        formatted_prompt = template.format(**sample_data)

        # Get OpenAI client
        client = get_openai_client()
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        # Make API call
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a marketing copywriter."},
                {"role": "user", "content": formatted_prompt},
            ],
            max_completion_tokens=500,
        )

        generated_content = response.choices[0].message.content.strip()

        # Parse response
        result = {
            "tone": tone,
            "success": True,
            "content": generated_content,
            "tokens_used": response.usage.total_tokens,
            "cost_estimate": calculate_cost(response.usage.total_tokens),
            "validation": validate_output(generated_content),
        }

        return result

    except Exception as e:
        return {
            "tone": tone,
            "success": False,
            "error": str(e),
            "content": None,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "validation": {},
        }


def calculate_cost(total_tokens: int) -> float:
    """Calculate estimated cost for gpt-4o-mini."""
    # Rough estimate: assume 70% input, 30% output tokens
    input_tokens = int(total_tokens * 0.7)
    output_tokens = int(total_tokens * 0.3)

    # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output
    input_cost = (input_tokens / 1_000_000) * 0.15
    output_cost = (output_tokens / 1_000_000) * 0.60

    return input_cost + output_cost


def validate_output(content: str) -> Dict:
    """
    Validate the generated output against requirements.

    Args:
        content: Generated message content

    Returns:
        Dictionary with validation results
    """
    validation = {}

    # Check for Subject and Body sections
    has_subject = "Subject:" in content
    has_body = "Body:" in content

    validation["has_subject"] = has_subject
    validation["has_body"] = has_body

    if has_subject and has_body:
        # Extract subject and body
        parts = content.split("Body:", 1)
        if len(parts) == 2:
            subject_part = parts[0].replace("Subject:", "").strip()
            body_part = parts[1].strip()

            # Validate subject length (≤60 characters)
            validation["subject_length"] = len(subject_part)
            validation["subject_valid"] = len(subject_part) <= 60

            # Validate body word count (150-200 words)
            body_words = len(body_part.split())
            validation["body_word_count"] = body_words
            validation["body_valid"] = 150 <= body_words <= 200

            # Check for citations
            citation_count = content.count("[Source:")
            validation["citation_count"] = citation_count
            validation["citations_valid"] = citation_count >= 2

        else:
            validation["subject_valid"] = False
            validation["body_valid"] = False
            validation["citations_valid"] = False

    return validation


def run_manual_tests():
    """Run manual tests for all tone variants."""

    print("🧪 Manual Prompt Template Testing with Azure OpenAI")
    print("=" * 60)

    # Check if we can connect to Azure OpenAI
    try:
        from src.integrations.azure_openai import test_connection

        connection_result = test_connection()
        print(f"✅ Azure OpenAI Connection: {connection_result}")
    except Exception as e:
        print(f"❌ Azure OpenAI Connection Failed: {e}")
        print("Please ensure your .env file has the correct Azure OpenAI credentials.")
        return False

    print()

    # Test each tone variant
    tones = ["urgent", "informational", "friendly"]
    sample_data = create_sample_data()
    results = []

    for tone in tones:
        print(f"🎯 Testing {tone.title()} Tone...")
        result = test_prompt_with_openai(tone, sample_data)
        results.append(result)

        if result["success"]:
            print(f"✅ Generation successful")
            print(f"   Tokens used: {result['tokens_used']}")
            print(f"   Estimated cost: ${result['cost_estimate']:.6f}")

            # Show validation results
            val = result["validation"]
            print(
                f"   Subject length: {val.get('subject_length', 'N/A')} chars ({'✅' if val.get('subject_valid') else '❌'})"
            )
            print(
                f"   Body word count: {val.get('body_word_count', 'N/A')} words ({'✅' if val.get('body_valid') else '❌'})"
            )
            print(
                f"   Citations: {val.get('citation_count', 'N/A')} found ({'✅' if val.get('citations_valid') else '❌'})"
            )

            # Show first 200 characters of generated content
            preview = (
                result["content"][:200] + "..."
                if len(result["content"]) > 200
                else result["content"]
            )
            print(f"   Preview: {preview}")

        else:
            print(f"❌ Generation failed: {result['error']}")

        print()

    # Summary
    successful_tests = sum(1 for r in results if r["success"])
    total_tokens = sum(r["tokens_used"] for r in results)
    total_cost = sum(r["cost_estimate"] for r in results)

    print("📊 Test Summary")
    print("-" * 30)
    print(f"Successful tests: {successful_tests}/{len(tones)}")
    print(f"Total tokens used: {total_tokens}")
    print(f"Total estimated cost: ${total_cost:.6f}")

    if successful_tests == len(tones):
        print("\n🎉 All manual tests passed!")
        print("✅ Prompt templates are working correctly with Azure OpenAI")
        print("✅ Ready to proceed with Task 3.2 (Azure OpenAI Integration)")
        return True
    else:
        print(f"\n⚠️  {len(tones) - successful_tests} tests failed")
        print("Please review the prompt templates and try again.")
        return False


if __name__ == "__main__":
    success = run_manual_tests()

    if not success:
        sys.exit(1)
