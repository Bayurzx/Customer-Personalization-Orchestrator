# Prompt Templates Documentation

## Overview

This directory contains the prompt templates used by the Generation Agent to create personalized email messages. The templates are designed to work with Azure OpenAI (gpt-4o-mini) to generate high-quality, on-brand content that is grounded in approved source material.

## Template Structure

### Base Template: `generation_prompt.txt`

The base template provides the core structure and instructions for message generation. It includes:

- **Role Definition**: Establishes the AI as an expert marketing copywriter
- **Context Variables**: Placeholders for dynamic content insertion
- **Task Requirements**: Clear specifications for output format and constraints
- **Citation Instructions**: Detailed guidance on proper source attribution

### Tone Variants

Three tone-specific templates modify the base generation approach:

1. **`variants/urgent.txt`** - Creates time-sensitive, action-oriented messages
2. **`variants/informational.txt`** - Generates educational, value-driven content  
3. **`variants/friendly.txt`** - Produces warm, conversational messages

## Template Variables

The following variables are dynamically replaced during prompt generation:

| Variable | Description | Example |
|----------|-------------|---------|
| `{segment_name}` | Customer segment identifier | "High-Value Recent" |
| `{segment_features}` | Key characteristics of the segment | "avg_order_value: 275.00, engagement_score: 0.48" |
| `{retrieved_snippets}` | Approved content snippets with metadata | "[DOC001] Premium Features: Our advanced capabilities include..." |
| `{tone}` | Selected tone variant | "urgent", "informational", or "friendly" |

## Citation Format

All generated messages must include proper citations using the format:
```
[Source: Document Title, Section]
```

Examples:
- `[Source: Premium Widget Features, Advanced Capabilities]`
- `[Source: Customer Success Stories, High-Value Testimonials]`

## Design Decisions

### 1. Structured Output Format

**Decision**: Require specific "Subject:" and "Body:" labels in output
**Rationale**: Enables reliable parsing of generated content for downstream processing

### 2. Word Count Constraints

**Decision**: Enforce 150-200 word body length and 60-character subject limit
**Rationale**: 
- Optimal email engagement based on industry best practices
- Ensures mobile-friendly subject lines
- Maintains focus and readability

### 3. Mandatory Citations

**Decision**: Require 2-3 citations per message with specific format
**Rationale**:
- Ensures content grounding in approved materials
- Enables audit trail for compliance
- Maintains brand consistency and accuracy

### 4. Tone Separation

**Decision**: Use separate tone instruction files rather than inline tone descriptions
**Rationale**:
- Allows detailed tone guidance without cluttering base template
- Enables easy tone customization and A/B testing
- Provides clear separation of concerns

### 5. Professional Constraints

**Decision**: Emphasize professional, on-brand voice across all tones
**Rationale**:
- Maintains brand integrity
- Reduces risk of inappropriate content generation
- Ensures enterprise-appropriate messaging

## Usage Guidelines

### For Developers

1. **Template Loading**: Use the base template and append appropriate tone variant
2. **Variable Substitution**: Replace all `{variable}` placeholders before sending to LLM
3. **Response Parsing**: Extract content between "Subject:" and "Body:" labels
4. **Citation Extraction**: Use regex to find all `[Source: ...]` patterns

### For Content Managers

1. **Template Updates**: Modify tone variants to adjust brand voice
2. **Citation Examples**: Update examples to reflect current content library
3. **Constraint Adjustments**: Modify word counts based on performance data

## Testing Recommendations

### Manual Testing Checklist

- [ ] Subject lines under 60 characters
- [ ] Body text between 150-200 words
- [ ] At least 2 citations present
- [ ] Citations follow correct format
- [ ] Tone appropriate for variant
- [ ] Professional, on-brand voice maintained
- [ ] Clear call-to-action included
- [ ] Content grounded in provided snippets

### A/B Testing Opportunities

1. **Subject Line Length**: Test 40-50 vs 50-60 character limits
2. **Citation Density**: Test 2-3 vs 3-4 citations per message
3. **Tone Intensity**: Test subtle vs strong tone variations
4. **CTA Placement**: Test early vs late call-to-action positioning

## Maintenance

### Regular Reviews

- **Monthly**: Review citation format compliance in generated content
- **Quarterly**: Analyze tone variant performance and adjust instructions
- **Bi-annually**: Update examples and constraints based on campaign results

### Version Control

- All template changes should be documented with rationale
- Test template changes on small sample before full deployment
- Maintain backup of previous versions for rollback capability

## Troubleshooting

### Common Issues

1. **Missing Citations**: Ensure retrieved_snippets variable contains sufficient content
2. **Incorrect Format**: Verify output parsing logic handles edge cases
3. **Tone Inconsistency**: Check that tone variant instructions are clear and specific
4. **Length Violations**: Adjust word count guidance if consistently over/under target

### Performance Optimization

- Monitor token usage across different segment types
- Track generation latency and adjust complexity if needed
- Analyze citation accuracy and adjust instruction clarity