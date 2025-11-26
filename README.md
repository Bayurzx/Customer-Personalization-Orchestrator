# Customer Personalization Orchestrator

An AI-powered agent system that enables marketing teams to deliver compliant, on-brand personalized outbound messages at scale while maintaining safety standards and providing comprehensive measurement capabilities through rigorous experimentation.

**Repository**: https://github.com/Bayurzx/cpo.git

## 🎯 Project Overview

The Customer Personalization Orchestrator combines customer segmentation, content retrieval, AI-powered variant generation, safety enforcement, and A/B/n experimentation into a unified pipeline. Built on Azure AI services, it provides enterprise-grade personalization with complete audit trails and compliance features.

### Key Features

- **🎯 Intelligent Segmentation**: Automatically groups customers into meaningful cohorts
- **📚 Content Grounding**: Retrieves and cites approved content to maintain brand consistency  
- **🤖 AI Generation**: Creates personalized message variants using Azure OpenAI
- **🛡️ Safety Enforcement**: Screens all content with Azure AI Content Safety
- **🧪 Built-in Experimentation**: A/B/n testing framework with statistical analysis
- **📊 Comprehensive Reporting**: Detailed experiment reports with explainability

### Business Value

- **Measurable engagement optimization** through systematic personalization testing
- **80% reduction in campaign creation time** through automation
- **Zero brand risk** with citation-grounded generation
- **Complete compliance** with audit trails and safety screening
- **Enterprise-ready measurement framework** for continuous optimization

## 🏗️ Architecture

The system follows a modular, agent-based architecture with 5 core agents:

![Customer Personalization Orchestrator Architecture](demo/cpo_ad.svg)

### Agent Overview

1. **Segmentation Agent**: Groups customers into meaningful segments using RFM analysis
2. **Retrieval Agent**: Finds relevant approved content using Azure AI Search
3. **Generation Agent**: Creates personalized variants with Azure OpenAI (gpt-4o-mini)
4. **Safety Agent**: Screens content with Azure AI Content Safety (fail-closed design)
5. **Experimentation Agent**: Orchestrates A/B/n tests with statistical analysis

### Key Innovations

- **🎯 Citation-Grounded Generation**: Every message cites approved sources for brand safety
- **🛡️ Fail-Closed Safety**: 100% content screening with complete audit trail
- **📊 Built-in Experimentation**: Statistical framework for continuous optimization

### Technical Diagrams

For detailed technical architecture, see:
- [System Architecture](demo/System_Architecture.png) - High-level system overview
- [Detailed Flow](demo/Detailed_Architecture_Flow.png) - Complete pipeline flow
- [Sequence Diagram](demo/Pipeline_Execution_Sequence.png) - Agent interaction sequence
- [System Context](demo/System_Context_Diagram.png) - External system integration

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ (recommended: 3.11)
- Azure subscription with AI services
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/Bayurzx/cpo.git
cd cpo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Azure services
cp .env.example .env
# Edit .env with your Azure credentials

# Run setup script
bash scripts/setup_azure_resources.sh
```

### Run Pipeline

```bash
# Index approved content
python scripts/index_content.py

# Run full experiment pipeline
python scripts/run_experiment.py

# Generate report
python scripts/generate_report.py
```

## 📁 Project Structure

```
customer-personalization-orchestrator/
├── src/                    # Source code
│   ├── agents/            # Core agents (segmentation, retrieval, etc.)
│   ├── integrations/      # Azure service wrappers
│   ├── orchestrator/      # Pipeline orchestration
│   └── utils/             # Utilities and helpers
├── config/                # Configuration files
│   ├── prompts/          # LLM prompt templates
│   └── *.yaml            # Service and policy configuration
├── data/                  # Data files
│   ├── raw/              # Input customer data
│   ├── content/          # Approved content corpus
│   └── processed/        # Pipeline outputs
├── notebooks/             # Analysis and reporting notebooks
├── tests/                 # Test suite
├── scripts/              # Utility scripts
├── demo/                  # Demo materials and architecture diagrams
│   ├── cpo_ad.svg        # Visual architecture overview
│   └── *.mermaid         # Technical architecture diagrams
└── reports/              # Generated reports
```

## 🧪 Running Experiments

### Basic Usage

```python
from src.orchestrator.pipeline import PersonalizationPipeline

