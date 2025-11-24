# Contributing to Customer Personalization Orchestrator

Thank you for your interest in contributing to the Customer Personalization Orchestrator! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ (recommended: 3.11)
- Git
- Azure subscription (for integration testing)
- Familiarity with Azure AI services

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/customer-personalization-orchestrator.git
   cd customer-personalization-orchestrator
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

5. **Verify Setup**
   ```bash
   pytest tests/ -v
   python scripts/test_azure_connection.py
   ```

## 🏗️ Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **hotfix/**: Critical bug fixes

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Changes**
   ```bash
   # Run tests
   pytest tests/ -v --cov=src
   
   # Check code quality
   ruff check src/ tests/
   ruff format src/ tests/
   mypy src/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new segmentation algorithm"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with modern adjustments:

- **Line length**: 100 characters (Ruff default)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all functions and classes
- **Naming**: snake_case for functions/variables, PascalCase for classes

### Code Quality Tools

```bash
# Linting and formatting (Ruff - replaces Black, Flake8, isort)
ruff check src/ tests/            # Lint
ruff format src/ tests/           # Format

# Type checking
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/

# Dependency vulnerabilities
pip-audit
```

### Example Code Style

```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MessageGenerator:
    """
    Generate personalized message variants using Azure OpenAI.
    
    This class handles the creation of personalized marketing messages
    with proper citation to approved content sources.
    
    Attributes:
        client: Azure OpenAI client instance
        config: Generation configuration dictionary
        
    Example:
        >>> generator = MessageGenerator(config)
        >>> variants = generator.generate_variants(segment, content)
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize generator with configuration."""
        self.client = get_openai_client()
        self.config = config
        self._cache: Dict[str, Any] = {}
    
    def generate_variants(
        self, 
        segment: Dict[str, Any], 
        content: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate 3 variants with different tones.
        
        Args:
            segment: Customer segment information with features
            content: List of retrieved content snippets
            
        Returns:
            List of 3 message variants with metadata
            
        Raises:
            ValueError: If segment or content is invalid
            APIError: If OpenAI API call fails
        """
        if not segment.get("name"):
            raise ValueError("Segment must have a name")
        
        variants = []
        for tone in ["urgent", "informational", "friendly"]:
            try:
                variant = self._generate_single_variant(segment, content, tone)
                variants.append(variant)
            except Exception as e:
                logger.error(f"Failed to generate {tone} variant: {e}")
                continue
        
        return variants
```

### Docstring Standards

Use Google-style docstrings:

```python
def calculate_lift(treatment_rate: float, control_rate: float) -> float:
    """
    Calculate relative lift between treatment and control.
    
    Uses the formula: lift = (treatment - control) / control * 100%
    
    Args:
        treatment_rate: Metric value for treatment arm (e.g., 0.30 = 30%)
        control_rate: Metric value for control arm (e.g., 0.25 = 25%)
        
    Returns:
        Relative lift percentage (e.g., 20.0 for 20% lift)
        
    Raises:
        ValueError: If control_rate is zero (division by zero)
        TypeError: If inputs are not numeric
        
    Example:
        >>> calculate_lift(0.30, 0.25)
        20.0
    """
    if control_rate == 0:
        raise ValueError("Control rate cannot be zero")
    return (treatment_rate - control_rate) / control_rate * 100
```

## 🧪 Testing Guidelines

### Test Organization

```
tests/
├── conftest.py                   # Pytest fixtures
├── test_segmentation.py          # Segmentation agent tests
├── test_retrieval.py             # Retrieval agent tests
├── test_generation.py            # Generation agent tests
├── test_safety.py                # Safety agent tests
├── test_experimentation.py       # Experimentation agent tests
└── test_integration.py           # End-to-end tests
```

### Writing Tests

1. **Test Naming**: `test_<function>_<scenario>_<expected>`
2. **Fixtures**: Use `conftest.py` for common test data
3. **Mocking**: Mock external dependencies (Azure APIs)
4. **Coverage**: Aim for >80% code coverage

### Example Test

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.generation_agent import generate_variants

@pytest.fixture
def sample_segment():
    return {
        "segment_id": "SEG001",
        "name": "High-Value Recent",
        "features": {
            "avg_order_value": 250.0,
            "purchase_frequency": 12
        }
    }

@pytest.fixture
def sample_content():
    return [
        {
            "document_id": "DOC001",
            "title": "Premium Features",
            "snippet": "Our premium features include..."
        }
    ]

def test_generate_variants_with_valid_input_returns_three_variants(
    sample_segment, 
    sample_content
):
    """Test that generate_variants returns 3 variants for valid input."""
    with patch('src.integrations.azure_openai.get_openai_client'):
        variants = generate_variants(sample_segment, sample_content)
        assert len(variants) == 3
        assert all('subject' in v for v in variants)
        assert all('body' in v for v in variants)

def test_generate_variants_with_empty_content_raises_error(sample_segment):
    """Test that generate_variants raises error with empty content."""
    with pytest.raises(ValueError, match="Content cannot be empty"):
        generate_variants(sample_segment, [])
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_segmentation.py -v

# Run specific test
pytest tests/test_segmentation.py::test_segment_customers_assigns_all -v
```

## 🏛️ Architecture Guidelines

### Agent Development

When creating new agents:

1. **Inherit from BaseAgent** (if available) or follow established patterns
2. **Implement required methods**: `__init__`, main processing method
3. **Add comprehensive error handling** with specific exception types
4. **Include input validation** with clear error messages
5. **Provide both class-based and convenience function APIs**

### Configuration Management

- **Externalize all configuration** to YAML files
- **Use environment variables** for secrets and endpoints
- **Validate configuration** on startup with clear error messages
- **Document all configuration options** with inline comments

### Error Handling

```python
# Custom exceptions
class CPOError(Exception):
    """Base exception for all CPO errors."""
    pass

class ConfigurationError(CPOError):
    """Raised when configuration is invalid or missing."""
    pass

class AzureAPIError(CPOError):
    """Raised when Azure API call fails."""
    def __init__(self, service: str, operation: str, message: str):
        self.service = service
        self.operation = operation
        super().__init__(f"{service}.{operation}: {message}")

# Retry logic
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_if_exception_type((ConnectionError, TimeoutError))
)
def call_azure_api(func, *args, **kwargs):
    return func(*args, **kwargs)
```

### Logging Standards

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_event(event_type: str, data: dict):
    """Log structured event in JSON format."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "data": data
    }
    logger.info(json.dumps(log_entry))

