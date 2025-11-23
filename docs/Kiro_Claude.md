# Task: **Complete Task 4.2**

Including Steering Documents  
[`api-standards.md`](api-standards.md)  
[`azure-services.md`](azure-services.md)  
[`data-models.md`](data-models.md)  
[`product.md`](product.md)  
[`roadmap.md`](roadmap.md)  
[`security-policies.md`](security-policies.md)  
[`steps.md`](steps.md)  
[`structure.md`](structure.md)  
[`tech.md`](tech.md)  

I'll implement **Task 4.2: Experimentation Agent Implementation**. Let me first read the task details and understand the requirements.  

`Read file(s)`  
[`tasks.md`](tasks.md)  

Now let me update the task status to "in progress" and examine the current project structure to understand what needs to be implemented.  

**Task**: `Task 4.2: Experimentation Agent Implementation` from  
[`tasks.md`](tasks.md)  
**Status**: `In Progress`  

Let me check the exact task format in the file:  

`Searched workspace`  
`Finding the exact format of Task 4.2 in the tasks file`  

**Task**: `4.2: Experimentation Agent Implementation` from  
[`tasks.md`](tasks.md)  
**Status**: `In Progress`  

Let me check the exact task format by looking at the specific section:  

`Read file(s)`  
[`tasks.md`](tasks.md) `545 - 556`  

**Task**: `Complete Task 4.2` from  
[`tasks.md`](tasks.md)  
**Status**: `In Progress`  

Let me check the current project structure and understand what's already implemented:  

`Searched workspace`  
`Checking existing agents to understand the current implementation`  

I see that [`experimentation_agent.py`](src/agents/experimentation_agent.py) already exists. Let me check its current state:  

`Read file(s)`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

Let me also check the experiment configuration that was created in Task 4.1:  

`Read file(s)`  
[`experiment_config.yaml`](config/experiment_config.yaml)  

Now let me check what data is available from previous tasks:  

`Searched workspace`  
`Checking what processed data is available from previous tasks`  

Let me check the segments and variants data to understand what I'll be working with:  

`Read file(s)`  
[`segments.json`](data/processed/segments.json)  

`variants.json`  

Let me get a count of the segments to understand the data size:  

`Command`  
```bash
wc -l data/processed/segments.json
```  
```
w wc -l data/processed/segments.json  
;wc -l data/processed/segments.json 2751 data/processed/segments.json  
(.venv) ~/cpo (main ✗)
```  

`Command`  
```bash
python -c "import json; data=json.load(open('data/processed/segments.json')); print(f'Total customers: {len(data)}'); print(f'Segments: {set(item[\"segment\"] for item in data)}')"
```  
```
p python -c "import json; data=json.load(open('data/processed/segments.json')); print(f'Total  
 customers: {len(data)}'); print(f'Segments: {set(item[\"segment\"] for item in data)}')"  
;python3 -c  Total customers: 250  
Segments: {'New Customer', 'High-Value Recent', 'Standard'}  
(.venv) ~/cpo (main ✗)
```  

Good! Now let me check the variants data:  

`Read file(s)`  
[`variants.json`](data/processed/variants.json) `1 - 51`  

Let me check if there's a generation samples file:  

`Read file(s)`  
[`generation_samples.json`](data/processed/generation_samples.json) `1 - 51`  

Perfect! Now let me check the existing tests to understand the testing patterns:  

`Searched workspace`  
`Checking existing test files to understand the testing patterns`  

Let me check if there's already a test file for experimentation:  

`Read file(s)`  
[`test_experimentation.py`](tests/test_experimentation.py)  

Now let me check the design document to understand the requirements for the experimentation agent:  

`Read file(s)`  
[`design.md`](design.md) `1000 - 1201`  

Let me continue reading the design document to understand the experimentation agent requirements:  

`Searched workspace`  
`Searching for experimentation agent details in the design document`  

Now let me read the specific section about the Experimentation Agent in the design document:  

`Read file(s)`  
[`design.md`](design.md) `559 - 701`  

Now I have a good understanding of what needs to be implemented. Let me start implementing the Experimentation Agent. First, let me create the main agent file:  

`Accepted edits to`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

`Credits used: 7.25`  
`Elapsed time: 7m 57s`  
`Checkpoint`  
`Restore`  
`Continue`  

**Kiro**  

Now I need to create the unit tests for the experimentation agent. Let me create the test file:  

