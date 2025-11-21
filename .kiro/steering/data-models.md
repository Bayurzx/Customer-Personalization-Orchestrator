# Data Models & Schemas

## Overview

This document defines all data structures used throughout the Customer Personalization Orchestrator, including input schemas, intermediate representations, and output formats.

---

## Customer Data Model

### Input Schema (CSV/DataFrame)

```python
customer_schema = {
    "customer_id": str,              # Unique identifier (e.g., "C001")
    "age": int,                      # Customer age
    "location": str,                 # City or region
    "tier": str,                     # Customer tier: "Gold", "Silver", "Bronze"
    "purchase_frequency": int,       # Purchases per year
    "avg_order_value": float,        # Average order value in USD
    "last_engagement_days": int,     # Days since last engagement
    "historical_open_rate": float,   # Historical email open rate (0.0-1.0)
    "historical_click_rate": float   # Historical email click rate (0.0-1.0)
}
```

### Example CSV

```csv
customer_id,age,location,tier,purchase_frequency,avg_order_value,last_engagement_days,historical_open_rate,historical_click_rate
C001,35,New York,Gold,12,250.00,5,0.45,0.12
C002,28,Los Angeles,Silver,6,150.00,30,0.35,0.08
C003,42,Chicago,Gold,18,300.00,3,0.50,0.15
```

### Pandas DataFrame Representation

```python
import pandas as pd

# Load data
customers_df = pd.read_csv('data/raw/customers.csv')

# Validation
assert customers_df['customer_id'].is_unique
assert (customers_df['age'] >= 18).all()
assert (customers_df['historical_open_rate'] >= 0).all()
assert (customers_df['historical_open_rate'] <= 1).all()
```

---

## Segment Model

### Segment Assignment Schema

```python
segment_assignment_schema = {
    "customer_id": str,
    "segment": str,                  # "High-Value Recent", "At-Risk", etc.
    "segment_id": int,               # Numeric cluster ID (for ML methods)
    "confidence": float,             # Assignment confidence (0.0-1.0)
    "features": {                    # Segment-defining features
        "avg_purchase_frequency": float,
        "avg_order_value": float,
        "engagement_score": float
    }
}
```

### Example JSON

```json
{
  "customer_id": "C001",
  "segment": "High-Value Recent",
  "segment_id": 0,
  "confidence": 0.85,
  "features": {
    "avg_purchase_frequency": 14.5,
    "avg_order_value": 275.00,
    "engagement_score": 0.48
  }
}
```

### Segment Metadata Schema

```python
segment_metadata_schema = {
    "segment": str,
    "segment_id": int,
    "size": int,                     # Number of customers
    "percentage": float,             # Percentage of total customers
    "characteristics": {
        "avg_age": float,
        "avg_purchase_frequency": float,
        "avg_order_value": float,
        "avg_engagement": float
    },
    "definition": str                # Human-readable description
}
```

---

## Content Document Model

### Content Document Schema

```python
content_document_schema = {
    "document_id": str,              # Unique ID (e.g., "DOC001")
    "title": str,                    # Document title
    "category": str,                 # "Product", "Promotion", "Support"
    "content": str,                  # Full text content
    "audience": str,                 # Target audience: "High-Value", "All", etc.
    "keywords": List[str],           # Search keywords
    "approval_date": str,            # ISO datetime string
    "source_url": str,               # Original content URL (optional)
    "metadata": {                    # Additional metadata
        "author": str,
        "version": str,
        "last_updated": str
    }
}
```

### Example JSON

```json
{
  "document_id": "DOC001",
  "title": "Premium Widget Features",
  "category": "Product",
  "content": "Our Premium Widget includes advanced features such as...",
  "audience": "High-Value",
  "keywords": ["premium", "features", "upgrade", "exclusive"],
  "approval_date": "2025-11-01T00:00:00Z",
  "source_url": "https://example.com/content/premium-widget",
  "metadata": {
    "author": "Marketing Team",
    "version": "1.2",
    "last_updated": "2025-10-15"
  }
}
```

---

## Retrieved Content Model