# Usage
log_event("variant_generated", {
    "variant_id": "VAR001",
    "segment": "High-Value",
    "tokens_used": 250,
    "cost_usd": 0.0075
})
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: Required for all public functions and classes
- **Type hints**: Required for all function parameters and returns
- **Inline comments**: For complex logic or business rules
- **README updates**: When adding new features or changing setup

### Documentation Files

- **README.md**: Project overview and quick start
- **ARCHITECTURE.md**: System design and technical details
- **CONTRIBUTING.md**: This file - development guidelines
- **API Documentation**: Auto-generated from docstrings

## 🔍 Code Review Process

### Before Submitting PR

- [ ] All tests pass locally
- [ ] Code coverage >80%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Security scan clean

### PR Requirements

1. **Clear Description**: What changes were made and why
2. **Test Coverage**: New functionality must have tests
3. **Documentation**: Update relevant docs
4. **Breaking Changes**: Clearly marked and justified
5. **Performance Impact**: Note any performance implications

### Review Checklist

Reviewers should check:

- [ ] Code follows style guidelines
- [ ] Tests are comprehensive and meaningful
- [ ] Error handling is appropriate
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Documentation is clear and complete

## 🐛 Bug Reports

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure bug still exists
3. **Gather relevant information** (logs, configuration, environment)

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.11.0]
- Package version: [e.g. 1.0.0]

**Additional Context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of what you want to happen.

**Use Case**
Describe the use case and why this feature would be valuable.

**Proposed Solution**
Describe how you envision this feature working.

**Alternatives Considered**
Any alternative solutions or features you've considered.

**Additional Context**
Add any other context or screenshots about the feature request.
```

## 🏷️ Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(generation): add citation extraction logic
fix(safety): handle API timeout errors correctly
docs(readme): update Azure setup instructions
test(retrieval): add integration tests for search client
```

## 🚀 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Security scan clean
- [ ] Performance regression tests pass

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Email**: [maintainer-email] for security issues

### Response Times

- **Bug reports**: 2-3 business days
- **Feature requests**: 1 week
- **Security issues**: 24 hours
- **General questions**: 3-5 business days

## 🙏 Recognition

Contributors will be recognized in:
- **README.md**: Contributors section
- **Release notes**: Major contributions highlighted
- **GitHub**: Contributor badges and statistics

Thank you for contributing to the Customer Personalization Orchestrator!

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Next Review**: Quarterly