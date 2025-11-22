# Implementation Tasks: Customer Personalization Orchestrator

## Task Overview

This document outlines the discrete, trackable implementation tasks for building the Customer Personalization Orchestrator MVP. Tasks are organized by day and priority, with clear acceptance criteria and dependencies.

**Total Duration**: 5 days  
**Methodology**: Incremental delivery with daily milestones

---

## Day 1: Environment Setup & Segmentation

### Task 1.1: Project Environment Setup
- [x] **Complete Task 1.1**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: None

**Description**: Set up development environment, Azure resources, and project structure. Alway confirm if exist first before writing.

**Subtasks**:
- Create Python virtual environment with **Python 3.10+** (3.10.12 or higher)
- Install dependencies from `requirements.txt`
- Create `.env` file with Azure credentials
- Initialize project directory structure (`.kiro/`, `src/`, `config/`, `data/`, `logs/`)
- Set up Git repository with `.gitignore`

**Acceptance Criteria**:
- Python environment activates without errors
- All dependencies install successfully
- Azure credentials configured and tested
- Directory structure matches design document
- Git initialized with first commit

**Validation**:
```bash
python --version  # Should show 3.10.12 or higher
pip list | grep azure  # Should show azure-* packages
python -c "from azure.identity import DefaultAzureCredential; DefaultAzureCredential()"
```

---

### Task 1.2: Azure Resource Provisioning
- [x] **Complete Task 1.2**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.1

**Description**: Provision and configure required Azure services. You MUST check `docs/ENV_SETUP_GUIDE.md` to guide you.

**Subtasks**:
- Create Azure OpenAI resource and deploy gpt-5-mini model (cost-optimized)
- Create Azure AI Search service
- Create Azure AI Content Safety resource
- Configure authentication (Managed Identity or API keys)
- Test connectivity to all services
- Document endpoints in `config/azure_config.yaml`

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
- [x] **Complete Task 1.3**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.1

**Description**: Create or load sample customer dataset and approved content.

**Subtasks**:
- Load or generate sample customer dataset (100-500 records)
- Validate dataset schema (required columns present)
- Create 20-50 approved content documents (JSON format)
- Validate content document schema
- Perform basic EDA in `notebooks/01_data_exploration.ipynb`

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
- [x] **Complete Task 1.4**

**Priority**: P0 (Blocker)  
**Estimated Time**: 2.5 hours  
**Dependencies**: Task 1.3

**Description**: Implement customer segmentation using rule-based or clustering approach.

**Subtasks**:
- Create `src/agents/segmentation_agent.py` module
- Implement `load_customer_data()` function
- Implement rule-based segmentation logic (RFM or similar)
- Alternative: Implement K-means clustering segmentation
- Implement `generate_segment_summary()` function
- Add segment label mapping (e.g., "High-Value Recent")
- Write unit tests in `tests/test_segmentation.py`

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
- [x] **Complete Task 1.5**

**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 1.4

**Description**: Analyze segment quality and document findings.

**Subtasks**:
- Create `notebooks/02_segmentation_analysis.ipynb` (Create .py file then convert it with jupytext like `notebooks/py/01_data_exploration.py`)
- Visualize segment distribution
- Calculate segment statistics (mean, median per feature)
- Validate segments are balanced (no segment <10% of total)
- Document segment definitions in notebook

**Acceptance Criteria**:
- Segment distribution visualized (bar chart)
- Statistical summary table generated
- All segments have >10% of customers
- Segment definitions documented

**Day 1 Deliverable**: ✅ Segmented customer dataset with 3-5 labeled groups

---

## Day 2: Content Retrieval & Indexing

### Task 2.1: Azure AI Search Index Setup
- [ ] **Complete Task 2.1**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2, Task 1.3

**Description**: Create search index and define schema for content documents.

**Subtasks**:
- Create `src/integrations/azure_search.py` module
- Define index schema (fields, types, searchable/filterable)
- Create index in Azure AI Search
- Configure semantic search settings
- Write `index_documents()` function
- Write unit tests for search client

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
- [ ] **Complete Task 2.2**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 2.1

**Description**: Index all approved content documents into Azure AI Search.

**Subtasks**:
- Create `scripts/index_content.py` script
- Read all content documents from `data/content/approved_content/`
- Transform documents to match index schema
- Batch index documents (batches of 100)
- Add progress bar with `tqdm`
- Log indexing statistics (count, errors)

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
- [ ] **Complete Task 2.3**

**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 2.2

**Description**: Implement content retrieval logic for segment-based queries.

**Subtasks**:
- Create `src/agents/retrieval_agent.py` module
- Implement `construct_query_from_segment()` function
- Implement `retrieve_content()` function with Azure Search client
- Implement `extract_snippet()` function (200-word limit)
- Add relevance score filtering (threshold: >0.5)
- Add logging for all queries and results
- Write unit tests in `tests/test_retrieval.py`

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
- [ ] **Complete Task 2.4**

