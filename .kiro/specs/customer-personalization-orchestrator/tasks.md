# Implementation Tasks: Customer Personalization Orchestrator

## Task Overview

This document outlines the discrete, trackable implementation tasks for building the Customer Personalization Orchestrator MVP. Tasks are organized by day and priority, with clear acceptance criteria and dependencies.

**Total Duration**: 5 days  
**Methodology**: Incremental delivery with daily milestones

---

## Day 1: Environment Setup & Segmentation

### Task 1.1: Project Environment Setup
**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: None

**Description**: Set up development environment, Azure resources, and project structure.

**Subtasks**:
- [ ] 1.1.1: Create Python virtual environment with Python 3.9+
- [ ] 1.1.2: Install dependencies from `requirements.txt`
- [ ] 1.1.3: Create `.env` file with Azure credentials
- [ ] 1.1.4: Initialize project directory structure (`.kiro/`, `src/`, `config/`, `data/`, `logs/`)
- [ ] 1.1.5: Set up Git repository with `.gitignore`

**Acceptance Criteria**:
- Python environment activates without errors
- All dependencies install successfully
- Azure credentials configured and tested
- Directory structure matches design document
- Git initialized with first commit

**Validation**:
```bash
python --version  # Should show 3.9+
pip list | grep azure  # Should show azure-* packages
python -c "from azure.identity import DefaultAzureCredential; DefaultAzureCredential()"
```

---

### Task 1.2: Azure Resource Provisioning
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.1

**Description**: Provision and configure required Azure services.

**Subtasks**:
- [ ] 1.2.1: Create Azure OpenAI resource and deploy GPT-4 model
- [ ] 1.2.2: Create Azure Cognitive Search service
- [ ] 1.2.3: Create Azure AI Content Safety resource
- [ ] 1.2.4: Configure authentication (Managed Identity or API keys)
- [ ] 1.2.5: Test connectivity to all services
- [ ] 1.2.6: Document endpoints in `config/azure_config.yaml`

**Acceptance Criteria**:
- All Azure resources created in same resource group
- API keys or Managed Identity configured
- Test API calls succeed for each service
- Configuration file complete and validated

**Validation**:
```python
from src.integrations.azure_openai import test_connection
test_connection()  # Should return "Connection successful"
```

---

### Task 1.3: Sample Data Preparation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.1

**Description**: Create or load sample customer dataset and approved content.

**Subtasks**:
- [ ] 1.3.1: Load or generate sample customer dataset (100-500 records)
- [ ] 1.3.2: Validate dataset schema (required columns present)
- [ ] 1.3.3: Create 20-50 approved content documents (JSON format)
- [ ] 1.3.4: Validate content document schema
- [ ] 1.3.5: Perform basic EDA in `notebooks/01_data_exploration.ipynb`

**Acceptance Criteria**:
- Customer dataset has 100-500 records with all required fields
- Content corpus has 20-50 documents with metadata
- No missing values in critical fields
- EDA notebook runs without errors

**Validation**:
```python
import pandas as pd
df = pd.read_csv('data/raw/customers.csv')
assert len(df) >= 100
assert 'customer_id' in df.columns
```

---

### Task 1.4: Segmentation Agent Implementation
**Priority**: P0 (Blocker)  
**Estimated Time**: 2.5 hours  
**Dependencies**: Task 1.3

**Description**: Implement customer segmentation using rule-based or clustering approach.

**Subtasks**:
- [ ] 1.4.1: Create `src/agents/segmentation_agent.py` module
- [ ] 1.4.2: Implement `load_customer_data()` function
- [ ] 1.4.3: Implement rule-based segmentation logic (RFM or similar)
- [ ] 1.4.4: Alternative: Implement K-means clustering segmentation
- [ ] 1.4.5: Implement `generate_segment_summary()` function
- [ ] 1.4.6: Add segment label mapping (e.g., "High-Value Recent")
- [ ] 1.4.7: Write unit tests in `tests/test_segmentation.py`

**Acceptance Criteria**:
- Segments all customers into 3-5 distinct groups
- Each customer assigned exactly one segment
- Segment labels are human-readable
- Segment summary includes size and key features
- Unit tests pass with >80% coverage

**Validation**:
```python
from src.agents.segmentation_agent import segment_customers
segments = segment_customers('data/raw/customers.csv')
assert len(segments['segment'].unique()) >= 3
assert segments['customer_id'].is_unique
```

