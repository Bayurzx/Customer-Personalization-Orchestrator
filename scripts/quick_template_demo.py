#!/usr/bin/env python3
"""
Quick template demonstration without API calls.

This script shows how the prompt templates work by formatting them
with sample data, demonstrating the complete functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_and_format_template(tone: str = "friendly"):
    """Load and format a template with sample data."""
    
    print(f"🎯 Demonstrating {tone.title()} Tone Template")
    print("=" * 50)
    
    # Load base template
    base_path = project_root / "config" / "prompts" / "generation_prompt.txt"
    with open(base_path, 'r') as f:
        base_template = f.read()
    
    # Load tone variant
    tone_path = project_root / "config" / "prompts" / "variants" / f"{tone}.txt"
    with open(tone_path, 'r') as f:
        tone_instructions = f.read()
    
    # Combine templates
    full_template = base_template + "\n\n" + tone_instructions
    
    # Sample data
    sample_data = {
        'segment_name': 'High-Value Recent',
        'segment_features': '''avg_order_value: 275.00
purchase_frequency: 14.5 per year
engagement_score: 0.48
tier: Gold
last_engagement_days: 5''',
        'retrieved_snippets': '''[DOC001] Premium Widget Features: Our Premium Widget includes advanced features designed specifically for our most valued customers. These features include priority support, exclusive access to new capabilities, and enhanced performance optimization that delivers 40% faster processing.

[DOC002] Customer Success Stories: High-value customers report significant ROI improvements when using our premium features. Sarah from TechCorp increased her team's productivity by 35% within the first month of upgrading to premium features.

[DOC003] Exclusive Benefits Program: Gold tier customers enjoy exclusive benefits including early access to new features, dedicated account management, and priority technical support with guaranteed 2-hour response times.''',
        'tone': tone
    }
    
    # Format template
    try:
        formatted_prompt = full_template.format(**sample_data)
        
        print("✅ Template loaded and formatted successfully")
        print(f"📊 Template Statistics:")
        print(f"   - Base template: {len(base_template)} characters")
        print(f"   - Tone instructions: {len(tone_instructions)} characters") 
        print(f"   - Formatted prompt: {len(formatted_prompt)} characters")
        print(f"   - Sample data variables: {len(sample_data)} items")
        
        print(f"\n📋 Template Variables Replaced:")
        for key, value in sample_data.items():
            preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"   - {{{key}}}: {preview}")
        
        print(f"\n📄 Formatted Prompt Preview (first 800 characters):")
        print("-" * 60)
        print(formatted_prompt[:800] + "...")
        print("-" * 60)
        
        # Validate template structure
        required_sections = [
            'CUSTOMER SEGMENT: High-Value Recent',
            'SEGMENT CHARACTERISTICS:',
            'APPROVED CONTENT TO REFERENCE:',
            'TASK:',
            f'TONE: {tone}',
            'REQUIREMENTS:',
            'OUTPUT FORMAT:',
            'CITATION EXAMPLES:'
        ]
        
        print(f"\n🔍 Template Structure Validation:")
        all_present = True
        for section in required_sections:
            present = section in formatted_prompt
            print(f"   {'✅' if present else '❌'} {section}")
            if not present:
                all_present = False
        
        if all_present:
            print(f"\n🎉 Template structure is PERFECT!")
            print(f"✅ All required sections present")
            print(f"✅ Variables properly substituted")
            print(f"✅ Ready for Azure OpenAI generation")
        else:
            print(f"\n⚠️  Some template sections missing")
        
        return all_present
        
    except KeyError as e:
        print(f"❌ Template formatting failed: Missing variable {e}")
        return False
    except Exception as e:
        print(f"❌ Template error: {e}")
        return False

def demonstrate_all_tones():
    """Demonstrate all three tone variants."""
    
    print("🎨 Prompt Template Demonstration")
    print("=" * 60)
    print("This demonstrates that all prompt templates are working correctly")
    print("without making API calls to avoid rate limits.\n")
    
    tones = ['urgent', 'informational', 'friendly']
    results = []
    
    for i, tone in enumerate(tones, 1):
        print(f"\n{i}. {tone.upper()} TONE TEMPLATE")
        print("-" * 30)
        success = load_and_format_template(tone)
        results.append(success)
        
        if i < len(tones):
            print()  # Add spacing between tests
    
    # Summary
    successful = sum(results)
    print(f"\n📊 DEMONSTRATION SUMMARY")
    print("=" * 40)
    print(f"Templates tested: {len(tones)}")
    print(f"Successful: {successful}")
    print(f"Success rate: {successful/len(tones)*100:.0f}%")
    
    if successful == len(tones):
        print(f"\n🎉 ALL TEMPLATES WORKING PERFECTLY!")
        print(f"✅ Task 3.1 validation complete")
        print(f"✅ Ready for Task 3.2 (Azure OpenAI Integration)")
        print(f"\n💡 To test with actual API calls (when rate limits allow):")
        print(f"   python scripts/single_prompt_test.py")
        return True
    else:
        print(f"\n❌ {len(tones) - successful} templates have issues")
        return False

if __name__ == "__main__":
    success = demonstrate_all_tones()
    
    if not success:
        sys.exit(1)