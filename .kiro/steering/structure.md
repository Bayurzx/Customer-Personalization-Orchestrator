# Project Structure Steering

## Overview

This document defines the directory organization, file naming conventions, and structural patterns for the Customer Personalization Orchestrator project. All paths and conventions align with modern Python best practices and Azure AI integrations as of November 2025.

---

## Root Directory Structure

```
customer-personalization-orchestrator/
├── .kiro/                      # Kiro configuration and steering
├── src/                        # Source code (all Python modules)
├── data/                       # Data files (raw, processed, content)
├── config/                     # Configuration files (YAML, text)
├── notebooks/                  # Jupyter notebooks for analysis
├── tests/                      # Test suite (pytest)
├── logs/                       # Runtime logs (gitignored)
├── reports/                    # Generated reports and visualizations
├── scripts/                    # Utility and automation scripts
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template (committed)
├── .gitignore                  # Git exclusions
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Modern Python project config (optional)
├── README.md                   # Project documentation
├── ARCHITECTURE.md             # Architecture overview
└── CONTRIBUTING.md             # Development guidelines
```

---

## Detailed Directory Purposes

### `.kiro/` - Kiro Configuration

```
.kiro/
├── specs/
│   └── customer-personalization-orchestrator/
│       ├── requirements.md     # EARS-format requirements
│       ├── design.md          # Technical architecture
│       └── tasks.md           # Implementation tasks
│
├── steering/
│   ├── product.md             # Product vision and goals
│   ├── tech.md                # Tech stack and standards
│   ├── structure.md           # This file - directory conventions
│   ├── azure-services.md      # Azure integration guide (your version)
│   ├── data-models.md         # Data schemas
│   ├── api-standards.md       # API integration patterns
│   ├── security-policies.md   # Security guidelines
│   └── steps.md               # Change tracking log
│
└── hooks/
    ├── on-save-safety-check.md    # Auto-validate safety
    └── on-save-update-docs.md     # Auto-update documentation
```

**Purpose**: Kiro-specific specifications and persistent knowledge for AI-assisted development.

**Conventions**:
- All steering files in Markdown
- Specs follow three-phase structure (requirements → design → tasks)
- Update `steps.md` daily with progress

---

### `src/` - Source Code

```
src/
├── agents/
│   ├── __init__.py
│   ├── segmentation_agent.py      # Customer segmentation logic
│   ├── retrieval_agent.py         # Content retrieval (Azure AI Search)
│   ├── generation_agent.py        # Message generation (Azure OpenAI)
│   ├── safety_agent.py            # Safety enforcement (Content Safety)
│   └── experimentation_agent.py   # A/B/n orchestration
│
├── orchestrator/
│   ├── __init__.py
│   ├── pipeline.py                # Main orchestration logic
│   └── config.py                  # Configuration loader
│
├── integrations/
│   ├── __init__.py
│   ├── azure_openai.py            # Azure OpenAI client wrapper
│   ├── azure_search.py            # Azure AI Search client wrapper
│   ├── azure_content_safety.py    # Content Safety client wrapper
│   └── azure_ml.py                # Azure ML tracking (MLflow)
│
├── utils/
│   ├── __init__.py
│   ├── logging_config.py          # Structured logging setup
│   ├── data_loader.py             # Data ingestion utilities
│   ├── metrics.py                 # Metrics calculation functions
│   └── validators.py              # Input validation
│
└── main.py                        # Entry point for CLI execution
```

**Purpose**: All production Python code, organized by responsibility.

**Conventions**:
- One agent per file
- Integration modules wrap Azure services
- Utils contain pure functions (no state)
- All modules have `__init__.py` for proper imports
- Type hints required for all public functions

**Import Pattern**:
```python
# Absolute imports from project root
from src.agents.segmentation_agent import segment_customers
from src.integrations.azure_openai import get_openai_client
from src.utils.logging_config import setup_logging
```

---

### `data/` - Data Storage

```
data/
├── raw/
│   ├── customers.csv              # Sample customer dataset
│   └── historical_engagement.csv  # Historical engagement data
│
├── content/
│   └── approved_content/          # Approved marketing content
│       ├── product_001.json
│       ├── product_002.json
│       └── ...
│
└── processed/
    ├── segments.json              # Segment assignments
    ├── variants.json              # Generated message variants
    ├── assignments.json           # Experiment assignments
    └── engagement.json            # Engagement records
```

**Purpose**: All data files, separated by processing stage.

