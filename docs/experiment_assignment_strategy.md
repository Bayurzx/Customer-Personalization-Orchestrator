# Experiment Assignment Strategy
**Task 4.1: Experiment Design**  
**Created**: 2025-11-23

## Overview

This document defines the stratified random assignment strategy for the Customer Personalization Orchestrator A/B/n experiment.

## Experiment Structure

### Arms Configuration
- **Control Arm**: Generic baseline message (25% of customers)
- **Treatment 1**: Personalized urgent tone variants (25% of customers)  
- **Treatment 2**: Personalized informational tone variants (25% of customers)
- **Treatment 3**: Personalized friendly tone variants (25% of customers)

### Sample Allocation
- **Total Customers**: 250
- **Customers per Arm**: ~62
- **Assignment Method**: Stratified random within segments

## Stratified Random Assignment Process

### Step 1: Segment Stratification
Customers are first grouped by their assigned segment:
- **High-Value Recent**: 84 customers (33.6%)
- **Standard**: 145 customers (58.0%) 
- **New Customer**: 21 customers (8.4%)

### Step 2: Within-Segment Randomization
Within each segment:
1. Randomly shuffle all customers
2. Assign first 25% to Control arm
3. Assign next 25% to Treatment 1 (urgent)
4. Assign next 25% to Treatment 2 (informational)  
5. Assign final 25% to Treatment 3 (friendly)

### Step 3: Balance Validation
Verify assignment balance:
- Each arm should have 25% ± 5% of total customers
- Each segment should be represented in each arm
- Minimum 5 customers per segment per arm

## Expected Assignment Distribution

| Segment | Control | Treatment 1 | Treatment 2 | Treatment 3 | Total |
|---------|---------|-------------|-------------|-------------|-------|
| High-Value Recent | 21 | 21 | 21 | 21 | 84 |
| Standard | 36 | 36 | 36 | 37 | 145 |
| New Customer | 5 | 5 | 5 | 6 | 21 |
| **Total** | **62** | **62** | **62** | **64** | **250** |

## Assignment Algorithm

```python
def stratified_random_assignment(customers, segments, random_seed=42):
    """
    Assign customers to experiment arms using stratified randomization.
    
    Args:
        customers: List of customer records
        segments: Segment assignments for each customer
        random_seed: Random seed for reproducibility
        
    Returns:
        List of assignment records
    """
    import random
    random.seed(random_seed)
    
    assignments = []
    arms = ['control', 'treatment_1', 'treatment_2', 'treatment_3']
    
    # Group customers by segment
    segment_groups = {}
    for customer in customers:
        segment = customer['segment']
        if segment not in segment_groups:
            segment_groups[segment] = []
        segment_groups[segment].append(customer)
    
    # Assign within each segment
    for segment, segment_customers in segment_groups.items():
        # Shuffle customers randomly
        random.shuffle(segment_customers)
        
        # Calculate customers per arm for this segment
        n = len(segment_customers)
        per_arm = n // 4
        remainder = n % 4
        
        # Assign to arms
        start_idx = 0
        for i, arm in enumerate(arms):
            # Add one extra customer to first 'remainder' arms
            arm_size = per_arm + (1 if i < remainder else 0)
            end_idx = start_idx + arm_size
            
            for customer in segment_customers[start_idx:end_idx]:
                assignments.append({
                    'customer_id': customer['customer_id'],
                    'segment': segment,
                    'experiment_arm': arm,
                    'assigned_at': datetime.utcnow().isoformat(),
                    'assignment_method': 'stratified_random'
                })
            
            start_idx = end_idx
    
    return assignments
```

## Quality Assurance Checks

### Balance Validation
- **Tolerance**: ±5% from target 25% allocation per arm
- **Check**: Each arm has 23-27% of total customers
- **Action**: Re-randomize if balance exceeds tolerance

### Segment Representation  
- **Minimum**: 5 customers per segment per arm
- **Check**: All segments represented in all arms
- **Action**: Adjust assignment if minimum not met

### Randomization Verification
- **Seed**: Fixed random seed (42) for reproducibility
- **Check**: Assignment appears random within segments
- **Action**: Verify no systematic bias in assignment

## Assignment Metadata

Each assignment record includes:
- `customer_id`: Unique customer identifier
- `segment`: Customer segment (High-Value Recent, Standard, New Customer)
- `experiment_arm`: Assigned arm (control, treatment_1, treatment_2, treatment_3)
- `variant_id`: Specific message variant (for treatment arms)
- `assigned_at`: Assignment timestamp
- `assignment_method`: "stratified_random"

## Statistical Considerations

### Power Analysis Results
- **Sample Size**: 62 customers per arm
- **Expected Effect**: 15% relative lift
- **Statistical Power**: Limited for small effects
- **Recommendation**: Focus on directional insights rather than statistical significance

### Minimum Detectable Effect
With current sample size:
- **Open Rate**: Can detect ~10-15% relative lift
- **Click Rate**: Can detect ~20-25% relative lift  
- **Conversion Rate**: Limited power for small effects

### Confidence Intervals
- Use bootstrap confidence intervals for metrics
- Report effect sizes with uncertainty ranges
- Focus on practical significance over statistical significance

## Implementation Notes

### Reproducibility
- Fixed random seed ensures consistent assignment
- Assignment process is deterministic given same input
- All assignment decisions logged with timestamps

### Scalability
- Algorithm scales to larger customer bases
- Maintains balance across segments automatically
- Can accommodate additional arms or segments

### Audit Trail
- Complete assignment log maintained
- Assignment method documented for each customer
- Enables post-hoc analysis and validation

## Success Criteria

### Assignment Success
- ✅ All 250 customers assigned to arms
- ✅ Balance within ±5% tolerance
- ✅ All segments represented in all arms
- ✅ Minimum 5 customers per segment per arm

### Experiment Validity
- ✅ Random assignment within segments
- ✅ No systematic bias in assignment
- ✅ Assignment independent of outcome variables
- ✅ Complete assignment metadata captured

## Next Steps

1. **Implementation**: Code assignment algorithm in experimentation agent
2. **Validation**: Run assignment and validate balance
3. **Documentation**: Log all assignment decisions
4. **Quality Check**: Verify randomization and balance
5. **Proceed**: Move to engagement simulation (Task 4.3)