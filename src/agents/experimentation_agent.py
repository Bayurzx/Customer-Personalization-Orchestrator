"""
Experimentation Agent for Customer Personalization Orchestrator.

This module implements A/B/n experiment orchestration, customer assignment,
engagement simulation, and metrics calculation.

Author: AI Assistant
Created: 2025-11-23
Task: 4.2 - Experimentation Agent Implementation
"""

import json
import logging
import random
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import uuid

import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

class ExperimentationAgent:
    """
    Agent responsible for A/B/n experiment orchestration and analysis.
    
    This agent handles:
    - Experiment design and configuration
    - Stratified random customer assignment
    - Engagement simulation
    - Metrics calculation and statistical analysis
    - Lift calculation and significance testing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Experimentation Agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.experiment_id = None
        self.assignments = []
        self.engagement_data = []
        self.metrics = {}
        
        # Set random seed for reproducibility
        random_seed = self.config.get('random_seed', 42)
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        logger.info("ExperimentationAgent initialized")
    
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
                'description': config.get('arms', {}).get('control', {}).get('description', 'Generic control message'),
                'variant_type': 'generic',
                'message': config.get('control_message', {'subject': 'Control', 'body': 'Control message'})
            }
        }
        
        # Add treatment arms for each tone
        tones = ['urgent', 'informational', 'friendly']
        for i, tone in enumerate(tones, 1):
            treatment_key = f'treatment_{i}'
            arms[treatment_key] = {
                'name': treatment_key,
                'description': config.get('arms', {}).get(treatment_key, {}).get('description', f'Treatment {i}'),
                'variant_type': 'personalized',
                'tone': tone,
                'variants_by_segment': {
                    segment: variants_by_segment[segment].get(tone)
                    for segment in segments
                }
            }
        
        experiment_design = {
            'experiment_id': self.experiment_id,
            'name': config.get('experiment', {}).get('name', 'experiment'),
            'description': config.get('experiment', {}).get('description', 'A/B/n experiment'),
            'created_at': datetime.utcnow().isoformat(),
            'arms': arms,
            'segments': segments,
            'assignment_strategy': config.get('assignment', {}).get('method', 'stratified_random'),
            'sample_allocation': config.get('sample_allocation', {'control_percent': 25, 'treatment_percent': 75}),
            'metrics': config.get('metrics', {'primary': 'click_rate'}),
            'statistical_testing': config.get('statistical_testing', {'alpha': 0.05})
        }
        
        logger.info(f"Experiment designed: {self.experiment_id} with {len(arms)} arms")
        return experiment_design
    
    def assign_customers_to_arms(
        self, 
        customers: List[Dict], 
        experiment_design: Dict
    ) -> List[Dict]:
        """
        Assign customers to experiment arms using stratified random assignment.
        
        Args:
            customers: List of customer data with segments
            experiment_design: Experiment design from design_experiment()
            
        Returns:
            List of assignment records
        """
        logger.info(f"Assigning {len(customers)} customers to experiment arms")
        
        assignments = []
        assignment_stats = defaultdict(lambda: defaultdict(int))
        
        # Group customers by segment
        customers_by_segment = defaultdict(list)
        for customer in customers:
            segment = customer['segment']
            customers_by_segment[segment].append(customer)
        
        # Assign customers within each segment
        for segment, segment_customers in customers_by_segment.items():
            logger.info(f"Assigning {len(segment_customers)} customers in segment '{segment}'")
            
            # Shuffle customers for random assignment
            shuffled_customers = segment_customers.copy()
            random.shuffle(shuffled_customers)
            
            n_customers = len(shuffled_customers)
            n_arms = len(experiment_design['arms'])
            
            # Calculate allocation sizes (25% each arm for 4 arms)
            allocation_pct = experiment_design['sample_allocation']
            control_size = max(1, int(n_customers * allocation_pct['control_percent'] / 100))
            treatment_size = max(1, int(n_customers * allocation_pct['treatment_percent'] / 100 / 3))  # 3 treatment arms
            
            # Adjust if total allocation exceeds available customers
            total_needed = control_size + (treatment_size * 3)
            if total_needed > n_customers:
                # Simple round-robin assignment for small samples
                control_size = 1 if n_customers >= 1 else 0
                treatment_size = max(1, (n_customers - control_size) // 3) if n_customers > 1 else 0
            
            # Assign to control
            for i in range(control_size):
                if i < len(shuffled_customers):
                    customer = shuffled_customers[i]
                    assignment = {
                        'customer_id': customer['customer_id'],
                        'segment': segment,
                        'experiment_arm': 'control',
                        'variant_id': 'control',
                        'assigned_at': datetime.utcnow().isoformat(),
                        'assignment_method': 'stratified_random'
                    }
                    assignments.append(assignment)
                    assignment_stats[segment]['control'] += 1
            
            # Assign to treatment arms
            treatment_arms = ['treatment_1', 'treatment_2', 'treatment_3']
            start_idx = control_size
            
            for arm_idx, arm_name in enumerate(treatment_arms):
                arm_start = start_idx + (arm_idx * treatment_size)
                arm_end = arm_start + treatment_size
                
                for i in range(arm_start, min(arm_end, len(shuffled_customers))):
                    customer = shuffled_customers[i]
                    
                    # Get variant for this segment and arm
                    arm_config = experiment_design['arms'][arm_name]
                    variant = arm_config['variants_by_segment'].get(segment)
                    variant_id = variant['variant_id'] if variant else f"{arm_name}_{segment}_fallback"
                    
                    assignment = {
                        'customer_id': customer['customer_id'],
                        'segment': segment,
                        'experiment_arm': arm_name,
                        'variant_id': variant_id,
                        'assigned_at': datetime.utcnow().isoformat(),
                        'assignment_method': 'stratified_random'
                    }
                    assignments.append(assignment)
                    assignment_stats[segment][arm_name] += 1
        
        # Log assignment statistics
        logger.info("Assignment statistics by segment:")
        for segment, arm_counts in assignment_stats.items():
            total = sum(arm_counts.values())
            logger.info(f"  {segment}: {dict(arm_counts)} (total: {total})")
        
        # Validate assignment balance
        self._validate_assignment_balance(assignments, experiment_design)
        
        self.assignments = assignments
        logger.info(f"Successfully assigned {len(assignments)} customers")
        return assignments
    
    def _validate_assignment_balance(self, assignments: List[Dict], experiment_design: Dict):
        """
        Validate that assignment distribution is balanced within tolerance.
        
        Args:
            assignments: List of customer assignments
            experiment_design: Experiment design configuration
        """
        # Count assignments by arm
        arm_counts = Counter(assignment['experiment_arm'] for assignment in assignments)
        total_assignments = len(assignments)
        
        # Check balance tolerance (±5%)
        tolerance = experiment_design.get('quality_checks', {}).get('assignment_balance', {}).get('tolerance', 0.05)
        target_pct = 25.0  # 25% per arm for 4 arms
        
        for arm, count in arm_counts.items():
            actual_pct = (count / total_assignments) * 100
            deviation = abs(actual_pct - target_pct)
            
            if deviation > (tolerance * 100):
                logger.warning(f"Assignment imbalance detected for {arm}: {actual_pct:.1f}% (target: {target_pct}%)")
            else:
                logger.info(f"Assignment balance OK for {arm}: {actual_pct:.1f}%")
    
    def simulate_engagement(
        self, 
        assignments: List[Dict], 
        config: Dict,
        use_historical: bool = False
    ) -> List[Dict]:
        """
        Simulate customer engagement based on assignments and configuration.
        
        Args:
            assignments: Customer assignments from assign_customers_to_arms()
            config: Experiment configuration with simulation parameters
            use_historical: Whether to use historical data (if available)
            
        Returns:
            List of engagement records
        """
        logger.info(f"Simulating engagement for {len(assignments)} assignments")
        
        engagement_data = []
        simulation_config = config.get('simulation', {
            'baseline_rates': {'open_rate': 0.25, 'click_rate': 0.05, 'conversion_rate': 0.01},
            'expected_uplift': {'mean': 0.15, 'std_dev': 0.05, 'min_uplift': 0.05, 'max_uplift': 0.30},
            'noise_factor': 0.02
        })
        baseline_rates = simulation_config['baseline_rates']
        uplift_config = simulation_config['expected_uplift']
        
        # Segment-specific baseline rates
        segment_baselines = config.get('segments', {})
        
        for assignment in assignments:
            customer_id = assignment['customer_id']
            segment = assignment['segment']
            arm = assignment['experiment_arm']
            
            # Get segment-specific baseline rates if available
            segment_config = segment_baselines.get(segment, {})
            open_baseline = segment_config.get('expected_baseline_open', baseline_rates['open_rate'])
            click_baseline = segment_config.get('expected_baseline_click', baseline_rates['click_rate'])
            conversion_baseline = baseline_rates['conversion_rate']
            
            # Calculate engagement probabilities
            if arm == 'control':
                # Control uses baseline rates
                open_prob = open_baseline
                click_prob = click_baseline
                conversion_prob = conversion_baseline
            else:
                # Treatment arms get uplift
                segment_uplift = segment_config.get('expected_uplift', uplift_config['mean'])
                
                # Add some randomness to uplift
                noise = np.random.normal(0, uplift_config['std_dev'])
                actual_uplift = max(
                    uplift_config['min_uplift'],
                    min(uplift_config['max_uplift'], segment_uplift + noise)
                )
                
                open_prob = min(1.0, open_baseline * (1 + actual_uplift))
                click_prob = min(1.0, click_baseline * (1 + actual_uplift))
                conversion_prob = min(1.0, conversion_baseline * (1 + actual_uplift))
            
            # Add noise factor
            noise_factor = simulation_config.get('noise_factor', 0.02)
            open_prob = max(0, min(1.0, open_prob + np.random.normal(0, noise_factor)))
            click_prob = max(0, min(1.0, click_prob + np.random.normal(0, noise_factor)))
            
            # Simulate engagement events
            opened = np.random.random() < open_prob
            clicked = opened and (np.random.random() < click_prob)  # Can only click if opened
            converted = clicked and (np.random.random() < conversion_prob)  # Can only convert if clicked
            
            engagement_record = {
                'customer_id': customer_id,
                'segment': segment,
                'experiment_arm': arm,
                'variant_id': assignment['variant_id'],
                'opened': opened,
                'clicked': clicked,
                'converted': converted,
                'engagement_at': datetime.utcnow().isoformat(),
                'engagement_source': 'simulated'
            }
            
            engagement_data.append(engagement_record)
        
        # Log engagement statistics
        self._log_engagement_stats(engagement_data)
        
        self.engagement_data = engagement_data
        logger.info(f"Simulated engagement for {len(engagement_data)} customers")
        return engagement_data
    
    def _log_engagement_stats(self, engagement_data: List[Dict]):
        """Log engagement statistics by arm and segment."""
        stats_by_arm = defaultdict(lambda: {'opened': 0, 'clicked': 0, 'converted': 0, 'total': 0})
        
        for record in engagement_data:
            arm = record['experiment_arm']
            stats_by_arm[arm]['total'] += 1
            if record['opened']:
                stats_by_arm[arm]['opened'] += 1
            if record['clicked']:
                stats_by_arm[arm]['clicked'] += 1
            if record['converted']:
                stats_by_arm[arm]['converted'] += 1
        
        logger.info("Engagement simulation results:")
        for arm, stats in stats_by_arm.items():
            total = stats['total']
            open_rate = (stats['opened'] / total) * 100 if total > 0 else 0
            click_rate = (stats['clicked'] / total) * 100 if total > 0 else 0
            conversion_rate = (stats['converted'] / total) * 100 if total > 0 else 0
            
            logger.info(f"  {arm}: Open={open_rate:.1f}%, Click={click_rate:.1f}%, Convert={conversion_rate:.1f}% (n={total})")
    
    def calculate_metrics(self, engagement_data: List[Dict]) -> Dict:
        """
        Calculate experiment metrics for all arms.
        
        Args:
            engagement_data: Engagement records from simulate_engagement()
            
        Returns:
            Dictionary containing metrics for all arms
        """
        logger.info(f"Calculating metrics for {len(engagement_data)} engagement records")
        
        # Group data by arm
        data_by_arm = defaultdict(list)
        for record in engagement_data:
            arm = record['experiment_arm']
            data_by_arm[arm].append(record)
        
        # Calculate metrics for each arm
        arm_metrics = {}
        for arm, arm_data in data_by_arm.items():
            metrics = self._calculate_arm_metrics(arm_data)
            arm_metrics[arm] = metrics
        
        # Calculate lift analysis
        lift_analysis = self._calculate_lift_analysis(arm_metrics)
        
        # Calculate segment breakdown
        segment_breakdown = self._calculate_segment_breakdown(engagement_data)
        
        experiment_metrics = {
            'experiment_id': self.experiment_id,
            'experiment_name': self.config.get('experiment', {}).get('name', 'personalization_poc'),
            'total_customers': len(engagement_data),
            'arms': arm_metrics,
            'lift_analysis': lift_analysis,
            'segment_breakdown': segment_breakdown,
            'computed_at': datetime.utcnow().isoformat()
        }
        
        self.metrics = experiment_metrics
        logger.info("Metrics calculation completed")
        return experiment_metrics
    
    def _calculate_arm_metrics(self, arm_data: List[Dict]) -> Dict:
        """Calculate metrics for a single experiment arm."""
        total = len(arm_data)
        opened = sum(1 for record in arm_data if record['opened'])
        clicked = sum(1 for record in arm_data if record['clicked'])
        converted = sum(1 for record in arm_data if record['converted'])
        
        return {
            'arm_name': arm_data[0]['experiment_arm'] if arm_data else 'unknown',
            'sample_size': total,
            'metrics': {
                'open_rate': opened / total if total > 0 else 0,
                'click_rate': clicked / total if total > 0 else 0,
                'conversion_rate': converted / total if total > 0 else 0
            },
            'counts': {
                'sent': total,
                'opened': opened,
                'clicked': clicked,
                'converted': converted
            }
        }
    
    def _calculate_lift_analysis(self, arm_metrics: Dict) -> List[Dict]:
        """Calculate lift analysis comparing treatment arms to control."""
        lift_analysis = []
        
        if 'control' not in arm_metrics:
            logger.warning("No control arm found for lift calculation")
            return lift_analysis
        
        control_metrics = arm_metrics['control']['metrics']
        
        for arm_name, arm_data in arm_metrics.items():
            if arm_name == 'control':
                continue
            
            treatment_metrics = arm_data['metrics']
            
            for metric_name in ['open_rate', 'click_rate', 'conversion_rate']:
                control_value = control_metrics[metric_name]
                treatment_value = treatment_metrics[metric_name]
                
                # Calculate lift
                if control_value > 0:
                    lift_percent = ((treatment_value - control_value) / control_value) * 100
                    lift_absolute = treatment_value - control_value
                else:
                    lift_percent = 0
                    lift_absolute = treatment_value
                
                # Calculate statistical significance
                significance = self._calculate_statistical_significance(
                    arm_metrics['control'], arm_data, metric_name
                )
                
                lift_record = {
                    'treatment_arm': arm_name,
                    'metric': metric_name,
                    'control_value': control_value,
                    'treatment_value': treatment_value,
                    'lift_percent': lift_percent,
                    'lift_absolute': lift_absolute,
                    'statistical_significance': significance
                }
                
                lift_analysis.append(lift_record)
        
        return lift_analysis
    
    def _calculate_statistical_significance(
        self, 
        control_data: Dict, 
        treatment_data: Dict, 
        metric: str
    ) -> Dict:
        """
        Calculate statistical significance using appropriate test.
        
        For binary outcomes (open/click/convert), use chi-square test.
        For continuous metrics, use t-test.
        """
        try:
            # Get sample sizes and success counts
            control_n = control_data['sample_size']
            treatment_n = treatment_data['sample_size']
            
            if metric == 'open_rate':
                control_successes = control_data['counts']['opened']
                treatment_successes = treatment_data['counts']['opened']
            elif metric == 'click_rate':
                control_successes = control_data['counts']['clicked']
                treatment_successes = treatment_data['counts']['clicked']
            elif metric == 'conversion_rate':
                control_successes = control_data['counts']['converted']
                treatment_successes = treatment_data['counts']['converted']
            else:
                return {'p_value': 1.0, 'significant': False, 'test_type': 'unknown'}
            
            # Chi-square test for proportions
            observed = np.array([[control_successes, control_n - control_successes],
                               [treatment_successes, treatment_n - treatment_successes]])
            
            chi2, p_value, dof, expected = stats.chi2_contingency(observed)
            
            # Calculate confidence interval for difference in proportions
            control_rate = control_successes / control_n if control_n > 0 else 0
            treatment_rate = treatment_successes / treatment_n if treatment_n > 0 else 0
            
            # Simple confidence interval (normal approximation)
            diff = treatment_rate - control_rate
            se_diff = np.sqrt((control_rate * (1 - control_rate) / control_n) + 
                            (treatment_rate * (1 - treatment_rate) / treatment_n))
            
            ci_lower = diff - 1.96 * se_diff
            ci_upper = diff + 1.96 * se_diff
            
            return {
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05),
                'test_type': 'chi_square',
                'chi2_statistic': float(chi2),
                'confidence_interval': {
                    'lower': float(ci_lower),
                    'upper': float(ci_upper)
                }
            }
            
        except Exception as e:
            logger.warning(f"Statistical significance calculation failed: {e}")
            return {
                'p_value': 1.0,
                'significant': False,
                'test_type': 'failed',
                'error': str(e)
            }
    
    def _calculate_segment_breakdown(self, engagement_data: List[Dict]) -> List[Dict]:
        """Calculate metrics breakdown by segment."""
        # Group by segment
        data_by_segment = defaultdict(lambda: defaultdict(list))
        for record in engagement_data:
            segment = record['segment']
            arm = record['experiment_arm']
            data_by_segment[segment][arm].append(record)
        
        segment_breakdown = []
        
        for segment, segment_data in data_by_segment.items():
            # Calculate metrics for each arm in this segment
            segment_metrics = {}
            for arm, arm_data in segment_data.items():
                segment_metrics[arm] = self._calculate_arm_metrics(arm_data)
            
            # Find best performing arm (by click rate)
            best_arm = 'control'
            best_click_rate = 0
            
            for arm, metrics in segment_metrics.items():
                click_rate = metrics['metrics']['click_rate']
                if click_rate > best_click_rate:
                    best_click_rate = click_rate
                    best_arm = arm
            
            # Calculate lift vs control
            control_click_rate = segment_metrics.get('control', {}).get('metrics', {}).get('click_rate', 0)
            if control_click_rate > 0:
                lift_percent = ((best_click_rate - control_click_rate) / control_click_rate) * 100
            else:
                lift_percent = 0
            
            segment_breakdown.append({
                'segment': segment,
                'sample_size': sum(len(arm_data) for arm_data in segment_data.values()),
                'best_performing_arm': best_arm,
                'lift_percent': lift_percent,
                'metrics_by_arm': segment_metrics
            })
        
        return segment_breakdown


# Convenience functions for backward compatibility and ease of use

def design_experiment(variants: List[Dict], config: Dict) -> Dict:
    """
    Convenience function to design an experiment.
    
    Args:
        variants: List of message variants
        config: Experiment configuration
        
    Returns:
        Experiment design dictionary
    """
    agent = ExperimentationAgent(config)
    return agent.design_experiment(variants, config)


def assign_customers_to_arms(
    customers: List[Dict], 
    variants: List[Dict], 
    config: Dict
) -> List[Dict]:
    """
    Convenience function to assign customers to experiment arms.
    
    Args:
        customers: List of customer data
        variants: List of message variants  
        config: Experiment configuration
        
    Returns:
        List of customer assignments
    """
    agent = ExperimentationAgent(config)
    experiment_design = agent.design_experiment(variants, config)
    return agent.assign_customers_to_arms(customers, experiment_design)


def simulate_engagement(assignments: List[Dict], config: Dict) -> List[Dict]:
    """
    Convenience function to simulate engagement.
    
    Args:
        assignments: Customer assignments
        config: Experiment configuration
        
    Returns:
        List of engagement records
    """
    agent = ExperimentationAgent(config)
    return agent.simulate_engagement(assignments, config)


def calculate_metrics(engagement_data: List[Dict], config: Dict) -> Dict:
    """
    Convenience function to calculate experiment metrics.
    
    Args:
        engagement_data: Engagement records
        config: Experiment configuration
        
    Returns:
        Experiment metrics dictionary
    """
    agent = ExperimentationAgent(config)
    return agent.calculate_metrics(engagement_data)


def calculate_lift(treatment_metric: float, control_metric: float) -> float:
    """
    Calculate relative lift between treatment and control.
    
    Args:
        treatment_metric: Treatment arm metric value
        control_metric: Control arm metric value
        
    Returns:
        Relative lift percentage
    """
    if control_metric == 0:
        return 0
    return ((treatment_metric - control_metric) / control_metric) * 100