---

### Task 1.5: Segmentation Analysis & Validation
**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.4

**Description**: Analyze segment quality and document findings.

**Subtasks**:
- [ ] 1.5.1: Create `notebooks/02_segmentation_analysis.ipynb`
- [ ] 1.5.2: Visualize segment distribution
- [ ] 1.5.3: Calculate segment statistics (mean, median per feature)
- [ ] 1.5.4: Validate segments are balanced (no segment <10% of total)
- [ ] 1.5.5: Document segment definitions in notebook

**Acceptance Criteria**:
- Segment distribution visualized (bar chart)
- Statistical summary table generated
- All segments have >10% of customers
- Segment definitions documented

**Day 1 Deliverable**: ✅ Segmented customer dataset with 3-5 labeled groups

---

## Day 2: Content Retrieval & Indexing

### Task 2.1: Azure Cognitive Search Index Setup
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2, Task 1.3

**Description**: Create search index and define schema for content documents.

**Subtasks**:
- [ ] 2.1.1: Create `src/integrations/azure_search.py` module
- [ ] 2.1.2: Define index schema (fields, types, searchable/filterable)
- [ ] 2.1.3: Create index in Azure Cognitive Search
- [ ] 2.1.4: Configure semantic search settings
- [ ] 2.1.5: Write `index_documents()` function
- [ ] 2.1.6: Write unit tests for search client

**Acceptance Criteria**:
- Index created with correct schema
- All fields properly configured (searchable, filterable, facetable)
- Semantic search enabled
- Test documents can be indexed successfully

**Validation**:
```python
from src.integrations.azure_search import create_index, index_exists
create_index("approved-content")
assert index_exists("approved-content") == True
```

---

### Task 2.2: Content Indexing Pipeline
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 2.1

**Description**: Index all approved content documents into Azure Search.

**Subtasks**:
- [ ] 2.2.1: Create `scripts/index_content.py` script
- [ ] 2.2.2: Read all content documents from `data/content/approved_content/`
- [ ] 2.2.3: Transform documents to match index schema
- [ ] 2.2.4: Batch index documents (batches of 100)
- [ ] 2.2.5: Add progress bar with `tqdm`
- [ ] 2.2.6: Log indexing statistics (count, errors)

**Acceptance Criteria**:
- All 20-50 documents successfully indexed
- No indexing errors logged
- Index statistics reported (document count)
- Script is idempotent (can re-run safely)

**Validation**:
```bash
python scripts/index_content.py
# Output: "Indexed 50 documents successfully. 0 errors."
```

---

### Task 2.3: Retrieval Agent Implementation
**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 2.2

**Description**: Implement content retrieval logic for segment-based queries.

**Subtasks**:
- [ ] 2.3.1: Create `src/agents/retrieval_agent.py` module
- [ ] 2.3.2: Implement `construct_query_from_segment()` function
- [ ] 2.3.3: Implement `retrieve_content()` function with Azure Search client
- [ ] 2.3.4: Implement `extract_snippet()` function (200-word limit)
- [ ] 2.3.5: Add relevance score filtering (threshold: >0.5)
- [ ] 2.3.6: Add logging for all queries and results
- [ ] 2.3.7: Write unit tests in `tests/test_retrieval.py`

**Acceptance Criteria**:
- Returns top 3-5 most relevant documents per query
- Snippets extracted with correct length
- Source metadata included (document_id, title, paragraph_index)
- Query construction uses segment features
- Unit tests pass with mocked search results

**Validation**:
```python
from src.agents.retrieval_agent import retrieve_content
segment = {"name": "High-Value", "features": {"tier": "Gold"}}
results = retrieve_content(segment, top_k=5)
assert len(results) <= 5
assert all('document_id' in r for r in results)
```

---

### Task 2.4: Retrieval Quality Testing
**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 2.3

**Description**: Test retrieval quality across different segment types.

**Subtasks**:
- [ ] 2.4.1: Create `notebooks/03_retrieval_testing.ipynb`
- [ ] 2.4.2: Test retrieval for each segment type
- [ ] 2.4.3: Visualize relevance scores distribution
- [ ] 2.4.4: Manually review top 3 results per segment for quality
- [ ] 2.4.5: Document any retrieval issues or improvements needed