### Retrieval Result Schema

```python
retrieval_result_schema = {
    "query": str,                    # Original search query
    "segment": str,                  # Segment this retrieval is for
    "results": List[{
        "document_id": str,
        "title": str,
        "snippet": str,              # Extracted content snippet (150-200 words)
        "relevance_score": float,    # Search relevance score
        "reranker_score": float,     # Semantic reranker score (optional)
        "paragraph_index": int,      # Which paragraph the snippet is from
        "retrieved_at": str          # ISO datetime
    }],
    "total_results": int
}
```

### Example JSON

```json
{
  "query": "premium features high value customers",
  "segment": "High-Value Recent",
  "results": [
    {
      "document_id": "DOC001",
      "title": "Premium Widget Features",
      "snippet": "Our Premium Widget includes advanced features designed specifically for our most valued customers...",
      "relevance_score": 0.92,
      "reranker_score": 0.88,
      "paragraph_index": 2,
      "retrieved_at": "2025-11-20T10:30:00Z"
    }
  ],
  "total_results": 3
}
```

---

## Message Variant Model

### Message Variant Schema

```python
message_variant_schema = {
    "variant_id": str,               # Unique ID (e.g., "VAR001")
    "customer_id": str,              # Associated customer
    "segment": str,                  # Customer segment
    "subject": str,                  # Email subject line (max 60 chars)
    "body": str,                     # Email body (150-200 words)
    "tone": str,                     # "urgent", "informational", "friendly"
    "citations": List[{              # Source content citations
        "document_id": str,
        "title": str,
        "paragraph_index": int,
        "text_snippet": str          # Cited text
    }],
    "generation_metadata": {
        "generated_at": str,         # ISO datetime
        "model": str,                # "gpt-4"
        "tokens_input": int,
        "tokens_output": int,
        "tokens_total": int,
        "cost_usd": float,
        "prompt_template": str        # Template used
    }
}
```

### Example JSON

```json
{
  "variant_id": "VAR001",
  "customer_id": "C001",
  "segment": "High-Value Recent",
  "subject": "Exclusive: Premium Features Just for You",
  "body": "Hi [Name],\n\nAs a valued Gold member with us for over a year, we wanted to share something special with you. Our new Premium Widget features are designed specifically for customers like you who appreciate quality and innovation.\n\n[Source: Premium Widget Features, Premium Widget]\n\nYour exclusive access starts today. Discover advanced capabilities that will enhance your experience...\n\nBest regards,\nThe Team",
  "tone": "urgent",
  "citations": [
    {
      "document_id": "DOC001",
      "title": "Premium Widget Features",
      "paragraph_index": 2,
      "text_snippet": "advanced features designed specifically for valued customers"
    }
  ],
  "generation_metadata": {
    "generated_at": "2025-11-20T10:35:00Z",
    "model": "gpt-4",
    "tokens_input": 450,
    "tokens_output": 185,
    "tokens_total": 635,
    "cost_usd": 0.0245,
    "prompt_template": "generation_prompt_urgent"
  }
}
```

---

## Safety Check Model

### Safety Result Schema

```python
safety_result_schema = {
    "variant_id": str,
    "customer_id": str,
    "segment": str,
    "status": str,                   # "pass" or "block"
    "severity_scores": {
        "hate": int,                 # 0, 2, 4, or 6
        "violence": int,
        "self_harm": int,
        "sexual": int
    },
    "blocked_categories": List[str], # Categories that exceeded threshold
    "threshold_used": int,           # Policy threshold applied
    "checked_at": str,               # ISO datetime
    "block_reason": str              # Explanation if blocked (optional)
}
```

### Example JSON (Pass)

```json
{
  "variant_id": "VAR001",
  "customer_id": "C001",
  "segment": "High-Value Recent",
  "status": "pass",
  "severity_scores": {
    "hate": 0,
    "violence": 0,
    "self_harm": 0,
    "sexual": 0
  },
  "blocked_categories": [],
  "threshold_used": 4,
  "checked_at": "2025-11-20T10:36:00Z",
  "block_reason": null
}
```