`Accepted edits to`  
[`test_experimentation.py`](tests/test_experimentation.py)  

Now let me run the tests to make sure the implementation works correctly:  

`Command`  
```bash
cd /home/antml/cpo && python -m pytest tests/test_experimentation.py -v
```  

`Command`  
```bash
python -m pytest tests/test_experimentation.py -v
```  
```
p python -m pytest tests/test_experimentation.py -v  
;python3 -m pytest tests/test_experimentation.py -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...  
```  

Let me check if there are any import issues by running a simple import test:  

`Command`  
```bash
python -c "from src.agents.experimentation_agent import ExperimentationAgent; print('Import successful')"
```  
```
p python -c "from src.agents.experimentation_agent import ExperimentationAgent; print('Import  
 successful')"  
;python3 -c  Traceback (most recent call last):  
  File "<string>", line 1, in <module>  
  File "/home/iglumtech/cpo/src/agents/experimentation_agent.py", line 23, in <module>  
    from src.utils.logging_config import setup_logging  
ImportError: cannot import name 'setup_logging' from 'src.utils.logging_config' (/home/iglumtech/cpo/src/utils/logging_config.py)  
(.venv) ~/cpo (main ✗)
```  

I need to check what's available in the `logging_config` module:  

`Read file(s)`  
[`logging_config.py`](src/utils/logging_config.py)  

Let me fix the import issue by removing the unused import:  

`Accepted edits to`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

Now let me test the import again:  

`Command`  
```bash
python -c "from src.agents.experimentation_agent import ExperimentationAgent; print('Import successful')"
```  
```
p python -c "from src.agents.experimentation_agent import ExperimentationAgent; print('Import  
 successful')"  
;python3 -c  Import successful  
(.venv) ~/cpo (main ✗)
```  