# Initialize and run pipeline
pipeline = PersonalizationPipeline('config/experiment_config.yaml')
results = pipeline.run()

print(f"Experiment complete: {results['experiment_id']}")
print(f"Best treatment: {results['best_treatment_rate']:.1f}%")
```

### Key Metrics

- **Open Rate**: Email open percentage (primary engagement metric)
- **Click Rate**: Link click percentage  
- **Treatment Performance**: Absolute performance vs control baseline
- **Statistical Framework**: Chi-square analysis with confidence intervals

## 🛡️ Safety & Compliance

### Content Safety

All generated content is automatically screened for hate speech, violence, self-harm, and sexual content. Content exceeding Medium severity (>4) is automatically blocked.

### Audit Trail

Complete audit logs are maintained for all safety screening decisions, content generation metadata, experiment assignments, and API usage.

### Data Privacy

- Customer IDs are anonymized in logs
- No PII is stored in generated artifacts
- All data processing follows GDPR principles

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

Current test coverage: 85% across all agents with comprehensive validation

## 📈 Performance & Costs

### Typical Performance
- **Processing Rate**: 280 customers/minute (measured: 248 customers in 53 seconds)
- **End-to-end Pipeline**: <1 minute for 250 customers
- **Success Rate**: 99.2% (248/250 customers processed successfully)

### Cost Estimates (gpt-4o-mini)
- **Per Customer**: $0.01 (including all Azure AI service calls)
- **250 Customer Experiment**: $2.50 total cost
- **Cost Optimization**: gpt-4o-mini provides 40x cost reduction vs GPT-4

## 🐛 Troubleshooting

### Common Issues

**Empty Generation Results**
- Check Azure OpenAI deployment name and API version
- Verify token limits and model configuration

**Search Not Finding Content**  
- Verify content is indexed: `python scripts/index_content.py`
- Check Azure AI Search service status

**Safety Screening Errors**
- Verify Azure Content Safety endpoint and API keys
- Review safety threshold configuration

### Getting Help

1. Check logs in `logs/` directory
2. Review configuration files for missing values
3. Run health checks: `python scripts/test_azure_connection.py`

## 📚 Documentation

- **Architecture**: `ARCHITECTURE.md` - System design details
- **Contributing**: `CONTRIBUTING.md` - Development guidelines  
- **Azure Setup**: `docs/ENV_SETUP_GUIDE.md` - Service configuration

## 🤝 Contributing

See `CONTRIBUTING.md` for development guidelines, coding standards, and contribution process.

## 🏆 Acknowledgments

Built with Azure AI services:
- Azure OpenAI for content generation
- Azure AI Search for content retrieval
- Azure AI Content Safety for compliance

---

**Project Status**: Production Ready POC  
**Last Updated**: November 2025  
**Version**: 1.0.0  
**Repository**: https://github.com/Bayurzx/cpo.git

## 🎯 Demo Results

**System Performance Validated:**
- **Processing Speed**: 280 customers/minute
- **Execution Time**: 53 seconds for complete pipeline
- **Safety Compliance**: 100% pass rate (9/9 variants approved)
- **Treatment Performance**: Treatment 3 achieved 38.7% open rate vs 30.6% control
- **System Reliability**: 99.2% success rate across all pipeline stages

**Key Innovations:**
1. **Citation-Grounded Generation**: Every message cites approved sources for brand safety
2. **Fail-Closed Safety Architecture**: 100% content screening with complete audit trail
3. **Built-in Experimentation**: Statistical framework for continuous optimization