**Conventions**:
- `raw/` is read-only, never modified by pipeline
- `processed/` contains pipeline outputs
- `content/` stores approved source materials
- Add `data/raw/*.csv` to `.gitignore` if contains sensitive data
- Use ISO 8601 timestamps in filenames for versioning

**Data Formats**:
- Customer data: CSV
- Content corpus: JSON
- Pipeline outputs: JSON
- Logs: CSV (safety audit), JSON (system logs)

---

### `config/` - Configuration Files

```
config/
├── prompts/
│   ├── generation_prompt.txt     # Base generation template
│   └── variants/
│       ├── urgent.txt            # Urgent tone variant
│       ├── informational.txt     # Informational tone
│       └── friendly.txt          # Friendly tone
│
├── azure_config.yaml             # Azure service endpoints
├── safety_thresholds.yaml        # Content safety policy
└── experiment_config.yaml        # Experiment parameters
```

**Purpose**: Externalized configuration for rapid iteration.

**Conventions**:
- Prompt templates: `.txt` files (human-editable)
- Service configs: `.yaml` files (structured data)
- No secrets in config files (use `.env` or Key Vault)
- Document all config options with inline comments
- Version control all config files

**Example Azure Config**:
```yaml
# config/azure_config.yaml
azure_openai:
  endpoint: ${AZURE_OPENAI_ENDPOINT}  # From environment
  deployment_name: ${AZURE_OPENAI_DEPLOYMENT_NAME}
  api_version: "2025-11-01-preview"
  max_tokens: 1000
  temperature: 0.7

azure_search:
  endpoint: ${AZURE_SEARCH_ENDPOINT}
  index_name: ${AZURE_SEARCH_INDEX_NAME}

azure_content_safety:
  endpoint: ${AZURE_CONTENT_SAFETY_ENDPOINT}
  api_version: "2024-09-01"
```

---

### `notebooks/` - Jupyter Notebooks

```
notebooks/
├── 01_data_exploration.ipynb      # EDA and data profiling
├── 02_segmentation_analysis.ipynb # Segment quality validation
├── 03_retrieval_testing.ipynb     # Content retrieval quality
├── 04_generation_samples.ipynb    # Generation examples
├── 05_experiment_report.ipynb     # Final experiment report
└── 06_explainability.ipynb        # Feature attribution
```

**Purpose**: Interactive analysis, experimentation, and reporting.

**Conventions**:
- Number notebooks in execution order (01, 02, ...)
- Include markdown explanations and narrative
- Clear outputs before committing (optional)
- Keep notebooks focused (one topic per notebook)
- Export final report notebook to PDF for stakeholders

**Notebook Standards**:
```python
# Standard imports block at top
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Load configuration
from src.orchestrator.config import ConfigLoader
config = ConfigLoader().load_all()
```

---

### `tests/` - Test Suite

```
tests/
├── __init__.py
├── conftest.py                   # Pytest fixtures
├── test_segmentation.py          # Segmentation agent tests
├── test_retrieval.py             # Retrieval agent tests
├── test_generation.py            # Generation agent tests
├── test_safety.py                # Safety agent tests
├── test_experimentation.py       # Experiment logic tests
└── test_integration.py           # End-to-end tests
```

**Purpose**: Automated testing for quality assurance.

**Conventions**:
- One test file per agent module
- Test naming: `test_<function>_<scenario>_<expected>`
- Use fixtures for common test data (`conftest.py`)
- Mock Azure API calls in unit tests
- Integration tests use actual Azure services (test accounts)
- Aim for >70% code coverage

**Test Example**:
```python
# tests/test_segmentation.py
import pytest
from src.agents.segmentation_agent import segment_customers

@pytest.fixture
def sample_customers():
    return pd.DataFrame({
        'customer_id': ['C001', 'C002'],
        'age': [35, 28],
        'tier': ['Gold', 'Silver'],
        'purchase_frequency': [12, 6]
    })

def test_segment_customers_assigns_all(sample_customers):
    segments = segment_customers(sample_customers)
    assert len(segments) == len(sample_customers)
    assert segments['segment'].notna().all()
```

---

### `logs/` - Runtime Logs

```
logs/
├── safety_audit.log              # Safety check audit trail (CSV)
├── experiment.log                # Experiment execution log (JSON)
└── system.log                    # General system logs (JSON)
```

**Purpose**: Runtime logging output for debugging and compliance.

**Conventions**:
- Add entire `logs/` directory to `.gitignore`
- Use structured JSON logging for `system.log`
- Use CSV format for `safety_audit.log` (compliance)
- Implement log rotation for production (not needed for POC)
- Never log PII or secrets

