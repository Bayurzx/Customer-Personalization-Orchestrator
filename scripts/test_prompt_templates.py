#!/usr/bin/env python3
"""
Test script to validate prompt templates for Task 3.1.

This script verifies that:
1. Base template exists and contains required variables
2. All 3 tone variants exist
3. Template variables are clearly defined
4. Citation format is specified
5. Templates can be loaded and formatted
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_prompt_templates():
    """Test all prompt templates for completeness and correctness."""

    print("🧪 Testing Prompt Templates for Task 3.1")
    print("=" * 50)

    # Test 1: Check base template exists and has required content
    base_template_path = project_root / "config" / "prompts" / "generation_prompt.txt"

    if not base_template_path.exists():
        print("❌ Base template not found")
        return False

    with open(base_template_path, "r") as f:
        base_content = f.read()

    # Check for required variables
    required_variables = ["{segment_name}", "{segment_features}", "{retrieved_snippets}", "{tone}"]
    missing_vars = []

    for var in required_variables:
        if var not in base_content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Base template missing variables: {missing_vars}")
        return False

    print("✅ Base template exists with all required variables")

    # Test 2: Check citation format is specified
    citation_indicators = ["[Source:", "Document Title", "Section]"]
    citation_found = all(indicator in base_content for indicator in citation_indicators)

    if not citation_found:
        print("❌ Citation format not properly specified in base template")
        return False

    print("✅ Citation format properly specified")

    # Test 3: Check all tone variants exist
    tone_variants = ["urgent", "informational", "friendly"]
    variants_path = project_root / "config" / "prompts" / "variants"

    for tone in tone_variants:
        variant_path = variants_path / f"{tone}.txt"
        if not variant_path.exists():
            print(f"❌ Tone variant '{tone}' not found")
            return False

        # Check variant has content
        with open(variant_path, "r") as f:
            variant_content = f.read().strip()

        if len(variant_content) < 100:  # Reasonable minimum length
            print(f"❌ Tone variant '{tone}' appears to be empty or too short")
            return False

    print("✅ All 3 tone variants exist with content")

    # Test 4: Check template can be formatted (simulate variable substitution)
    try:
        # Test with sample data
        sample_data = {
            "segment_name": "High-Value Recent",
            "segment_features": "avg_order_value: 275.00, engagement_score: 0.48",
            "retrieved_snippets": "[DOC001] Premium Features: Advanced capabilities...",
            "tone": "urgent",
        }

        formatted_template = base_content.format(**sample_data)

        # Check that variables were replaced
        for var in required_variables:
            if var in formatted_template:
                print(f"❌ Variable {var} not properly substituted")
                return False

        print("✅ Template variables can be properly substituted")

    except KeyError as e:
        print(f"❌ Template formatting failed: {e}")
        return False

    # Test 5: Check output format requirements
    format_indicators = ["Subject:", "Body:", "60 characters", "150-200 words"]
    format_found = all(indicator in base_content for indicator in format_indicators)

    if not format_found:
        print("❌ Output format requirements not properly specified")
        return False

    print("✅ Output format requirements properly specified")

    # Test 6: Check documentation exists
    readme_path = project_root / "config" / "prompts" / "README.md"
    if not readme_path.exists():
        print("❌ Prompt documentation (README.md) not found")
        return False

    print("✅ Prompt documentation exists")

    print("\n🎉 All prompt template tests passed!")
    print("\nAcceptance Criteria Verification:")
    print("✅ Base template created with all necessary sections")
    print("✅ 3 tone variants created (urgent, informational, friendly)")
    print("✅ Template variables clearly defined")
    print("✅ Citation format specified in template")
    print("✅ Ready for manual testing with Azure OpenAI")

    return True


def demonstrate_template_usage():
    """Demonstrate how the templates would be used."""

    print("\n📋 Template Usage Demonstration")
    print("=" * 40)

    # Load base template
    base_template_path = project_root / "config" / "prompts" / "generation_prompt.txt"
    with open(base_template_path, "r") as f:
        base_template = f.read()

    # Load urgent tone variant
    urgent_path = project_root / "config" / "prompts" / "variants" / "urgent.txt"
    with open(urgent_path, "r") as f:
        urgent_instructions = f.read()

    # Sample data
    sample_segment = {
        "segment_name": "High-Value Recent",
        "segment_features": "avg_order_value: 275.00, purchase_frequency: 14.5, engagement_score: 0.48",
        "retrieved_snippets": """[DOC001] Premium Widget Features: Our Premium Widget includes advanced features designed specifically for our most valued customers, including priority support and exclusive access to new capabilities.

[DOC002] Customer Success Stories: High-value customers report 40% increased productivity and significant ROI improvements when using our premium features.""",
        "tone": "urgent",
    }

    # Combine base template with tone instructions
    full_prompt = base_template + "\n\n" + urgent_instructions

    # Format with sample data
    formatted_prompt = full_prompt.format(**sample_segment)

    print("Sample formatted prompt (first 500 characters):")
    print("-" * 50)
    print(formatted_prompt[:500] + "...")
    print("-" * 50)

    print("\n✅ Template successfully formatted with sample data")


if __name__ == "__main__":
    success = test_prompt_templates()

    if success:
        demonstrate_template_usage()
        print("\n🚀 Prompt templates are ready for Task 3.2 (Azure OpenAI Integration)")
    else:
        print("\n❌ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)
