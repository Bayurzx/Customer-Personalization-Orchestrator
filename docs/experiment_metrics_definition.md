# Experiment Metrics Definition
**Task 4.1: Experiment Design**  
**Created**: 2025-11-23

## Overview

This document defines all metrics, calculations, and statistical tests for the Customer Personalization Orchestrator A/B/n experiment.

## Primary and Secondary Metrics

### Primary Metric
**Click Rate**: The percentage of customers who click on links in the email
- **Formula**: `clicks / emails_sent * 100`
- **Baseline**: 5.0%
- **Target Improvement**: 15% relative lift (5.0% → 5.75%)
- **Business Impact**: Direct indicator of engagement and intent

### Secondary Metrics
1. **Open Rate**: Percentage of customers who open the email
   - **Formula**: `opens / emails_sent * 100`
   - **Baseline**: 25.0%
   - **Target Improvement**: 15% relative lift (25.0% → 28.75%)

2. **Conversion Rate**: Percentage of customers who complete desired action
   - **Formula**: `conversions / emails_sent * 100`
   - **Baseline**: 1.0%
   - **Target Improvement**: 15% relative lift (1.0% → 1.15%)

## Metric Calculations

### Rate Calculations
```python
def calculate_rates(engagement_data):
    """Calculate engagement rates for experiment arms."""
    metrics = {}
    
    for arm in ['control', 'treatment_1', 'treatment_2', 'treatment_3']:
        arm_data = [e for e in engagement_data if e['experiment_arm'] == arm]
        
        total_sent = len(arm_data)
        total_opened = sum(1 for e in arm_data if e['opened'])
        total_clicked = sum(1 for e in arm_data if e['clicked'])
        total_converted = sum(1 for e in arm_data if e['converted'])
        
        metrics[arm] = {
            'sample_size': total_sent,
            'open_rate': total_opened / total_sent if total_sent > 0 else 0,
            'click_rate': total_clicked / total_sent if total_sent > 0 else 0,
            'conversion_rate': total_converted / total_sent if total_sent > 0 else 0,
            'counts': {
                'sent': total_sent,
                'opened': total_opened,
                'clicked': total_clicked,
                'converted': total_converted
            }
        }
    
    return metrics
```

### Lift Calculations
```python
def calculate_lift(treatment_rate, control_rate):
    """Calculate relative lift vs control."""
    if control_rate == 0:
        return float('inf') if treatment_rate > 0 else 0
    
    return (treatment_rate - control_rate) / control_rate * 100

def calculate_absolute_lift(treatment_rate, control_rate):
    """Calculate absolute lift vs control."""
    return treatment_rate - control_rate
```

## Statistical Testing

### Test Selection
- **Proportions**: Two-sample z-test for proportions
- **Small Samples**: Fisher's exact test (if sample size < 30)
- **Multiple Comparisons**: Bonferroni correction for multiple treatment arms

### Significance Testing
```python
from scipy import stats
import numpy as np

def proportion_z_test(x1, n1, x2, n2):
    """
    Two-sample z-test for proportions.
    
    Args:
        x1: Successes in treatment group
        n1: Sample size in treatment group  
        x2: Successes in control group
        n2: Sample size in control group
        
    Returns:
        z_stat, p_value
    """
    p1 = x1 / n1
    p2 = x2 / n2
    
    # Pooled proportion
    p_pool = (x1 + x2) / (n1 + n2)
    
    # Standard error
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    # Z-statistic
    z_stat = (p1 - p2) / se
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return z_stat, p_value

def calculate_confidence_interval(rate, n, confidence=0.95):
    """Calculate confidence interval for proportion."""
    z_score = stats.norm.ppf(1 - (1 - confidence) / 2)
    se = np.sqrt(rate * (1 - rate) / n)
    
    lower = rate - z_score * se
    upper = rate + z_score * se
    
    return max(0, lower), min(1, upper)
```

### Multiple Comparisons Correction
```python
def bonferroni_correction(p_values, alpha=0.05):
    """Apply Bonferroni correction for multiple comparisons."""
    corrected_alpha = alpha / len(p_values)
    significant = [p < corrected_alpha for p in p_values]
    return corrected_alpha, significant
```

## Segment-Level Analysis

### Segment Breakdown
Calculate metrics separately for each customer segment:
- High-Value Recent
- Standard  
- New Customer