**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 2.3

**Description**: Test retrieval quality across different segment types.

**Subtasks**:
- Create `notebooks/03_retrieval_testing.ipynb`
- Test retrieval for each segment type
- Visualize relevance scores distribution
- Manually review top 3 results per segment for quality
- Document any retrieval issues or improvements needed

**Acceptance Criteria**:
- Retrieval tested for all 3-5 segments
- Relevance scores visualized
- Manual quality review documented
- At least 80% of retrieved content relevant to segment

**Day 2 Deliverable**: ✅ Functional content retrieval with indexed corpus

---

## Day 3: Message Generation & Safety

### Task 3.1: Prompt Template Creation
- [ ] **Complete Task 3.1**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 2.3

**Description**: Design and document prompt templates for message generation.

**Subtasks**:
- Create base prompt template in `config/prompts/generation_prompt.txt`
- Create variant tone templates (urgent, informational, friendly)
- Define template variables (segment, content, tone)
- Add citation instruction examples
- Test prompts manually with Azure OpenAI Playground
- Document prompt engineering decisions

**Acceptance Criteria**:
- Base template created with all necessary sections
- 3 tone variants created
- Template variables clearly defined
- Citation format specified in template
- Manual testing shows good quality outputs

---

### Task 3.2: Azure OpenAI Integration
- [ ] **Complete Task 3.2**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2

**Description**: Implement Azure OpenAI client and generation logic.

**Subtasks**:
- Create `src/integrations/azure_openai.py` module
- Implement `AzureOpenAIClient` class
- Implement `generate_completion()` method with retry logic
- Add token counting and cost tracking
- Add timeout handling (10 seconds)
- Write unit tests with mocked responses

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
- [ ] **Complete Task 3.3**

**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 3.1, Task 3.2

**Description**: Implement message variant generation with citations.

**Subtasks**:
- Create `src/agents/generation_agent.py` module
- Implement `load_prompt_template()` function
- Implement `generate_variant()` function
- Implement `extract_citations()` function using regex
- Implement variant validation (length, format)
- Generate 3 variants per segment (different tones)
- Write unit tests in `tests/test_generation.py`

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
- [ ] **Complete Task 3.4**

**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 3.3

**Description**: Test generation quality and create sample variants.

**Subtasks**:
- Create `notebooks/04_generation_samples.ipynb`
- Generate variants for each segment type
- Review variant quality manually
- Validate citations are correct
- Calculate token usage and costs
- Document any generation issues

**Acceptance Criteria**:
- Variants generated for all segments
- Quality review documented
- Citations verified against source content
- Cost estimates calculated
- No generation errors

---

### Task 3.5: Content Safety Integration
- [ ] **Complete Task 3.5**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.2

**Description**: Integrate Azure AI Content Safety API.

**Subtasks**:
- Create `src/integrations/azure_content_safety.py` module
- Implement `ContentSafetyClient` class
- Implement `analyze_text()` method
- Parse severity scores from response
- Add retry logic for transient failures
- Write unit tests with mocked API responses

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
- [ ] **Complete Task 3.6**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 3.5

**Description**: Implement safety screening and audit logging.

**Subtasks**:
- Create `src/agents/safety_agent.py` module
- Load safety thresholds from `config/safety_thresholds.yaml`
- Implement `check_safety()` function
- Implement `apply_policy_threshold()` function
- Implement audit logging to CSV
- Implement `generate_audit_report()` function
- Write unit tests in `tests/test_safety.py`

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
- [ ] **Complete Task 3.7**

**Priority**: P0 (Blocker)  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 3.6

**Description**: Test safety screening on all generated variants.

**Subtasks**:
- Run safety checks on all generated variants
- Calculate pass/block rates
- Review blocked variants manually
- Verify audit log completeness
- Generate safety summary report

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
- [ ] **Complete Task 4.1**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 3.7

**Description**: Design A/B/n experiment structure and configuration.

**Subtasks**:
- Define experiment arms (3 treatment + 1 control)
- Update `config/experiment_config.yaml` with parameters
- Design control message (generic baseline)
- Document assignment strategy (stratified random)
- Define metrics and statistical tests
- Calculate required sample sizes (power analysis)

**Acceptance Criteria**:
- Experiment configuration complete
- Control message created
- Assignment strategy documented
- Sample size requirements calculated
- Metrics and tests defined

---

### Task 4.2: Experimentation Agent Implementation
- [ ] **Complete Task 4.2**

**Priority**: P0 (Blocker)  
**Estimated Time**: 2.5 hours  
**Dependencies**: Task 4.1

**Description**: Implement experiment orchestration and assignment logic.

**Subtasks**:
- Create `src/agents/experimentation_agent.py` module
- Implement `design_experiment()` function
- Implement `assign_customers_to_arms()` function
- Validate assignment distribution (balanced across arms)
- Implement assignment logging
- Write unit tests in `tests/test_experimentation.py`

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
- [ ] **Complete Task 4.3**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 4.2