**Acceptance Criteria**:
- Retrieval tested for all 3-5 segments
- Relevance scores visualized
- Manual quality review documented
- At least 80% of retrieved content relevant to segment

**Day 2 Deliverable**: ✅ Functional content retrieval with indexed corpus

---

## Day 3: Message Generation & Safety

### Task 3.1: Prompt Template Creation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 2.3

**Description**: Design and document prompt templates for message generation.

**Subtasks**:
- [ ] 3.1.1: Create base prompt template in `config/prompts/generation_prompt.txt`
- [ ] 3.1.2: Create variant tone templates (urgent, informational, friendly)
- [ ] 3.1.3: Define template variables (segment, content, tone)
- [ ] 3.1.4: Add citation instruction examples
- [ ] 3.1.5: Test prompts manually with Azure OpenAI Playground
- [ ] 3.1.6: Document prompt engineering decisions

**Acceptance Criteria**:
- Base template created with all necessary sections
- 3 tone variants created
- Template variables clearly defined
- Citation format specified in template
- Manual testing shows good quality outputs

---

### Task 3.2: Azure OpenAI Integration
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2

**Description**: Implement Azure OpenAI client and generation logic.

**Subtasks**:
- [ ] 3.2.1: Create `src/integrations/azure_openai.py` module
- [ ] 3.2.2: Implement `AzureOpenAIClient` class
- [ ] 3.2.3: Implement `generate_completion()` method with retry logic
- [ ] 3.2.4: Add token counting and cost tracking
- [ ] 3.2.5: Add timeout handling (10 seconds)
- [ ] 3.2.6: Write unit tests with mocked responses

**Acceptance Criteria**:
- Client successfully connects to Azure OpenAI
- Retry logic works (tested with forced failure)
- Token usage and costs tracked
- Timeout properly handled
- Unit tests pass

**Validation**:
```python
from src.integrations.azure_openai import AzureOpenAIClient
client = AzureOpenAIClient()
response = client.generate_completion("Test prompt")
assert 'text' in response
assert 'tokens_used' in response
```

---

### Task 3.3: Generation Agent Implementation
**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 3.1, Task 3.2

**Description**: Implement message variant generation with citations.

**Subtasks**:
- [ ] 3.3.1: Create `src/agents/generation_agent.py` module
- [ ] 3.3.2: Implement `load_prompt_template()` function
- [ ] 3.3.3: Implement `generate_variant()` function
- [ ] 3.3.4: Implement `extract_citations()` function using regex
- [ ] 3.3.5: Implement variant validation (length, format)
- [ ] 3.3.6: Generate 3 variants per segment (different tones)
- [ ] 3.3.7: Write unit tests in `tests/test_generation.py`

**Acceptance Criteria**:
- Generates 3 distinct variants per segment
- Each variant has subject (≤60 chars) and body (150-200 words)
- Citations properly extracted and mapped to source documents
- Tones appropriately varied
- Unit tests pass with mocked OpenAI responses

**Validation**:
```python
from src.agents.generation_agent import generate_variant
segment = {...}
content = [...]
variant = generate_variant(segment, content, tone="urgent")
assert len(variant['subject']) <= 60
assert 150 <= len(variant['body'].split()) <= 250
assert len(variant['citations']) >= 1
```

---

### Task 3.4: Batch Generation Testing
**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 3.3

**Description**: Test generation quality and create sample variants.

**Subtasks**:
- [ ] 3.4.1: Create `notebooks/04_generation_samples.ipynb`
- [ ] 3.4.2: Generate variants for each segment type
- [ ] 3.4.3: Review variant quality manually
- [ ] 3.4.4: Validate citations are correct
- [ ] 3.4.5: Calculate token usage and costs
- [ ] 3.4.6: Document any generation issues

**Acceptance Criteria**:
- Variants generated for all segments
- Quality review documented
- Citations verified against source content
- Cost estimates calculated
- No generation errors

---

### Task 3.5: Content Safety Integration
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2

**Description**: Integrate Azure AI Content Safety API.

**Subtasks**:
- [ ] 3.5.1: Create `src/integrations/azure_content_safety.py` module
- [ ] 3.5.2: Implement `ContentSafetyClient` class
- [ ] 3.5.3: Implement `analyze_text()` method
- [ ] 3.5.4: Parse severity scores from response
- [ ] 3.5.5: Add retry logic for transient failures
- [ ] 3.5.6: Write unit tests with mocked API responses