### Example JSON (Block)

```json
{
  "variant_id": "VAR999",
  "customer_id": "C999",
  "segment": "At-Risk",
  "status": "block",
  "severity_scores": {
    "hate": 6,
    "violence": 0,
    "self_harm": 0,
    "sexual": 0
  },
  "blocked_categories": ["hate"],
  "threshold_used": 4,
  "checked_at": "2025-11-20T10:36:05Z",
  "block_reason": "Hate severity (6) exceeds threshold (4)"
}
```

---

## Experiment Model

### Experiment Assignment Schema

```python
experiment_assignment_schema = {
    "customer_id": str,
    "segment": str,
    "experiment_arm": str,           # "control", "treatment_1", "treatment_2", etc.
    "variant_id": str,               # Variant assigned (or "control" for control group)
    "assigned_at": str,              # ISO datetime
    "assignment_method": str         # "stratified_random"
}
```

### Example JSON

```json
{
  "customer_id": "C001",
  "segment": "High-Value Recent",
  "experiment_arm": "treatment_1",
  "variant_id": "VAR001",
  "assigned_at": "2025-11-20T10:40:00Z",
  "assignment_method": "stratified_random"
}
```

### Engagement Event Schema

```python
engagement_event_schema = {
    "customer_id": str,
    "variant_id": str,
    "experiment_arm": str,
    "opened": bool,                  # Email opened
    "clicked": bool,                 # Link clicked
    "converted": bool,               # Conversion action taken
    "engagement_at": str,            # ISO datetime
    "engagement_source": str         # "historical" or "simulated"
}
```

### Example JSON

```json
{
  "customer_id": "C001",
  "variant_id": "VAR001",
  "experiment_arm": "treatment_1",
  "opened": true,
  "clicked": true,
  "converted": false,
  "engagement_at": "2025-11-20T11:00:00Z",
  "engagement_source": "simulated"
}
```

---

## Metrics Model

### Experiment Metrics Schema

```python
experiment_metrics_schema = {
    "experiment_id": str,
    "experiment_name": str,
    "total_customers": int,
    "arms": List[{
        "arm_name": str,             # "control", "treatment_1", etc.
        "sample_size": int,
        "metrics": {
            "open_rate": float,      # 0.0-1.0
            "click_rate": float,
            "conversion_rate": float
        },
        "counts": {
            "sent": int,
            "opened": int,
            "clicked": int,
            "converted": int
        }
    }],
    "lift_analysis": List[{
        "treatment_arm": str,
        "metric": str,               # "open_rate", "click_rate", etc.
        "control_value": float,
        "treatment_value": float,
        "lift_percent": float,       # Relative lift
        "lift_absolute": float,      # Absolute difference
        "statistical_significance": {
            "p_value": float,
            "significant": bool,     # True if p < 0.05
            "confidence_interval": {
                "lower": float,
                "upper": float
            }
        }
    }],
    "segment_breakdown": List[{
        "segment": str,
        "sample_size": int,
        "best_performing_arm": str,
        "lift_percent": float
    }],
    "computed_at": str               # ISO datetime
}
```

### Example JSON

```json
{
  "experiment_id": "EXP001",
  "experiment_name": "personalization_poc_v1",
  "total_customers": 500,
  "arms": [
    {
      "arm_name": "control",
      "sample_size": 125,
      "metrics": {
        "open_rate": 0.25,
        "click_rate": 0.05,
        "conversion_rate": 0.01
      },
      "counts": {
        "sent": 125,
        "opened": 31,
        "clicked": 6,
        "converted": 1
      }
    },
    {
      "arm_name": "treatment_1",
      "sample_size": 125,
      "metrics": {
        "open_rate": 0.32,
        "click_rate": 0.08,
        "conversion_rate": 0.015
      },
      "counts": {
        "sent": 125,
        "opened": 40,
        "clicked": 10,
        "converted": 2
      }
    }
  ],
  "lift_analysis": [
    {
      "treatment_arm": "treatment_1",
      "metric": "open_rate",
      "control_value": 0.25,
      "treatment_value": 0.32,
      "lift_percent": 28.0,
      "lift_absolute": 0.07,
      "statistical_significance": {
        "p_value": 0.023,
        "significant": true,
        "confidence_interval": {
          "lower": 0.01,
          "upper": 0.13
        }
      }
    }
  ],
  "segment_breakdown": [
    {
      "segment": "High-Value Recent",
      "sample_size": 150,
      "best_performing_arm": "treatment_1",
      "lift_percent": 35.5
    }
  ],
  "computed_at": "2025-11-20T12:00:00Z"
}
```