Good! Now let me run the tests:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_agent_initia  
l  
lization -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization PASSED                  [100%]  
=============================================== 1 passed in 0.98s ================================================  
(.venv) ~/cpo (main ✗)
```  

Great! Let me run a few more key tests:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_design_experiment -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_design_exper  
i  
iment -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_design_experiment PASSED                     [100%]  
=============================================== 1 passed in 1.04s ================================================  
(.venv) ~/cpo (main ✗)
```  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_assign_custo  
m  
mers_to_arms -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms FAILED              [100%]  
==================================================== FAILURES ====================================================  
_____________________________ TestExperimentationAgent.test_assign_customers_to_arms _____________________________  
self = <tests.test_experimentation.TestExperimentationAgent object at 0x7bb1de2c1750>  
sample_customers = [{'customer_id': 'C001', 'features': {'avg_order_value': 250.0}, 'segment': 'High-Value Recent'}, {'customer_id': 'C00...ment': 'New Customer'}, {'customer_id': 'C006', 'features': {'avg_order_value': 80.0}, 'segment': 'New Customer'}, ...]  
sample_variants = [{'body': 'Act now for exclusive benefits!', 'segment': 'High-Value Recent', 'subject': 'Urgent: Limited Time Offer', ...anted to share some news with you.', 'segment': 'Standard', 'subject': 'Hello from our team', 'tone': 'friendly', ...}]  
sample_config = {'arms': {'control': {'description': 'Generic control message', 'variant_type': 'generic'}, 'treatment_1': {'descripti...ject': 'Test Control Subject'}, 'experiment': {'description': 'Test A/B/n experiment', 'name': 'test_experiment'}, ...}  
    def test_assign_customers_to_arms(self, sample_customers, sample_variants, sample_config):  
        """Test customer assignment to experiment arms."""  
        agent = ExperimentationAgent(sample_config)  
        # First design the experiment  
        experiment_design = agent.design_experiment(sample_variants, sample_config)  
        # Then assign customers  
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)  
        # Check all customers are assigned  
>       assert len(assignments) == len(sample_customers)  
E       AssertionError: assert 0 == 8  
E        +  where 0 = len([])  
E        +  and   8 = len([{'customer_id': 'C001', 'features': {'avg_order_value': 250.0}, 'segment': 'High-Value Recent'}, {'customer_id': 'C002', 'features': {'avg_order_value': 300.0}, 'segment': 'High-Value Recent'}, {'customer_id': 'C003', 'features': {'avg_order_value': 150.0}, 'segment': 'Standard'}, {'customer_id': 'C004', 'features': {'avg_order_value': 120.0}, 'segment': 'Standard'}, {'customer_id': 'C005', 'features': {'avg_order_value': 75.0}, 'segment': 'New Customer'}, {'customer_id': 'C006', 'features': {'avg_order_value': 80.0}, 'segment': 'New Customer'}, ...])  
tests/test_experimentation.py:259: AssertionError  
============================================ short test summary info =============================================  
FAILED tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms - AssertionError: assert 0 == 8  
=============================================== 1 failed in 1.55s ================================================  
(.venv) ~/cpo (main ✗)
```  

There's an issue with the assignment logic. Let me debug this by checking what's happening in the assignment function. Let me look at the issue more closely:  

`Command`  
```bash
python -c "
from src.agents.experimentation_agent import ExperimentationAgent
import json
# Test data
sample_customers = [
    {'customer_id': 'C001', 'segment': 'High-Value Recent', 'features': {'avg_order_value': 250.0}},
    {'customer_id': 'C002', 'segment': 'Standard', 'features': {'avg_order_value': 150.0}}
]
sample_variants = [
    {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent', 'subject': 'Test', 'body': 'Test'},
    {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent', 'subject': 'Test', 'body': 'Test'}
]
sample_config = {
    'experiment': {'name': 'test_experiment', 'description': 'Test'},
    'experiment_id': 'TEST_EXP_001',
    'arms': {
        'control': {'description': 'Generic control message', 'variant_type': 'generic'},
        'treatment_1': {'description': 'Urgent tone treatment', 'variant_type': 'personalized'},
        'treatment_2': {'description': 'Info tone treatment', 'variant_type': 'personalized'},
        'treatment_3': {'description': 'Friendly tone treatment', 'variant_type': 'personalized'}
    },
    'control_message': {'subject': 'Test Control Subject', 'body': 'Test control message body'},
    'assignment': {'method': 'stratified_random'},
    'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}
}
agent = ExperimentationAgent(sample_config)
experiment_design = agent.design_experiment(sample_variants, sample_config)
print('Experiment design arms:', list(experiment_design['arms'].keys()))
print('Segments:', experiment_design['segments'])
assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
print('Number of assignments:', len(assignments))
"
```  
```
p python -c "  
dquote> f from src.agents.experimentation_agent import ExperimentationAgent  
dquote> i import json  
dquote>   
dquote> # # Test data  
dquote> s sample_customers = [  
dquote>       {'customer_id': 'C001', 'segment': 'High-Value Recent', 'features': {'avg_order_value': 250.0}},  
dquote>       {'customer_id': 'C002', 'segment': 'Standard', 'features': {'avg_order_value': 150.0}}  
dquote> ]  
dquote>   
dquote> s sample_variants = [  
dquote>       {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent', 'subject': 'Test', 'body':   
 'Test'},  
dquote>       {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent', 'subject': 'Test', 'body': 'Test'}  
dquote> ]  
dquote>   
dquote> s sample_config = {  
dquote>       'experiment': {'name': 'test_experiment', 'description': 'Test'},  
dquote>       'experiment_id': 'TEST_EXP_001',  
dquote>       'arms': {  
dquote>           'control': {'description': 'Generic control message', 'variant_type': 'generic'},  
dquote>           'treatment_1': {'description': 'Urgent tone treatment', 'variant_type': 'personalized'},  
dquote>           'treatment_2': {'description': 'Info tone treatment', 'variant_type': 'personalized'},  
dquote>           'treatment_3': {'description': 'Friendly tone treatment', 'variant_type': 'personalized'}  
dquote>       },  
dquote>       'control_message': {'subject': 'Test Control Subject', 'body': 'Test control message body'},  
dquote>       'assignment': {'method': 'stratified_random'},  
dquote>       'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}  
dquote> }  
dquote>   
dquote> a agent = ExperimentationAgent(sample_config)  
dquote> e experiment_design = agent.design_experiment(sample_variants, sample_config)  
dquote> p print('Experiment design arms:', list(experiment_design['arms'].keys()))  
dquote> p print('Segments:', experiment_design['segments'])  
dquote>   
dquote> a assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)  
dquote> p print('Number of assignments:', len(assignments))  
dquote> "  
;python3 -c  Traceback (most recent call last):  
  File "<string>", line 31, in <module>  
  File "/home/iglumtech/cpo/src/agents/experimentation_agent.py", line 118, in design_experiment  
    'metrics': config['metrics'],  
KeyError: 'metrics'  
(.venv) ~/cpo (main ✗)
```  

I see the issue. The config is missing some required fields. Let me fix the assignment logic to handle missing fields gracefully and also fix the test. Let me update the agent to handle missing config fields:  

`Accepted edits to`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

Now let me test the assignment again:  

`Command`  
```bash
python -c "
from src.agents.experimentation_agent import ExperimentationAgent
# Simple test
sample_customers = [
    {'customer_id': 'C001', 'segment': 'High-Value Recent'},
    {'customer_id': 'C002', 'segment': 'Standard'}
]
sample_variants = [
    {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent'},
    {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent'}
]
sample_config = {
    'experiment': {'name': 'test'},
    'experiment_id': 'TEST_001',
    'arms': {
        'control': {'description': 'control'},
        'treatment_1': {'description': 'treatment 1'},
        'treatment_2': {'description': 'treatment 2'},
        'treatment_3': {'description': 'treatment 3'}
    },
    'control_message': {'subject': 'test', 'body': 'test'},
    'assignment': {'method': 'stratified_random'},
    'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}
}
agent = ExperimentationAgent(sample_config)
experiment_design = agent.design_experiment(sample_variants, sample_config)
print('Design successful')
assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
print('Assignments:', len(assignments))
for a in assignments:
    print(f'  {a[\"customer_id\"]} -> {a[\"experiment_arm\"]}')
"
```  
```
p python -c "  
dquote> f from src.agents.experimentation_agent import ExperimentationAgent  
dquote>   
dquote> # # Simple test  
dquote> s sample_customers = [  
dquote>       {'customer_id': 'C001', 'segment': 'High-Value Recent'},  
dquote>       {'customer_id': 'C002', 'segment': 'Standard'}  
dquote> ]  
dquote>   
dquote> s sample_variants = [  
dquote>       {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent'},  
dquote>       {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent'}  
dquote> ]  
dquote>   
dquote> s sample_config = {  
dquote>       'experiment': {'name': 'test'},  
dquote>       'experiment_id': 'TEST_001',  
dquote>       'arms': {  
dquote>           'control': {'description': 'control'},  
dquote>           'treatment_1': {'description': 'treatment 1'},  
dquote>           'treatment_2': {'description': 'treatment 2'},  
dquote>           'treatment_3': {'description': 'treatment 3'}  
dquote>       },  
dquote>       'control_message': {'subject': 'test', 'body': 'test'},  
dquote>       'assignment': {'method': 'stratified_random'},  
dquote>       'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}  
dquote> }  
dquote>   
dquote> a agent = ExperimentationAgent(sample_config)  
dquote> e experiment_design = agent.design_experiment(sample_variants, sample_config)  
dquote> p print('Design successful')  
dquote>   
dquote> a assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)  
dquote> p print('Assignments:', len(assignments))  
dquote> f for a in assignments:  
dquote>       print(f'  {a[\"customer_id\"]} -> {a[\"experiment_arm\"]}')  
dquote> "  
;python3 -c  Design successful  
Assignments: 0  
(.venv) ~/cpo (main ✗)
```  

The issue is that no assignments are being made. Let me debug the assignment logic. I think the problem is in the allocation calculation. Let me check the assignment logic more carefully:  

`Read file(s)`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py) `150 - 201`  

I see the issue! The problem is that with only 2 customers, the allocation calculation results in 0 customers per arm because:  
- `control_size = int(2 * 25 / 100) = int(0.5) = 0`  
- `treatment_size = int(2 * 75 / 100 / 3) = int(0.5) = 0`  

Let me fix this by ensuring at least 1 customer per arm when possible:  

`Accepted edits to`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

Now let me test the assignment again:  

`Command`  
```bash
python -c "
from src.agents.experimentation_agent import ExperimentationAgent
# Simple test with 8 customers
sample_customers = [
    {'customer_id': f'C{i:03d}', 'segment': 'High-Value Recent' if i % 2 == 0 else 'Standard'}
    for i in range(1, 9)
]
sample_variants = [
    {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent'},
    {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent'}
]
sample_config = {
    'experiment': {'name': 'test'},
    'experiment_id': 'TEST_001',
    'arms': {
        'control': {'description': 'control'},
        'treatment_1': {'description': 'treatment 1'},
        'treatment_2': {'description': 'treatment 2'},
        'treatment_3': {'description': 'treatment 3'}
    },
    'control_message': {'subject': 'test', 'body': 'test'},
    'assignment': {'method': 'stratified_random'},
    'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}
}
agent = ExperimentationAgent(sample_config)
experiment_design = agent.design_experiment(sample_variants, sample_config)
assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
print('Assignments:', len(assignments))
from collections import Counter
arm_counts = Counter(a['experiment_arm'] for a in assignments)
print('Arm distribution:', dict(arm_counts))
"
```  
```
p python -c "  
dquote> f from src.agents.experimentation_agent import ExperimentationAgent  
dquote>   
dquote> # # Simple test with 8 customers  
dquote> s sample_customers = [  
dquote>       {'customer_id': f'C{i:03d}', 'segment': 'High-Value Recent' if i % 2 == 0 else 'Standard'}  
dquote>       for i in range(1, 9)  
dquote> ]  
dquote>   
dquote> s sample_variants = [  
dquote>       {'variant_id': 'VAR_001', 'segment': 'High-Value Recent', 'tone': 'urgent'},  
dquote>       {'variant_id': 'VAR_002', 'segment': 'Standard', 'tone': 'urgent'}  
dquote> ]  
dquote>   
dquote> s sample_config = {  
dquote>       'experiment': {'name': 'test'},  
dquote>       'experiment_id': 'TEST_001',  
dquote>       'arms': {  
dquote>           'control': {'description': 'control'},  
dquote>           'treatment_1': {'description': 'treatment 1'},  
dquote>           'treatment_2': {'description': 'treatment 2'},  
dquote>           'treatment_3': {'description': 'treatment 3'}  
dquote>       },  
dquote>       'control_message': {'subject': 'test', 'body': 'test'},  
dquote>       'assignment': {'method': 'stratified_random'},  
dquote>       'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}  
dquote> }  
dquote>   
dquote> a agent = ExperimentationAgent(sample_config)  
dquote> e experiment_design = agent.design_experiment(sample_variants, sample_config)  
dquote> a assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)  
dquote> p print('Assignments:', len(assignments))  
dquote>   
dquote> f from collections import Counter  
dquote> a arm_counts = Counter(a['experiment_arm'] for a in assignments)  
dquote> p print('Arm distribution:', dict(arm_counts))  
dquote> "  
;python3 -c  Assignments: 8  
Arm distribution: {'control': 2, 'treatment_1': 2, 'treatment_2': 2, 'treatment_3': 2}  
(.venv) ~/cpo (main ✗)
```  

Great! Now the assignment is working. Let me run the test again:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_assign_custo  
m  
mers_to_arms -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms PASSED              [100%]  
=============================================== 1 passed in 1.20s ================================================  
(.venv) ~/cpo (main ✗)
```  

Excellent! Now let me test the engagement simulation:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_simulate_engagement -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_simulate_eng  
a  
agement -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_simulate_engagement PASSED                   [100%]  
=============================================== 1 passed in 0.96s ================================================  
(.venv) ~/cpo (main ✗)
```  

Great! Let me test the metrics calculation:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_calculate_metrics -v
```  
```
p python -m pytest tests/test_experimentation.py::TestExperimentationAgent::test_calculate_me  
t  
trics -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestExperimentationAgent::test_calculate_metrics PASSED                     [100%]  
=============================================== 1 passed in 0.92s ================================================  
(.venv) ~/cpo (main ✗)
```  

Perfect! Now let me run all the tests to make sure everything works:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py -v
```  
```
p python -m pytest tests/test_experimentation.py -v  
;python3 -m pytest tests/test_experimentation.py -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collecting 8 items                                                                                               
collected 18 items                                                                                               
tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization PASSED                  [  5%]  
tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization_without_config PASSED   [ 11%]  
tests/test_experimentation.py::TestExperimentationAgent::test_design_experiment PASSED                     [ 16%]  
tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms PASSED              [ 22%]  
tests/test_experimentation.py::TestExperimentationAgent::test_assignment_balance_validation PASSED         [ 27%]  
tests/test_experimentation.py::TestExperimentationAgent::test_simulate_engagement PASSED                   [ 33%]  
tests/test_experimentation.py::TestExperimentationAgent::test_calculate_metrics PASSED                     [ 38%]  
tests/test_experimentation.py::TestExperimentationAgent::test_segment_breakdown_calculation PASSED         [ 44%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_design_experiment_function PASSED            [ 50%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function FAILED               [ 55%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_assign_customers_to_arms_function PASSED     [ 61%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_simulate_engagement_function PASSED          [ 66%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_metrics_function PASSED            [ 72%]  
tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list FAILED                              [ 77%]  
tests/test_experimentation.py::TestEdgeCases::test_empty_customers_list PASSED                             [ 83%]  
tests/test_experimentation.py::TestEdgeCases::test_single_customer_assignment PASSED                       [ 88%]  
tests/test_experimentation.py::TestEdgeCases::test_statistical_significance_with_small_sample FAILED       [ 94%]  
tests/test_experimentation.py::TestEdgeCases::test_zero_engagement_rates PASSED                            [100%]  
==================================================== FAILURES ====================================================  
_____________________________ TestConvenienceFunctions.test_calculate_lift_function ______________________________  
self = <tests.test_experimentation.TestConvenienceFunctions object at 0x734584f3df90>  
    def test_calculate_lift_function(self):  
        """Test calculate_lift convenience function."""  
        # Test normal case  
        lift = calculate_lift(0.30, 0.25)  
>       assert lift == 20.0  # 20% lift  
E       assert 19.999999999999996 == 20.0  
tests/test_experimentation.py:446: AssertionError  
_____________________________________ TestEdgeCases.test_empty_variants_list _____________________________________  
self = <tests.test_experimentation.TestEdgeCases object at 0x734584f3eb90>  
    def test_empty_variants_list(self):  
        """Test handling of empty variants list."""  
        agent = ExperimentationAgent()  
        config = {  
            'experiment': {'name': 'test'},  
            'arms': {'control': {'description': 'test'}},  
            'control_message': {'subject': 'test', 'body': 'test'},  
            'assignment': {'method': 'stratified_random'},  
            'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}  
        }  
        # Should not crash with empty variants  
>       result = agent.design_experiment([], config)  
tests/test_experimentation.py:522:   
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _   
self = <src.agents.experimentation_agent.ExperimentationAgent object at 0x734584d5f8e0>, variants = []  
config = {'arms': {'control': {'description': 'test'}}, 'assignment': {'method': 'stratified_random'}, 'control_message': {'body': 'test', 'subject': 'test'}, 'experiment': {'name': 'test'}, ...}  
    def design_experiment(self, variants: List[Dict], config: Dict) -> Dict:  
        """  
        Design A/B/n experiment structure based on variants and configuration.  
        Args:  
            variants: List of message variants from generation agent  
            config: Experiment configuration from config/experiment_config.yaml  
        Returns:  
            Dictionary containing experiment design details  
        """  
        logger.info(f"Designing experiment with {len(variants)} variants")  
        # Generate unique experiment ID  
        self.experiment_id = config.get('experiment_id', f"EXP_{uuid.uuid4().hex[:8].upper()}")  
        # Extract unique segments from variants  
        segments = list(set(variant['segment'] for variant in variants))  
        logger.info(f"Found segments: {segments}")  
        # Group variants by segment and tone  
        variants_by_segment = defaultdict(dict)  
        for variant in variants:  
            segment = variant['segment']  
            tone = variant['tone']  
            variants_by_segment[segment][tone] = variant  
        # Design experiment arms  
        arms = {  
            'control': {  
                'name': 'control',  
                'description': config['arms']['control']['description'],  
                'variant_type': 'generic',  
                'message': config['control_message']  
            }  
        }  
        # Add treatment arms for each tone  
        tones = ['urgent', 'informational', 'friendly']  
        for i, tone in enumerate(tones, 1):  
            arms[f'treatment_{i}'] = {  
                'name': f'treatment_{i}',  
>               'description': config['arms'][f'treatment_{i}']['description'],  
                'variant_type': 'personalized',  
                'tone': tone,  
                'variants_by_segment': {  
                    segment: variants_by_segment[segment].get(tone)  
                    for segment in segments  
                }  
            }  
E           KeyError: 'treatment_1'  
src/agents/experimentation_agent.py:100: KeyError  
_________________________ TestEdgeCases.test_statistical_significance_with_small_sample __________________________  
self = <tests.test_experimentation.TestEdgeCases object at 0x734584f3f400>  
    def test_statistical_significance_with_small_sample(self):  
        """Test statistical significance calculation with small samples."""  
        agent = ExperimentationAgent()  
        control_data = {  
            'sample_size': 5,  
            'counts': {'opened': 1, 'clicked': 0, 'converted': 0}  
        }  
        treatment_data = {  
            'sample_size': 5,  
            'counts': {'opened': 2, 'clicked': 1, 'converted': 0}  
        }  
        # Should not crash with small samples  
        result = agent._calculate_statistical_significance(  
            control_data, treatment_data, 'open_rate'  
        )  
        assert 'p_value' in result  
        assert 'significant' in result  
>       assert isinstance(result['significant'], bool)  
E       assert False  
E        +  where False = isinstance(np.False_, bool)  
tests/test_experimentation.py:577: AssertionError  
============================================ short test summary info =============================================  
FAILED tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function - assert 19.999999999999996 == 20.0  
FAILED tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list - KeyError: 'treatment_1'  
FAILED tests/test_experimentation.py::TestEdgeCases::test_statistical_significance_with_small_sample - assert False  
========================================== 3 failed, 15 passed in 1.22s ==========================================  
(.venv) ~/cpo (main ✗)
```  

I need to fix these test failures. Let me address them one by one:  
- Fix the floating point precision issue in `calculate_lift`  
- Fix the empty variants handling  
- Fix the numpy boolean type issue  

`Accepted edits to`  
[`test_experimentation.py`](tests/test_experimentation.py)  

`2 edits to file`  
[`experimentation_agent.py`](src/agents/experimentation_agent.py)  

Now let me run the tests again:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function -v
```  
```
p python -m pytest tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_li  
f  
ft_function -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function FAILED               [100%]  
==================================================== FAILURES ====================================================  
_____________________________ TestConvenienceFunctions.test_calculate_lift_function ______________________________  
self = <tests.test_experimentation.TestConvenienceFunctions object at 0x7f3629db1180>  
    def test_calculate_lift_function(self):  
        """Test calculate_lift convenience function."""  
        # Test normal case  
        lift = calculate_lift(0.30, 0.25)  
        assert abs(lift - 20.0) < 0.001  # 20% lift (allow for floating point precision)  
        # Test zero control case  
        lift = calculate_lift(0.10, 0.0)  
        assert lift == 0  
        # Test negative lift  
        lift = calculate_lift(0.20, 0.25)  
>       assert lift == -20.0  # 20% decrease  
E       assert -19.999999999999996 == -20.0  
tests/test_experimentation.py:454: AssertionError  
============================================ short test summary info =============================================  
FAILED tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function - assert -19.999999999999996 == -20.0  
=============================================== 1 failed in 1.20s ================================================  
(.venv) ~/cpo (main ✗)
```  

Let me fix the other floating point assertion too:  

`Accepted edits to`  
[`test_experimentation.py`](tests/test_experimentation.py)  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function -v
```  
```
p python -m pytest tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_li  
f  
ft_function -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function PASSED               [100%]  
=============================================== 1 passed in 1.01s ================================================  
(.venv) ~/cpo (main ✗)
```  

Good! Now let me test the other failing tests:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list -v
```  
```
p python -m pytest tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list PASSED                              [100%]  
=============================================== 1 passed in 0.85s ================================================  
(.venv) ~/cpo (main ✗)
```  

`Command`  
```bash
python -m pytest tests/test_experimentation.py::TestEdgeCases::test_statistical_significance_with_small_sample -v
```  
```
p python -m pytest tests/test_experimentation.py::TestEdgeCases::test_statistical_significanc  
e  
e_with_small_sample -v  
;python3 -m pytest  -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collected 1 item                                                                                                 
tests/test_experimentation.py::TestEdgeCases::test_statistical_significance_with_small_sample PASSED       [100%]  
=============================================== 1 passed in 0.88s ================================================  
(.venv) ~/cpo (main ✗)
```  

Excellent! Now let me run all the tests to make sure everything passes:  

`Command`  
```bash
python -m pytest tests/test_experimentation.py -v
```  
```
p python -m pytest tests/test_experimentation.py -v  
;python3 -m pytest tests/test_experimentation.py -v ============================================== test session starts ===============================================  
platform linux -- Python 3.10.12, pytest-9.0.1, pluggy-1.6.0 -- /home/iglumtech/cpo/.venv/bin/python3  
cachedir: .pytest_cache  
rootdir: /home/iglumtech/cpo  
plugins: anyio-4.11.0, cov-7.0.0  
collecting ...   
collecting 8 items                                                                                               
collected 18 items                                                                                               
tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization PASSED                  [  5%]  
tests/test_experimentation.py::TestExperimentationAgent::test_agent_initialization_without_config PASSED   [ 11%]  
tests/test_experimentation.py::TestExperimentationAgent::test_design_experiment PASSED                     [ 16%]  
tests/test_experimentation.py::TestExperimentationAgent::test_assign_customers_to_arms PASSED              [ 22%]  
tests/test_experimentation.py::TestExperimentationAgent::test_assignment_balance_validation PASSED         [ 27%]  
tests/test_experimentation.py::TestExperimentationAgent::test_simulate_engagement PASSED                   [ 33%]  
tests/test_experimentation.py::TestExperimentationAgent::test_calculate_metrics PASSED                     [ 38%]  
tests/test_experimentation.py::TestExperimentationAgent::test_segment_breakdown_calculation PASSED         [ 44%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_design_experiment_function PASSED            [ 50%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_lift_function PASSED               [ 55%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_assign_customers_to_arms_function PASSED     [ 61%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_simulate_engagement_function PASSED          [ 66%]  
tests/test_experimentation.py::TestConvenienceFunctions::test_calculate_metrics_function PASSED            [ 72%]  
tests/test_experimentation.py::TestEdgeCases::test_empty_variants_list PASSED                              [ 77%]  
tests/test_experimentation.py::TestEdgeCases::test_empty_customers_list PASSED                             [ 83%]  
tests/test_experimentation.py::TestEdgeCases::test_single_customer_assignment PASSED                       [ 88%]  
tests/test_experimentation.py::TestEdgeCases::test_statistical_significance_with_small_sample PASSED       [ 94%]  
tests/test_experimentation.py::TestEdgeCases::test_zero_engagement_rates PASSED                            [100%]  
=============================================== 18 passed in 1.38s ===============================================  
(.venv) ~/cpo (main ✗)
```  

Perfect! All tests are passing. Now let me test the implementation with real data to make sure it works with the actual project data. Let me create a simple integration test:  

`Command`  
```bash
python -c "
import json
from src.agents.experimentation_agent import ExperimentationAgent
# Load real data
with open('data/processed/segments.json', 'r') as f:
    segments_data = json.load(f)
with open('data/processed/generation_samples.json', 'r') as f:
    variants_data = json.load(f)
with open('config/experiment_config.yaml', 'r') as f:
    import yaml
    config = yaml.safe_load(f)
print(f'Loaded {len(segments_data)} customers and {len(variants_data)} variants')
# Test with first 20 customers and first 6 variants
test_customers = segments_data[:20]
test_variants = variants_data[:6]
print(f'Testing with {len(test_customers)} customers and {len(test_variants)} variants')
# Initialize agent
agent = ExperimentationAgent(config)
# Design experiment
experiment_design = agent.design_experiment(test_variants, config)
print(f'Experiment designed: {experiment_design[\"experiment_id\"]}')
# Assign customers
assignments = agent.assign_customers_to_arms(test_customers, experiment_design)
print(f'Assigned {len(assignments)} customers')
# Simulate engagement
engagement_data = agent.simulate_engagement(assignments, config)
print(f'Simulated engagement for {len(engagement_data)} customers')
# Calculate metrics
metrics = agent.calculate_metrics(engagement_data)
print(f'Calculated metrics for {len(metrics[\"arms\"])} arms')
# Show results
for arm_name, arm_data in metrics['arms'].items():
    arm_metrics = arm_data['metrics']
    print(f'{arm_name}: Open={arm_metrics[\"open_rate\"]:.1%}, Click={arm_metrics[\"click_rate\"]:.1%}')
print('✅ Integration test successful!')
"
```  
```
p python -c "  
dquote> i import json  
dquote> f from src.agents.experimentation_agent import ExperimentationAgent  
dquote>   
dquote> # # Load real data  
dquote> w with open('data/processed/segments.json', 'r') as f:  
dquote>       segments_data = json.load(f)  
dquote>   
dquote> w with open('data/processed/generation_samples.json', 'r') as f:  
dquote>       variants_data = json.load(f)  
dquote>   
dquote> w with open('config/experiment_config.yaml', 'r') as f:  
dquote>       import yaml  
dquote>       config = yaml
```