**Acceptance Criteria**:
- Client successfully connects to Content Safety API
- Returns severity scores for all categories
- Retry logic tested
- Unit tests pass

**Validation**:
```python
from src.integrations.azure_content_safety import ContentSafetyClient
client = ContentSafetyClient()
result = client.analyze_text("Test message")
assert 'hate_severity' in result
```

---

### Task 3.6: Safety Agent Implementation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 3.5

**Description**: Implement safety screening and audit logging.

**Subtasks**:
- [ ] 3.6.1: Create `src/agents/safety_agent.py` module
- [ ] 3.6.2: Load safety thresholds from `config/safety_thresholds.yaml`
- [ ] 3.6.3: Implement `check_safety()` function
- [ ] 3.6.4: Implement `apply_policy_threshold()` function
- [ ] 3.6.5: Implement audit logging to CSV
- [ ] 3.6.6: Implement `generate_audit_report()` function
- [ ] 3.6.7: Write unit tests in `tests/test_safety.py`

**Acceptance Criteria**:
- All variants screened against policy
- Blocks variants with severity > Medium
- Audit log created in CSV format
- Pass/block decisions logged with timestamps
- Unit tests pass

**Validation**:
```python
from src.agents.safety_agent import check_safety
variant = {"body": "Safe marketing message"}
result = check_safety(variant)
assert result['status'] in ['pass', 'block']
assert 'hate_severity' in result
```

---

### Task 3.7: Safety Screening Testing
**Priority**: P0 (Blocker)  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 3.6

**Description**: Test safety screening on all generated variants.

**Subtasks**:
- [ ] 3.7.1: Run safety checks on all generated variants
- [ ] 3.7.2: Calculate pass/block rates
- [ ] 3.7.3: Review blocked variants manually
- [ ] 3.7.4: Verify audit log completeness
- [ ] 3.7.5: Generate safety summary report

**Acceptance Criteria**:
- All variants screened
- Pass rate >90%
- Blocked variants reviewed
- Audit log contains all decisions
- No screening errors

**Day 3 Deliverable**: ✅ Generated, safety-checked message variants with audit trail

---

## Day 4: Experimentation

### Task 4.1: Experiment Design
**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 3.7

**Description**: Design A/B/n experiment structure and configuration.

**Subtasks**:
- [ ] 4.1.1: Define experiment arms (3 treatment + 1 control)
- [ ] 4.1.2: Update `config/experiment_config.yaml` with parameters
- [ ] 4.1.3: Design control message (generic baseline)
- [ ] 4.1.4: Document assignment strategy (stratified random)
- [ ] 4.1.5: Define metrics and statistical tests
- [ ] 4.1.6: Calculate required sample sizes (power analysis)

**Acceptance Criteria**:
- Experiment configuration complete
- Control message created
- Assignment strategy documented
- Sample size requirements calculated
- Metrics and tests defined

---

### Task 4.2: Experimentation Agent Implementation
**Priority**: P0 (Blocker)  
**Estimated Time**: 2.5 hours  
**Dependencies**: Task 4.1

**Description**: Implement experiment orchestration and assignment logic.

**Subtasks**:
- [ ] 4.2.1: Create `src/agents/experimentation_agent.py` module
- [ ] 4.2.2: Implement `design_experiment()` function
- [ ] 4.2.3: Implement `assign_customers_to_arms()` function
- [ ] 4.2.4: Validate assignment distribution (balanced across arms)
- [ ] 4.2.5: Implement assignment logging
- [ ] 4.2.6: Write unit tests in `tests/test_experimentation.py`

**Acceptance Criteria**:
- Experiment designed with correct arm structure
- Customers assigned to arms (stratified by segment)
- Assignment distribution balanced (±5%)
- Assignments logged with timestamps
- Unit tests pass

**Validation**:
```python
from src.agents.experimentation_agent import assign_customers_to_arms
assignments = assign_customers_to_arms(customers, variants)
arm_counts = Counter(a['arm'] for a in assignments)
# Each arm should have ~25% of customers
```

---

### Task 4.3: Engagement Simulation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 4.2

**Description**: Simulate or load engagement data for experiment.

**Subtasks**:
- [ ] 4.3.1: Check if historical engagement data available
- [ ] 4.3.2: If available: Load and map to assignments
- [ ] 4.3.3: If not: Implement engagement simulation function
- [ ] 4.3.4: Simulate open, click, conversion events
- [ ] 4.3.5: Add realistic uplift bias for personalized variants
- [ ] 4.3.6: Validate simulation distributions

