#!/usr/bin/env bash

# Create all directories
mkdir -p .kiro/specs/customer-personalization-orchestrator
mkdir -p .kiro/steering
mkdir -p .kiro/hooks

mkdir -p src/agents
mkdir -p src/orchestrator
mkdir -p src/integrations
mkdir -p src/utils

mkdir -p data/raw
mkdir -p data/content/approved_content
mkdir -p data/processed

mkdir -p config/prompts/variants

mkdir -p notebooks
mkdir -p tests
mkdir -p logs
mkdir -p reports/visualizations
mkdir -p scripts

# Create specification files
touch .kiro/specs/customer-personalization-orchestrator/requirements.md
touch .kiro/specs/customer-personalization-orchestrator/design.md
touch .kiro/specs/customer-personalization-orchestrator/tasks.md

# Create steering files
touch .kiro/steering/product.md
touch .kiro/steering/tech.md
touch .kiro/steering/structure.md
touch .kiro/steering/azure-services.md
touch .kiro/steering/data-models.md
touch .kiro/steering/api-standards.md
touch .kiro/steering/security-policies.md
touch .kiro/steering/steps.md

# Create hook files
touch .kiro/hooks/on-save-safety-check.md
touch .kiro/hooks/on-save-update-docs.md

# Source module files
touch src/agents/__init__.py
touch src/agents/segmentation_agent.py
touch src/agents/retrieval_agent.py
touch src/agents/generation_agent.py
touch src/agents/safety_agent.py
touch src/agents/experimentation_agent.py

touch src/orchestrator/__init__.py
touch src/orchestrator/pipeline.py
touch src/orchestrator/config.py

touch src/integrations/__init__.py
touch src/integrations/azure_openai.py
touch src/integrations/azure_search.py
touch src/integrations/azure_content_safety.py
touch src/integrations/azure_ml.py

touch src/utils/__init__.py
touch src/utils/logging_config.py
touch src/utils/data_loader.py
touch src/utils/metrics.py
touch src/utils/validators.py

touch src/main.py

# Data files
touch data/raw/customers.csv
touch data/raw/historical_engagement.csv

touch data/content/approved_content/product_001.json
touch data/content/approved_content/product_002.json

touch data/processed/segments.json
touch data/processed/variants.json
touch data/processed/assignments.json

# Config files
touch config/prompts/segmentation_prompt.txt
touch config/prompts/generation_prompt.txt
touch config/prompts/variants/urgent.txt
touch config/prompts/variants/informational.txt
touch config/prompts/variants/friendly.txt

touch config/experiment_config.yaml
touch config/safety_thresholds.yaml
touch config/azure_config.yaml

# Notebooks
touch notebooks/01_data_exploration.ipynb
touch notebooks/02_segmentation_analysis.ipynb
touch notebooks/03_retrieval_testing.ipynb
touch notebooks/04_generation_samples.ipynb
touch notebooks/05_experiment_report.ipynb
touch notebooks/06_explainability.ipynb

# Tests
touch tests/__init__.py
touch tests/test_segmentation.py
touch tests/test_retrieval.py
touch tests/test_generation.py
touch tests/test_safety.py
touch tests/test_experimentation.py
touch tests/test_integration.py

# Logs
touch logs/safety_audit.log
touch logs/experiment.log
touch logs/system.log

# Reports
touch reports/experiment_report.pdf
touch reports/safety_audit_report.csv
touch reports/visualizations/lift_by_segment.png
touch reports/visualizations/safety_distribution.png
touch reports/visualizations/feature_importance.png

# Scripts
touch scripts/setup_azure_resources.py
touch scripts/index_content.py
touch scripts/run_experiment.py
touch scripts/generate_report.py

# Root files
touch .env.example
touch .gitignore
touch requirements.txt
touch setup.py
touch README.md
touch ARCHITECTURE.md
touch CONTRIBUTING.md

echo "Project structure successfully created."
