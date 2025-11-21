# Customer Personalization Orchestrator - Complete Project Structure

```
customer-personalization-orchestrator/
│
├── .kiro/
│   ├── specs/
│   │   └── customer-personalization-orchestrator/
│   │       ├── requirements.md          # User stories with EARS notation
│   │       ├── design.md                # Technical architecture & sequence diagrams
│   │       └── tasks.md                 # Granular implementation tasks
│   │
│   ├── steering/
│   │   ├── product.md                   # Product vision and objectives
│   │   ├── tech.md                      # Technology stack and tools
│   │   ├── structure.md                 # Project organization and conventions
│   │   ├── azure-services.md            # Azure-specific configurations
│   │   ├── data-models.md               # Data schemas and structures
│   │   ├── api-standards.md             # API design and integration patterns
│   │   ├── security-policies.md         # Security and compliance guidelines
│   │   └── steps.md                     # Change tracking and progress log
│   │
│   └── hooks/
│       ├── on-save-safety-check.md      # Auto-validate safety on content save
│       └── on-save-update-docs.md       # Auto-update documentation
│
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── segmentation_agent.py        # Customer segmentation logic
│   │   ├── retrieval_agent.py           # Content retrieval from Azure Search
│   │   ├── generation_agent.py          # Message variant generation
│   │   ├── safety_agent.py              # Safety policy enforcement
│   │   └── experimentation_agent.py     # A/B/n experiment orchestration
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── pipeline.py                  # Main orchestration pipeline
│   │   └── config.py                    # Configuration management
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── azure_openai.py              # Azure OpenAI client
│   │   ├── azure_search.py              # Azure Cognitive Search client
│   │   ├── azure_content_safety.py      # Azure Content Safety client
│   │   └── azure_ml.py                  # Azure ML tracking (optional)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_config.py            # Structured logging setup
│   │   ├── data_loader.py               # Data ingestion utilities
│   │   ├── metrics.py                   # Metrics calculation
│   │   └── validators.py                # Input validation
│   │
│   └── main.py                          # Entry point for orchestration
│
├── data/
│   ├── raw/
│   │   ├── customers.csv                # Sample customer dataset
│   │   └── historical_engagement.csv    # Historical engagement data
│   │
│   ├── content/
│   │   └── approved_content/            # Approved marketing content
│   │       ├── product_001.json
│   │       ├── product_002.json
│   │       └── ...
│   │
│   └── processed/
│       ├── segments.json                # Processed segment assignments
│       ├── variants.json                # Generated message variants
│       └── assignments.json             # Experiment assignments
│
├── config/
│   ├── prompts/
│   │   ├── segmentation_prompt.txt      # Segmentation prompt template
│   │   ├── generation_prompt.txt        # Message generation template
│   │   └── variants/
│   │       ├── urgent.txt               # Urgent tone variant
│   │       ├── informational.txt        # Informational tone variant
│   │       └── friendly.txt             # Friendly tone variant
│   │
│   ├── experiment_config.yaml           # Experiment parameters
│   ├── safety_thresholds.yaml           # Safety policy thresholds
│   └── azure_config.yaml                # Azure service configurations
│
├── notebooks/
│   ├── 01_data_exploration.ipynb        # EDA and data profiling
│   ├── 02_segmentation_analysis.ipynb   # Segment quality validation
│   ├── 03_retrieval_testing.ipynb       # Content retrieval testing
│   ├── 04_generation_samples.ipynb      # Message generation examples
│   ├── 05_experiment_report.ipynb       # Final experiment report
│   └── 06_explainability.ipynb          # Feature attribution analysis
│
├── tests/
│   ├── __init__.py
│   ├── test_segmentation.py             # Segmentation agent tests
│   ├── test_retrieval.py                # Retrieval agent tests
│   ├── test_generation.py               # Generation agent tests
│   ├── test_safety.py                   # Safety agent tests
│   ├── test_experimentation.py          # Experiment logic tests
│   └── test_integration.py              # End-to-end integration tests
│
├── logs/
│   ├── safety_audit.log                 # Safety check audit trail
│   ├── experiment.log                   # Experiment execution log
│   └── system.log                       # General system logs
│
├── reports/
│   ├── experiment_report.pdf            # Final experiment report
│   ├── safety_audit_report.csv          # Safety screening results
│   └── visualizations/                  # Charts and graphs
│       ├── lift_by_segment.png
│       ├── safety_distribution.png
│       └── feature_importance.png
│
├── scripts/
│   ├── setup_azure_resources.py         # Azure resource provisioning
│   ├── index_content.py                 # Index content to Azure Search
│   ├── run_experiment.py                # Execute full experiment pipeline
│   └── generate_report.py               # Generate final report
│
├── .env.example                         # Environment variables template
├── .gitignore                           # Git ignore patterns
├── requirements.txt                     # Python dependencies
├── setup.py                             # Package setup
├── README.md                            # Project documentation
├── ARCHITECTURE.md                      # Architecture documentation
└── CONTRIBUTING.md                      # Contribution guidelines
```

## Key Directory Descriptions

### `.kiro/` - Kiro Configuration
- **specs/**: Contains structured specifications following Kiro's three-phase workflow
- **steering/**: Persistent knowledge files that guide Kiro's behavior
- **hooks/**: Automated agent tasks triggered by events

### `src/` - Source Code
- **agents/**: Individual agent modules (segmentation, retrieval, generation, safety, experimentation)
- **orchestrator/**: Main pipeline logic and configuration
- **integrations/**: Azure service clients and API wrappers
- **utils/**: Shared utilities and helpers

### `data/` - Data Storage
- **raw/**: Original datasets (customers, engagement history)
- **content/**: Approved marketing content corpus
- **processed/**: Processed outputs (segments, variants, assignments)

### `config/` - Configuration Files
- **prompts/**: Prompt templates for generation
- **experiment_config.yaml**: A/B/n experiment parameters
- **safety_thresholds.yaml**: Content safety thresholds
- **azure_config.yaml**: Azure service endpoints and settings

### `notebooks/` - Jupyter Notebooks
- Exploratory data analysis
- Agent testing and validation
- Final experiment reporting

### `tests/` - Test Suite
- Unit tests for each agent
- Integration tests for end-to-end workflow

### `logs/` - Logging Output
- Safety audit trail
- Experiment execution logs
- System logs

### `reports/` - Deliverables
- Final experiment report
- Safety audit report
- Visualizations

### `scripts/` - Utility Scripts
- Azure resource setup
- Content indexing
- Experiment execution
- Report generation

## File Naming Conventions

- **Python modules**: `snake_case.py`
- **Configuration files**: `kebab-case.yaml` or `snake_case.yaml`
- **Notebooks**: `##_descriptive_name.ipynb` (numbered for sequence)
- **Steering files**: `kebab-case.md`
- **Data files**: `snake_case.csv` or `snake_case.json`

## Architecture Principles

1. **Modularity**: Each agent is independent and testable
2. **Configuration-driven**: Prompts, thresholds, and parameters in config files
3. **Azure-native**: Leverage Azure services for scalability
4. **Observability**: Structured logging and audit trails
5. **Reproducibility**: Version-controlled prompts and configurations