---

## Validation Functions

### Customer Data Validation

```python
def validate_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate customer DataFrame schema and constraints."""
    required_columns = [
        'customer_id', 'age', 'location', 'tier',
        'purchase_frequency', 'avg_order_value',
        'last_engagement_days', 'historical_open_rate',
        'historical_click_rate'
    ]
    
    # Check required columns
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check uniqueness
    if df['customer_id'].duplicated().any():
        raise ValueError("Duplicate customer IDs found")
    
    # Check data types and ranges
    assert df['age'].dtype in [int, np.int64], "Age must be integer"
    assert (df['age'] >= 18).all(), "Age must be >= 18"
    assert (df['purchase_frequency'] >= 0).all(), "Purchase frequency must be non-negative"
    assert (df['avg_order_value'] >= 0).all(), "Order value must be non-negative"
    assert (df['historical_open_rate'] >= 0).all() and (df['historical_open_rate'] <= 1).all()
    assert (df['historical_click_rate'] >= 0).all() and (df['historical_click_rate'] <= 1).all()
    
    return df
```

### Content Document Validation

```python
def validate_content_document(doc: dict) -> dict:
    """Validate content document schema."""
    required_fields = ['document_id', 'title', 'category', 'content']
    
    missing = set(required_fields) - set(doc.keys())
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    # Check types
    assert isinstance(doc['document_id'], str)
    assert isinstance(doc['title'], str)
    assert isinstance(doc['content'], str)
    assert len(doc['content']) > 100, "Content too short"
    
    # Validate category
    valid_categories = ['Product', 'Promotion', 'Support', 'General']
    if doc['category'] not in valid_categories:
        raise ValueError(f"Invalid category: {doc['category']}")
    
    return doc
```

---

## Data Transformation Utilities

### Convert Segment DataFrame to JSON

```python
def segments_to_json(segments_df: pd.DataFrame) -> List[dict]:
    """Convert segment DataFrame to JSON format."""
    return segments_df.to_dict(orient='records')
```

### Convert Metrics to Report Format

```python
def format_metrics_for_report(metrics: dict) -> pd.DataFrame:
    """Format experiment metrics as DataFrame for reporting."""
    rows = []
    for arm in metrics['arms']:
        rows.append({
            'Experiment Arm': arm['arm_name'],
            'Sample Size': arm['sample_size'],
            'Open Rate': f"{arm['metrics']['open_rate']:.1%}",
            'Click Rate': f"{arm['metrics']['click_rate']:.1%}",
            'Conversion Rate': f"{arm['metrics']['conversion_rate']:.1%}"
        })
    
    return pd.DataFrame(rows)
```

---

## Storage Formats

### File Format Standards

| Data Type | Storage Format | Location |
|-----------|---------------|----------|
| Customer data | CSV | `data/raw/customers.csv` |
| Content documents | JSON (one per file) | `data/content/approved_content/*.json` |
| Segments | JSON | `data/processed/segments.json` |
| Variants | JSON | `data/processed/variants.json` |
| Assignments | JSON | `data/processed/assignments.json` |
| Safety audit | CSV | `logs/safety_audit.csv` |
| Experiment results | JSON | `data/processed/experiment_results.json` |

### JSON File Conventions

```python
import json

# Save with proper formatting
with open('data/processed/segments.json', 'w') as f:
    json.dump(segments, f, indent=2, ensure_ascii=False)

# Load
with open('data/processed/segments.json', 'r') as f:
    segments = json.load(f)
```