**Acceptance Criteria**:
- Engagement data generated for all assignments
- Open rate ~20-30%, click rate ~5-10% (realistic)
- Treatment arms show uplift vs control
- Simulation is reproducible (set random seed)

**Validation**:
```python
from src.agents.experimentation_agent import simulate_engagement
engagement = simulate_engagement(assignments)
control_open_rate = calc_rate(engagement, 'control', 'opened')
treatment_open_rate = calc_rate(engagement, 'treatment_1', 'opened')
assert treatment_open_rate > control_open_rate
```

---

### Task 4.4: Metrics Calculation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 4.3

**Description**: Calculate experiment metrics and statistical significance.

**Subtasks**:
- [ ] 4.4.1: Implement `calculate_metrics()` function
- [ ] 4.4.2: Calculate per-arm metrics (open, click, conversion rates)
- [ ] 4.4.3: Implement `calculate_lift()` function
- [ ] 4.4.4: Implement statistical significance testing (t-test/chi-square)
- [ ] 4.4.5: Calculate confidence intervals
- [ ] 4.4.6: Segment-level metrics breakdown

**Acceptance Criteria**:
- Metrics calculated for all arms
- Lift computed vs control for each treatment
- P-values calculated and interpreted
- Confidence intervals included
- Segment breakdown generated

**Validation**:
```python
from src.agents.experimentation_agent import calculate_metrics, calculate_lift
metrics = calculate_metrics(engagement)
lift = calculate_lift(metrics['treatment_1']['open_rate'], metrics['control']['open_rate'])
assert lift > 0  # Expect positive lift
```

---

### Task 4.5: Experiment Execution Script
**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 4.4

**Description**: Create end-to-end experiment execution script.

**Subtasks**:
- [ ] 4.5.1: Create `scripts/run_experiment.py` script
- [ ] 4.5.2: Integrate all agents in pipeline
- [ ] 4.5.3: Add progress logging with `tqdm`
- [ ] 4.5.4: Add error handling and graceful degradation
- [ ] 4.5.5: Save intermediate outputs (segments, variants, assignments)
- [ ] 4.5.6: Generate final results summary

**Acceptance Criteria**:
- Script executes full pipeline without errors
- All intermediate data saved
- Progress displayed during execution
- Final results summary printed
- Execution time <1 hour for 500 customers

**Validation**:
```bash
python scripts/run_experiment.py
# Should complete successfully and print summary
```

**Day 4 Deliverable**: ✅ Complete experiment execution with results

---

## Day 5: Reporting & Finalization

### Task 5.1: Experiment Report Generation
**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 4.5

**Description**: Create comprehensive experiment report notebook.

**Subtasks**:
- [ ] 5.1.1: Create `notebooks/05_experiment_report.ipynb`
- [ ] 5.1.2: Add executive summary section
- [ ] 5.1.3: Generate lift by variant visualizations (bar charts)
- [ ] 5.1.4: Generate segment breakdown table
- [ ] 5.1.5: Include statistical significance indicators
- [ ] 5.1.6: Add safety audit summary section
- [ ] 5.1.7: Include citation frequency analysis

**Acceptance Criteria**:
- Notebook runs end-to-end without errors
- All visualizations render correctly
- Statistical significance clearly indicated
- Safety audit included
- Report is stakeholder-ready

---

### Task 5.2: Feature Attribution & Explainability
**Priority**: P1 (Important)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 5.1

**Description**: Analyze which segment features drive performance.

**Subtasks**:
- [ ] 5.2.1: Create `notebooks/06_explainability.ipynb`
- [ ] 5.2.2: Calculate correlation between segment features and metrics
- [ ] 5.2.3: Generate feature importance plot
- [ ] 5.2.4: Identify top-performing segment characteristics
- [ ] 5.2.5: Write explainability narrative
- [ ] 5.2.6: Document recommendations

**Acceptance Criteria**:
- Feature correlations calculated
- Feature importance visualized
- Narrative explains findings clearly
- Recommendations actionable
- Notebook runs without errors

---

### Task 5.3: PDF Report Generation
**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 5.1

**Description**: Export report to PDF for distribution.