**Safety Audit Log Format**:
```csv
timestamp,variant_id,segment,status,hate,violence,self_harm,sexual,block_reason
2025-11-21T10:00:00Z,VAR001,High-Value,pass,0,0,0,0,
2025-11-21T10:00:05Z,VAR002,At-Risk,block,6,2,0,0,Hate severity above threshold
```

---

### `reports/` - Generated Reports

```
reports/
├── experiment_report.pdf         # Final experiment report
├── safety_audit_report.csv       # Safety screening summary
└── visualizations/               # Charts and graphs
    ├── lift_by_segment.png
    ├── safety_distribution.png
    └── feature_importance.png
```

**Purpose**: Final deliverables and visualizations.

**Conventions**:
- Generated files (not source controlled, optional)
- Include both PDF and source notebooks
- Visualizations saved as PNG or SVG
- Use descriptive filenames with dates if versioning

---

### `scripts/` - Utility Scripts

```
scripts/
├── setup_azure_resources.py      # Azure resource provisioning
├── index_content.py              # Index content to Azure AI Search
├── run_experiment.py             # Execute full pipeline
└── generate_report.py            # Export notebook to PDF
```

**Purpose**: Standalone executable scripts for automation.

**Conventions**:
- Entry point scripts for common tasks
- Include `if __name__ == "__main__":` guard
- Use `argparse` for CLI arguments
- Document usage in script docstring
- Make scripts idempotent where possible

**Script Template**:
```python
#!/usr/bin/env python3
"""
Script: run_experiment.py
Purpose: Execute the full personalization experiment pipeline.

Usage:
    python scripts/run_experiment.py --config config/experiment_config.yaml
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.pipeline import PersonalizationPipeline

def main():
    parser = argparse.ArgumentParser(description="Run experiment pipeline")
    parser.add_argument("--config", required=True, help="Path to experiment config")
    args = parser.parse_args()
    
    # Execute pipeline
    pipeline = PersonalizationPipeline(args.config)
    results = pipeline.run()
    
    print(f"✅ Experiment complete: {results['experiment_id']}")

if __name__ == "__main__":
    main()
```

---

## File Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `segmentation_agent.py`)
- **Classes**: `PascalCase` (e.g., `ContentRetriever`)
- **Functions**: `snake_case` (e.g., `generate_variant()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS = 1000`)
- **Private functions**: `_snake_case` (e.g., `_normalize_features()`)

### Configuration Files
- **YAML**: `snake_case.yaml` (e.g., `experiment_config.yaml`)
- **Text/Templates**: `snake_case.txt` (e.g., `generation_prompt.txt`)
- **Environment**: `.env` (no variations)

### Data Files
- **CSV**: `snake_case.csv` (e.g., `customer_segments.csv`)
- **JSON**: `snake_case.json` (e.g., `approved_content.json`)
- **Timestamps**: ISO 8601 format (`2025-11-21T10:00:00Z`)

### Notebooks
- **Format**: `##_descriptive_name.ipynb` (e.g., `01_data_exploration.ipynb`)
- **Numbering**: Two digits, execution order

### Reports
- **PDFs**: `descriptive_name_report.pdf` (e.g., `experiment_report.pdf`)
- **Images**: `descriptive_name.png` (e.g., `lift_by_segment.png`)

---

## Python Code Organization Standards

### Module Structure

```python
"""
Module: generation_agent.py
Purpose: Generate personalized message variants using Azure OpenAI.

This module implements the Generation Agent responsible for creating
message variants with citations to approved content.
"""

# Standard library imports
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Third-party imports
import pandas as pd
from openai import AzureOpenAI

# Local imports
from src.integrations.azure_openai import get_openai_client
from src.utils.validators import validate_variant_format

# Module-level constants
MAX_TOKENS = 1000
TEMPERATURE = 0.7
VARIANT_TONES = ["urgent", "informational", "friendly"]

# Logger configuration
logger = logging.getLogger(__name__)

# Public API functions
def generate_variants(segment: Dict, content: List[Dict]) -> List[Dict]:
    """Generate message variants for a segment."""
    pass

# Private helper functions
def _build_prompt(segment: Dict, content: List[Dict], tone: str) -> str:
    """Build generation prompt (private helper)."""
    pass
```

### Class Organization

