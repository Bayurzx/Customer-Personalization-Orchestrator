"""
Unit tests for the Experimentation Agent.

Tests cover experiment design, customer assignment, engagement simulation,
and metrics calculation functionality.

Author: AI Assistant  
Created: 2025-11-23
Task: 4.2 - Experimentation Agent Implementation
"""

import json
import pytest
from collections import Counter
from unittest.mock import patch, MagicMock

from src.agents.experimentation_agent import (
    ExperimentationAgent,
    design_experiment,
    assign_customers_to_arms,
    simulate_engagement,
    calculate_metrics,
    calculate_lift
)


class TestExperimentationAgent:
    """Test cases for ExperimentationAgent class."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample experiment configuration."""
        return {
            'experiment': {
                'name': 'test_experiment',
                'description': 'Test A/B/n experiment'
            },
            'experiment_id': 'TEST_EXP_001',
            'arms': {
                'control': {
                    'description': 'Generic control message',
                    'variant_type': 'generic'
                },
                'treatment_1': {
                    'description': 'Urgent tone treatment',
                    'variant_type': 'personalized'
                },
                'treatment_2': {
                    'description': 'Informational tone treatment', 
                    'variant_type': 'personalized'
                },
                'treatment_3': {
                    'description': 'Friendly tone treatment',
                    'variant_type': 'personalized'
                }
            },
            'control_message': {
                'subject': 'Test Control Subject',
                'body': 'Test control message body'
            },
            'assignment': {
                'method': 'stratified_random'
            },
            'sample_allocation': {
                'control_percent': 25,
                'treatment_percent': 75
            },
            'metrics': {
                'primary': 'click_rate',
                'secondary': ['open_rate', 'conversion_rate']
            },
            'statistical_testing': {
                'alpha': 0.05,
                'test_type': 't_test'
            },
            'simulation': {
                'baseline_rates': {
                    'open_rate': 0.25,
                    'click_rate': 0.05,
                    'conversion_rate': 0.01
                },
                'expected_uplift': {
                    'mean': 0.15,
                    'std_dev': 0.05,
                    'min_uplift': 0.05,
                    'max_uplift': 0.30
                },
                'noise_factor': 0.02
            },
            'segments': {
                'High-Value Recent': {
                    'expected_baseline_open': 0.30,
                    'expected_baseline_click': 0.08,
                    'expected_uplift': 0.20
                },
                'Standard': {
                    'expected_baseline_open': 0.25,
                    'expected_baseline_click': 0.05,
                    'expected_uplift': 0.15
                },
                'New Customer': {
                    'expected_baseline_open': 0.20,
                    'expected_baseline_click': 0.03,
                    'expected_uplift': 0.10
                }
            },
            'random_seed': 42
        }
    
    @pytest.fixture
    def sample_variants(self):
        """Sample message variants."""
        return [
            {
                'variant_id': 'VAR_001',
                'segment': 'High-Value Recent',
                'tone': 'urgent',
                'subject': 'Urgent: Limited Time Offer',
                'body': 'Act now for exclusive benefits!'
            },
            {
                'variant_id': 'VAR_002',
                'segment': 'High-Value Recent',
                'tone': 'informational',
                'subject': 'New Features Available',
                'body': 'Learn about our latest updates.'
            },
            {
                'variant_id': 'VAR_003',
                'segment': 'High-Value Recent',
                'tone': 'friendly',
                'subject': 'We have something special for you',
                'body': 'Check out what we have prepared!'
            },
            {
                'variant_id': 'VAR_004',
                'segment': 'Standard',
                'tone': 'urgent',
                'subject': 'Don\'t miss out!',
                'body': 'Limited time opportunity awaits.'
            },
            {
                'variant_id': 'VAR_005',
                'segment': 'Standard',
                'tone': 'informational',
                'subject': 'Product Update',
                'body': 'Here are the latest improvements.'
            },
            {
                'variant_id': 'VAR_006',
                'segment': 'Standard',
                'tone': 'friendly',
                'subject': 'Hello from our team',
                'body': 'We wanted to share some news with you.'
            }
        ]
    
    @pytest.fixture
    def sample_customers(self):
        """Sample customer data."""
        return [
            {
                'customer_id': 'C001',
                'segment': 'High-Value Recent',
                'features': {'avg_order_value': 250.0}
            },
            {
                'customer_id': 'C002',
                'segment': 'High-Value Recent',
                'features': {'avg_order_value': 300.0}
            },
            {
                'customer_id': 'C003',
                'segment': 'Standard',
                'features': {'avg_order_value': 150.0}
            },
            {
                'customer_id': 'C004',
                'segment': 'Standard',
                'features': {'avg_order_value': 120.0}
            },
            {
                'customer_id': 'C005',
                'segment': 'New Customer',
                'features': {'avg_order_value': 75.0}
            },
            {
                'customer_id': 'C006',
                'segment': 'New Customer',
                'features': {'avg_order_value': 80.0}
            },
            {
                'customer_id': 'C007',
                'segment': 'High-Value Recent',
                'features': {'avg_order_value': 280.0}
            },
            {
                'customer_id': 'C008',
                'segment': 'Standard',
                'features': {'avg_order_value': 140.0}
            }
        ]
    
    def test_agent_initialization(self, sample_config):
        """Test ExperimentationAgent initialization."""
        agent = ExperimentationAgent(sample_config)
        
        assert agent.config == sample_config
        assert agent.experiment_id is None
        assert agent.assignments == []
        assert agent.engagement_data == []
        assert agent.metrics == {}
    
    def test_agent_initialization_without_config(self):
        """Test agent initialization with default config."""
        agent = ExperimentationAgent()
        
        assert agent.config == {}
        assert agent.experiment_id is None
    
    def test_design_experiment(self, sample_variants, sample_config):
        """Test experiment design functionality."""
        agent = ExperimentationAgent(sample_config)
        
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        
        # Check basic structure
        assert 'experiment_id' in experiment_design
        assert experiment_design['name'] == 'test_experiment'
        assert 'arms' in experiment_design
        assert 'segments' in experiment_design
        
        # Check arms
        arms = experiment_design['arms']
        assert 'control' in arms
        assert 'treatment_1' in arms
        assert 'treatment_2' in arms
        assert 'treatment_3' in arms
        
        # Check segments detected
        segments = experiment_design['segments']
        assert 'High-Value Recent' in segments
        assert 'Standard' in segments
        
        # Check experiment ID is set
        assert agent.experiment_id == 'TEST_EXP_001'
    
    def test_assign_customers_to_arms(self, sample_customers, sample_variants, sample_config):
        """Test customer assignment to experiment arms."""
        agent = ExperimentationAgent(sample_config)
        
        # First design the experiment
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        
        # Then assign customers
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
        
        # Check all customers are assigned
        assert len(assignments) == len(sample_customers)
        
        # Check assignment structure
        for assignment in assignments:
            assert 'customer_id' in assignment
            assert 'segment' in assignment
            assert 'experiment_arm' in assignment
            assert 'variant_id' in assignment
            assert 'assigned_at' in assignment
            assert 'assignment_method' in assignment
        
        # Check all customers have assignments
        assigned_customers = {a['customer_id'] for a in assignments}
        original_customers = {c['customer_id'] for c in sample_customers}
        assert assigned_customers == original_customers
        
        # Check arms distribution
        arm_counts = Counter(a['experiment_arm'] for a in assignments)
        assert 'control' in arm_counts
        assert len(arm_counts) <= 4  # control + 3 treatments
        
        # Store assignments for later tests
        agent.assignments = assignments
    
    def test_assignment_balance_validation(self, sample_customers, sample_variants, sample_config):
        """Test that assignment balance validation works."""
        agent = ExperimentationAgent(sample_config)
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        
        # This should not raise an exception for balanced assignment
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
        
        # Check that we have assignments for all arms
        arm_counts = Counter(a['experiment_arm'] for a in assignments)
        assert len(arm_counts) >= 2  # At least control and one treatment
    
    def test_simulate_engagement(self, sample_customers, sample_variants, sample_config):
        """Test engagement simulation."""
        agent = ExperimentationAgent(sample_config)
        
        # Setup experiment and assignments
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
        
        # Simulate engagement
        engagement_data = agent.simulate_engagement(assignments, sample_config)
        
        # Check structure
        assert len(engagement_data) == len(assignments)
        
        for record in engagement_data:
            assert 'customer_id' in record
            assert 'segment' in record
            assert 'experiment_arm' in record
            assert 'variant_id' in record
            assert 'opened' in record
            assert 'clicked' in record
            assert 'converted' in record
            assert 'engagement_at' in record
            assert 'engagement_source' in record
            
            # Check data types
            assert isinstance(record['opened'], bool)
            assert isinstance(record['clicked'], bool)
            assert isinstance(record['converted'], bool)
            
            # Check logical constraints
            if record['clicked']:
                assert record['opened']  # Can't click without opening
            if record['converted']:
                assert record['clicked']  # Can't convert without clicking
    
    def test_calculate_metrics(self, sample_customers, sample_variants, sample_config):
        """Test metrics calculation."""
        agent = ExperimentationAgent(sample_config)
        
        # Setup full experiment
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
        engagement_data = agent.simulate_engagement(assignments, sample_config)
        
        # Calculate metrics
        metrics = agent.calculate_metrics(engagement_data)
        
        # Check structure
        assert 'experiment_id' in metrics
        assert 'arms' in metrics
        assert 'lift_analysis' in metrics
        assert 'segment_breakdown' in metrics
        assert 'computed_at' in metrics
        
        # Check arms metrics
        arms = metrics['arms']
        for arm_name, arm_data in arms.items():
            assert 'arm_name' in arm_data
            assert 'sample_size' in arm_data
            assert 'metrics' in arm_data
            assert 'counts' in arm_data
            
            # Check metrics structure
            arm_metrics = arm_data['metrics']
            assert 'open_rate' in arm_metrics
            assert 'click_rate' in arm_metrics
            assert 'conversion_rate' in arm_metrics
            
            # Check rates are valid probabilities
            for rate in arm_metrics.values():
                assert 0 <= rate <= 1
        
        # Check lift analysis
        lift_analysis = metrics['lift_analysis']
        for lift_record in lift_analysis:
            assert 'treatment_arm' in lift_record
            assert 'metric' in lift_record
            assert 'lift_percent' in lift_record
            assert 'statistical_significance' in lift_record
    
    def test_segment_breakdown_calculation(self, sample_customers, sample_variants, sample_config):
        """Test segment breakdown calculation."""
        agent = ExperimentationAgent(sample_config)
        
        # Setup experiment
        experiment_design = agent.design_experiment(sample_variants, sample_config)
        assignments = agent.assign_customers_to_arms(sample_customers, experiment_design)
        engagement_data = agent.simulate_engagement(assignments, sample_config)
        
        # Calculate metrics
        metrics = agent.calculate_metrics(engagement_data)
        
        # Check segment breakdown
        segment_breakdown = metrics['segment_breakdown']
        
        # Should have breakdown for each segment
        segments_in_breakdown = {item['segment'] for item in segment_breakdown}
        original_segments = {c['segment'] for c in sample_customers}
        assert segments_in_breakdown == original_segments
        
        for segment_data in segment_breakdown:
            assert 'segment' in segment_data
            assert 'sample_size' in segment_data
            assert 'best_performing_arm' in segment_data
            assert 'lift_percent' in segment_data


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for convenience function tests."""
        return {
            'experiment': {'name': 'test', 'description': 'test'},
            'experiment_id': 'TEST_001',
            'arms': {
                'control': {'description': 'control'},
                'treatment_1': {'description': 'treatment 1'},
                'treatment_2': {'description': 'treatment 2'},
                'treatment_3': {'description': 'treatment 3'}
            },
            'control_message': {'subject': 'test', 'body': 'test'},
            'assignment': {'method': 'stratified_random'},
            'sample_allocation': {'control_percent': 25, 'treatment_percent': 75},
            'metrics': {'primary': 'click_rate'},
            'statistical_testing': {'alpha': 0.05},
            'simulation': {
                'baseline_rates': {'open_rate': 0.25, 'click_rate': 0.05, 'conversion_rate': 0.01},
                'expected_uplift': {'mean': 0.15, 'std_dev': 0.05, 'min_uplift': 0.05, 'max_uplift': 0.30},
                'noise_factor': 0.02
            },
            'random_seed': 42
        }
    
    def test_design_experiment_function(self, sample_config):
        """Test design_experiment convenience function."""
        variants = [
            {'variant_id': 'V1', 'segment': 'Test', 'tone': 'urgent'}
        ]
        
        result = design_experiment(variants, sample_config)
        
        assert 'experiment_id' in result
        assert 'arms' in result
    
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
        assert abs(lift - (-20.0)) < 0.001  # 20% decrease (allow for floating point precision)
    
    def test_assign_customers_to_arms_function(self, sample_config):
        """Test assign_customers_to_arms convenience function."""
        customers = [
            {'customer_id': 'C1', 'segment': 'Test'},
            {'customer_id': 'C2', 'segment': 'Test'}
        ]
        variants = [
            {'variant_id': 'V1', 'segment': 'Test', 'tone': 'urgent'}
        ]
        
        assignments = assign_customers_to_arms(customers, variants, sample_config)
        
        assert len(assignments) == len(customers)
        assert all('customer_id' in a for a in assignments)
    
    def test_simulate_engagement_function(self, sample_config):
        """Test simulate_engagement convenience function."""
        assignments = [
            {
                'customer_id': 'C1',
                'segment': 'Test',
                'experiment_arm': 'control',
                'variant_id': 'control'
            }
        ]
        
        engagement = simulate_engagement(assignments, sample_config)
        
        assert len(engagement) == len(assignments)
        assert all('opened' in e for e in engagement)
    
    def test_calculate_metrics_function(self, sample_config):
        """Test calculate_metrics convenience function."""
        engagement_data = [
            {
                'customer_id': 'C1',
                'segment': 'Test',
                'experiment_arm': 'control',
                'variant_id': 'control',
                'opened': True,
                'clicked': False,
                'converted': False
            }
        ]
        
        metrics = calculate_metrics(engagement_data, sample_config)
        
        assert 'arms' in metrics
        assert 'lift_analysis' in metrics


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
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
        result = agent.design_experiment([], config)
        assert 'experiment_id' in result
        assert result['segments'] == []
    
    def test_empty_customers_list(self):
        """Test handling of empty customers list."""
        agent = ExperimentationAgent()
        experiment_design = {
            'experiment_id': 'TEST',
            'arms': {'control': {'name': 'control'}},
            'segments': [],
            'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}
        }
        
        assignments = agent.assign_customers_to_arms([], experiment_design)
        assert assignments == []
    
    def test_single_customer_assignment(self):
        """Test assignment with single customer."""
        agent = ExperimentationAgent({'random_seed': 42})
        customers = [{'customer_id': 'C1', 'segment': 'Test'}]
        experiment_design = {
            'experiment_id': 'TEST',
            'arms': {
                'control': {'name': 'control', 'variants_by_segment': {}},
                'treatment_1': {'name': 'treatment_1', 'variants_by_segment': {}}
            },
            'segments': ['Test'],
            'sample_allocation': {'control_percent': 25, 'treatment_percent': 75}
        }
        
        assignments = agent.assign_customers_to_arms(customers, experiment_design)
        assert len(assignments) == 1
        assert assignments[0]['customer_id'] == 'C1'
    
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
        assert isinstance(result['significant'], bool)
    
    def test_zero_engagement_rates(self):
        """Test metrics calculation with zero engagement."""
        agent = ExperimentationAgent()
        
        engagement_data = [
            {
                'customer_id': 'C1',
                'segment': 'Test',
                'experiment_arm': 'control',
                'variant_id': 'control',
                'opened': False,
                'clicked': False,
                'converted': False
            }
        ]
        
        metrics = agent.calculate_metrics(engagement_data)
        
        # Should handle zero rates gracefully
        control_metrics = metrics['arms']['control']['metrics']
        assert control_metrics['open_rate'] == 0
        assert control_metrics['click_rate'] == 0
        assert control_metrics['conversion_rate'] == 0


if __name__ == '__main__':
    pytest.main([__file__])