**Subtasks**:
- [ ] 5.3.1: Install `nbconvert` and dependencies
- [ ] 5.3.2: Create `scripts/generate_report.py` script
- [ ] 5.3.3: Convert notebook to PDF with styling
- [ ] 5.3.4: Verify all visualizations render in PDF
- [ ] 5.3.5: Add cover page and table of contents
- [ ] 5.3.6: Save to `reports/experiment_report.pdf`

**Acceptance Criteria**:
- PDF generated successfully
- All charts and tables visible
- PDF is professionally formatted
- File size reasonable (<10MB)

**Validation**:
```bash
python scripts/generate_report.py
# Should create reports/experiment_report.pdf
```

---

### Task 5.4: Documentation Finalization
**Priority**: P1 (Important)  
**Estimated Time**: 1.5 hours  
**Dependencies**: All previous tasks

**Description**: Complete project documentation.

**Subtasks**:
- [ ] 5.4.1: Update `README.md` with project overview and setup instructions
- [ ] 5.4.2: Create `ARCHITECTURE.md` with system design details
- [ ] 5.4.3: Document all configuration files with inline comments
- [ ] 5.4.4: Add docstrings to all functions (Google style)
- [ ] 5.4.5: Update `.env.example` with all required variables
- [ ] 5.4.6: Create `CONTRIBUTING.md` with development guidelines

**Acceptance Criteria**:
- README explains project purpose and setup clearly
- ARCHITECTURE document matches implementation
- All config files documented
- Code documentation coverage >80%
- `.env.example` complete

---

### Task 5.5: Testing & Validation
**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 5.4

**Description**: Run full test suite and integration tests.

**Subtasks**:
- [ ] 5.5.1: Run all unit tests with `pytest`
- [ ] 5.5.2: Check test coverage with `pytest-cov`
- [ ] 5.5.3: Fix any failing tests
- [ ] 5.5.4: Run integration test (`tests/test_integration.py`)
- [ ] 5.5.5: Verify end-to-end pipeline on fresh data
- [ ] 5.5.6: Document test results

**Acceptance Criteria**:
- All unit tests pass
- Code coverage >70%
- Integration test passes
- End-to-end execution successful
- No critical bugs remaining

**Validation**:
```bash
pytest tests/ --cov=src --cov-report=html
# All tests should pass, coverage >70%
```

---

### Task 5.6: Code Review & Cleanup
**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 5.5

**Description**: Final code review and cleanup.

**Subtasks**:
- [ ] 5.6.1: Run linter (`flake8` or `pylint`)
- [ ] 5.6.2: Run code formatter (`black`)
- [ ] 5.6.3: Remove debugging code and commented-out sections
- [ ] 5.6.4: Verify all TODOs addressed or documented
- [ ] 5.6.5: Check for hardcoded values (move to config)
- [ ] 5.6.6: Final Git commit with all changes

**Acceptance Criteria**:
- No linter errors
- Code formatted consistently
- No debugging artifacts
- All TODOs resolved or tracked
- Git history clean with meaningful commits

---

### Task 5.7: Operationalization Recommendations
**Priority**: P2 (Nice-to-have)  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 5.2

**Description**: Document recommendations for scaling beyond POC.

**Subtasks**:
- [ ] 5.7.1: Add operationalization section to experiment report
- [ ] 5.7.2: Document scaling considerations
- [ ] 5.7.3: Suggest production architecture improvements
- [ ] 5.7.4: Identify technical debt and future work
- [ ] 5.7.5: Estimate production timeline and resources

**Acceptance Criteria**:
- Recommendations clearly documented
- Scaling considerations specific and actionable
- Production architecture sketched
- Technical debt tracked
- Estimates provided

**Day 5 Deliverable**: ✅ Complete project with documentation, tests, and report

---

## Task Priority Legend

- **P0 (Blocker)**: Must be completed for MVP success
- **P1 (Important)**: High value, should be completed if time allows
- **P2 (Nice-to-have)**: Optional, enhances quality but not critical

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Azure API rate limits** | Implement retry logic, batch requests, monitor usage |
| **Poor retrieval quality** | Manual content review, tune search queries, add more content |
| **High safety block rate** | Pre-screen content corpus, adjust thresholds if needed |
| **Insufficient sample size** | Use synthetic data augmentation if dataset too small |
| **Scope creep** | Stick to P0 tasks, defer P2 to future phases |
| **API costs exceed budget** | Monitor token usage daily, use caching for repeated calls |