### Segment Metrics
```python
def calculate_segment_metrics(engagement_data, segments):
    """Calculate metrics by segment and experiment arm."""
    segment_metrics = {}
    
    for segment_name in ['High-Value Recent', 'Standard', 'New Customer']:
        segment_customers = [s['customer_id'] for s in segments if s['segment'] == segment_name]
        segment_engagement = [e for e in engagement_data if e['customer_id'] in segment_customers]
        
        segment_metrics[segment_name] = calculate_rates(segment_engagement)
    
    return segment_metrics
```

## Effect Size Calculations

### Cohen's h for Proportions
```python
def cohens_h(p1, p2):
    """Calculate Cohen's h effect size for proportions."""
    return 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))

def interpret_cohens_h(h):
    """Interpret Cohen's h effect size."""
    h = abs(h)
    if h < 0.2:
        return "small"
    elif h < 0.5:
        return "medium"
    else:
        return "large"
```

## Confidence Intervals

### Bootstrap Confidence Intervals
```python
def bootstrap_confidence_interval(data, statistic_func, n_bootstrap=1000, confidence=0.95):
    """Calculate bootstrap confidence interval."""
    bootstrap_stats = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        bootstrap_sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_stat = statistic_func(bootstrap_sample)
        bootstrap_stats.append(bootstrap_stat)
    
    # Calculate percentiles
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower = np.percentile(bootstrap_stats, lower_percentile)
    upper = np.percentile(bootstrap_stats, upper_percentile)
    
    return lower, upper
```

## Reporting Metrics

### Summary Statistics
For each metric and arm combination, report:
- **Rate**: Percentage (e.g., 5.2%)
- **Count**: Raw numbers (e.g., 13/250)
- **Confidence Interval**: 95% CI (e.g., [3.1%, 7.3%])
- **Sample Size**: Number of customers

### Lift Analysis
For each treatment vs control comparison:
- **Relative Lift**: Percentage improvement (e.g., +15.2%)
- **Absolute Lift**: Percentage point difference (e.g., +0.8pp)
- **Statistical Significance**: p-value and significance indicator
- **Effect Size**: Cohen's h with interpretation
- **Confidence Interval**: CI for the lift estimate

### Example Report Format
```
Click Rate Analysis:
==================
Control:      5.0% (3/60) [95% CI: 1.7%, 8.3%]
Treatment 1:  6.2% (4/65) [95% CI: 2.4%, 10.0%] 
Treatment 2:  5.8% (4/69) [95% CI: 2.3%, 9.3%]
Treatment 3:  7.1% (5/70) [95% CI: 3.0%, 11.2%]

Lift vs Control:
================
Treatment 1: +24.0% relative (+1.2pp absolute), p=0.67, Cohen's h=0.12 (small)
Treatment 2: +16.0% relative (+0.8pp absolute), p=0.78, Cohen's h=0.08 (small)  
Treatment 3: +42.0% relative (+2.1pp absolute), p=0.45, Cohen's h=0.21 (medium)

Statistical Significance: None (after Bonferroni correction, α=0.017)
```

## Quality Assurance

### Data Validation
- Verify all customers have engagement records
- Check for missing or invalid data
- Validate assignment integrity

### Metric Validation
- Ensure rates are between 0 and 1
- Verify sample sizes match assignment counts
- Check for data consistency across metrics

### Statistical Assumptions
- Independence of observations
- Adequate sample size for normal approximation
- No systematic bias in assignment or measurement

## Interpretation Guidelines

### Statistical Significance
- **α = 0.05** for individual tests
- **Bonferroni correction** for multiple comparisons
- **Focus on effect size** over p-values for POC

### Practical Significance
- **Minimum meaningful lift**: 10% relative improvement
- **Business impact**: Consider cost-benefit of implementation
- **Confidence in results**: Account for uncertainty in estimates

### POC Considerations
- **Limited power**: Focus on directional insights
- **Effect size**: Emphasize magnitude over significance
- **Trends**: Look for consistent patterns across metrics
- **Segment insights**: Identify which segments respond best

## Success Criteria

### Primary Success
- **Click rate improvement**: Any treatment shows >10% relative lift
- **Statistical trend**: Consistent direction across treatments
- **Segment insights**: Identify best-performing segment-treatment combinations

### Secondary Success  
- **Open rate improvement**: Supporting evidence of engagement
- **Conversion rate**: Early indicator of business impact
- **Cross-metric consistency**: Improvements align across funnel

### Learning Objectives
- **Personalization value**: Quantify benefit of segment-based messaging
- **Tone effectiveness**: Identify most effective tone per segment
- **Implementation insights**: Understand operational requirements for scale