```python
class MessageGenerator:
    """
    Generate personalized message variants using Azure OpenAI.
    
    Attributes:
        client: Azure OpenAI client instance
        config: Generation configuration dict
        
    Example:
        >>> generator = MessageGenerator(config)
        >>> variants = generator.generate_variants(segment, content)
    """
    
    def __init__(self, config: Dict):
        """Initialize generator with configuration."""
        self.client = get_openai_client()
        self.config = config
        self._cache = {}  # Private attribute
    
    def generate_variants(self, segment: Dict, content: List[Dict]) -> List[Dict]:
        """Generate variants (public method)."""
        pass
    
    def _build_prompt(self, segment: Dict, tone: str) -> str:
        """Build prompt from template (private method)."""
        pass
```

---

## Environment Configuration

### `.env` File Structure

```bash
# .env (NEVER commit this file)

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_API_VERSION=2025-11-01-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_INDEX_NAME=approved-content-index

# Azure AI Content Safety
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# Azure Machine Learning (Optional)
AZURE_ML_SUBSCRIPTION_ID=<guid>
AZURE_ML_RESOURCE_GROUP=rg-personalization-poc
AZURE_ML_WORKSPACE_NAME=ml-personalization-poc

# Azure Monitor (Optional)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>

# Azure Key Vault (Optional)
AZURE_KEY_VAULT_URL=https://kv-cpo-poc.vault.azure.net/
```

### `.env.example` Template

```bash
# .env.example (Commit this file as template)

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_API_VERSION=2025-11-01-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<service-name>.search.windows.net
AZURE_SEARCH_INDEX_NAME=approved-content-index

# Azure AI Content Safety
AZURE_CONTENT_SAFETY_ENDPOINT=https://<resource-name>.cognitiveservices.azure.com/

# Instructions: Copy this to .env and fill in your values
```

---

## Version Control Patterns

### `.gitignore` (Essential Entries)

```
# Environment
.env
.env.local
*.env

# Azure
.azure/

# Data (if sensitive)
data/raw/*.csv
data/processed/*.json

# Logs
logs/
*.log

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.mypy_cache/
*.egg-info/
dist/
build/

# IDE
.vscode/settings.json
.vscode/.ropeproject
.idea/
*.swp
*.swo

# Notebooks
.ipynb_checkpoints/
*-checkpoint.ipynb

# OS
.DS_Store
Thumbs.db

# Reports (optional - comment out if you want to version)
# reports/*.pdf
# reports/visualizations/*.png
```

### Git Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code formatting (no logic change)
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance tasks

Examples:
feat(generation): add citation extraction logic
fix(safety): handle API timeout errors correctly
docs(readme): update Azure setup instructions
test(retrieval): add integration tests for search client
```

---

## Quality Gates

### Pre-Commit Checklist
- [ ] All tests pass (`pytest`)
- [ ] Code coverage >70% (`pytest --cov`)
- [ ] No linting errors (`ruff check`)
- [ ] Code formatted (`ruff format` or `black`)
- [ ] No type errors (`mypy`)
- [ ] No secrets in code (`detect-secrets`)
- [ ] Documentation updated
- [ ] `.env.example` updated if new vars added

### Code Quality Commands

```bash
# Format code
ruff format src/ tests/
# Or use black
black src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/ --ignore-missing-imports

# Run tests
pytest tests/ -v --cov=src --cov-report=html

# Security scan
bandit -r src/
```

---

## Maintenance Schedule

### Daily (During POC Week)
- Review and update `steps.md`
- Check log files for errors
- Monitor Azure costs (portal)

### Weekly (Post-POC)
- Review and merge dependency updates
- Check for security vulnerabilities (`pip-audit`)
- Update documentation as needed

### Monthly (Production)
- Dependency updates (`pip list --outdated`)
- Security audit (`bandit`)
- Performance profiling
- Technical debt review

---

## Modern Python Project Setup (Optional)

### Using `pyproject.toml` (Recommended for Python 3.11+)

```toml
# pyproject.toml
[project]
name = "customer-personalization-orchestrator"
version = "0.1.0"
description = "AI-powered customer personalization system"
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "openai>=1.55.0",
    "azure-identity>=1.19.0",
    "azure-search-documents>=11.6.0",
    "azure-ai-contentsafety>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

---

## Contact & Support

**Project Structure Owner**: [Your Name]  
**Repository**: [GitHub URL]  
**Documentation**: See `.kiro/specs/` and `.kiro/steering/`  
**Questions**: [Team Slack / Email]

---

**Last Updated**: November 21, 2025  
**Next Review**: End of POC Week  
**Document Owner**: Technical Lead