**Description**: Simulate or load engagement data for experiment.

**Subtasks**:
- Check if historical engagement data available
- If available: Load and map to assignments
- If not: Implement engagement simulation function
- Simulate open, click, conversion events
- Add realistic uplift bias for personalized variants
- Validate simulation distributions

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
- [ ] **Complete Task 4.4**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 4.3

**Description**: Calculate experiment metrics and statistical significance.

**Subtasks**:
- Implement `calculate_metrics()` function
- Calculate per-arm metrics (open, click, conversion rates)
- Implement `calculate_lift()` function
- Implement statistical significance testing (t-test/chi-square)
- Calculate confidence intervals
- Segment-level metrics breakdown

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
- [ ] **Complete Task 4.5**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 4.4

**Description**: Create end-to-end experiment execution script.

**Subtasks**:
- Create `scripts/run_experiment.py` script
- Integrate all agents in pipeline
- Add progress logging with `tqdm`
- Add error handling and graceful degradation
- Save intermediate outputs (segments, variants, assignments)
- Generate final results summary

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
- [ ] **Complete Task 5.1**

**Priority**: P0 (Blocker)  
**Estimated Time**: 2 hours  
**Dependencies**: Task 4.5

**Description**: Create comprehensive experiment report notebook.

**Subtasks**:
- Create `notebooks/05_experiment_report.ipynb`
- Add executive summary section
- Generate lift by variant visualizations (bar charts)
- Generate segment breakdown table
- Include statistical significance indicators
- Add safety audit summary section
- Include citation frequency analysis

**Acceptance Criteria**:
- Notebook runs end-to-end without errors
- All visualizations render correctly
- Statistical significance clearly indicated
- Safety audit included
- Report is stakeholder-ready

---

### Task 5.2: Feature Attribution & Explainability
- [ ] **Complete Task 5.2**

**Priority**: P1 (Important)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 5.1

**Description**: Analyze which segment features drive performance.

**Subtasks**:
- Create `notebooks/06_explainability.ipynb`
- Calculate correlation between segment features and metrics
- Generate feature importance plot
- Identify top-performing segment characteristics
- Write explainability narrative
- Document recommendations

**Acceptance Criteria**:
- Feature correlations calculated
- Feature importance visualized
- Narrative explains findings clearly
- Recommendations actionable
- Notebook runs without errors

---

### Task 5.3: PDF Report Generation
- [ ] **Complete Task 5.3**

**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 5.1

**Description**: Export report to PDF for distribution.

**Subtasks**:
- Install `nbconvert` and dependencies
- Create `scripts/generate_report.py` script
- Convert notebook to PDF with styling
- Verify all visualizations render in PDF
- Add cover page and table of contents
- Save to `reports/experiment_report.pdf`

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
- [ ] **Complete Task 5.4**

**Priority**: P1 (Important)  
**Estimated Time**: 1.5 hours  
**Dependencies**: All previous tasks

**Description**: Complete project documentation.

**Subtasks**:
- Update `README.md` with project overview and setup instructions
- Create `ARCHITECTURE.md` with system design details
- Document all configuration files with inline comments
- Add docstrings to all functions (Google style)
- Update `.env.example` with all required variables
- Create `CONTRIBUTING.md` with development guidelines

**Acceptance Criteria**:
- README explains project purpose and setup clearly
- ARCHITECTURE document matches implementation
- All config files documented
- Code documentation coverage >80%
- `.env.example` complete

---

### Task 5.5: Testing & Validation
- [ ] **Complete Task 5.5**

**Priority**: P0 (Blocker)  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 5.4

**Description**: Run full test suite and integration tests.

**Subtasks**:
- Run all unit tests with `pytest`
- Check test coverage with `pytest-cov`
- Fix any failing tests
- Run integration test (`tests/test_integration.py`)
- Verify end-to-end pipeline on fresh data
- Document test results

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
- [ ] **Complete Task 5.6**

**Priority**: P1 (Important)  
**Estimated Time**: 1 hour  
**Dependencies**: Task 5.5

**Description**: Final code review and cleanup.

**Subtasks**:
- Run linter (`flake8` or `pylint`)
- Run code formatter (`black`)
- Remove debugging code and commented-out sections
- Verify all TODOs addressed or documented
- Check for hardcoded values (move to config)
- Final Git commit with all changes

**Acceptance Criteria**:
- No linter errors
- Code formatted consistently
- No debugging artifacts
- All TODOs resolved or tracked
- Git history clean with meaningful commits

---

### Task 5.7: Operationalization Recommendations
- [ ] **Complete Task 5.7**

**Priority**: P2 (Nice-to-have)  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 5.2

**Description**: Document recommendations for scaling beyond POC.

**Subtasks**:
- Add operationalization section to experiment report
- Document scaling considerations
- Suggest production architecture improvements
- Identify technical debt and future work
- Estimate production timeline and resources

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