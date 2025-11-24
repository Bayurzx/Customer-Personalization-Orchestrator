"""
Simple integration tests for the Customer Personalization Orchestrator.

These tests verify basic end-to-end functionality with minimal mocking.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

# Import agents
from src.agents.segmentation_agent import segment_customers
from src.agents.experimentation_agent import ExperimentationAgent


class TestBasicIntegration:
    """Test basic integration between components."""

    def setup_method(self):
        """Set up test data."""
        # Create sample customer data
        self.sample_customers = pd.DataFrame(
            {
                "customer_id": ["C001", "C002", "C003", "C004", "C005"],
                "age": [35, 28, 42, 31, 39],
                "location": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"],
                "tier": ["Gold", "Silver", "Gold", "Bronze", "Silver"],
                "purchase_frequency": [12, 6, 18, 3, 8],
                "avg_order_value": [250.0, 150.0, 300.0, 80.0, 180.0],
                "last_engagement_days": [5, 30, 3, 60, 20],
                "historical_open_rate": [0.45, 0.35, 0.50, 0.25, 0.40],
                "historical_click_rate": [0.12, 0.08, 0.15, 0.05, 0.10],
            }
        )

        # Sample configuration
        self.config = {
            "experiment": {
                "name": "integration_test",
                "arms": ["control", "treatment_1", "treatment_2"],
                "allocation": {"control": 0.33, "treatment_1": 0.33, "treatment_2": 0.34},
            },
            "simulation": {
                "baseline_open_rate": 0.25,
                "baseline_click_rate": 0.05,
                "uplift_mean": 0.10,
                "uplift_std": 0.05,
                "random_seed": 42,
            },
        }

    def test_segmentation_works(self):
        """Test that segmentation produces valid output."""
        # Test segmentation
        segments_df = segment_customers(self.sample_customers, method="rules")

        # Verify segmentation worked
        assert len(segments_df) == len(self.sample_customers)
        assert "segment" in segments_df.columns
        assert "customer_id" in segments_df.columns

        # Check that all customers are assigned to segments
        assert segments_df["segment"].notna().all()

        # Check that we have multiple segments
        unique_segments = segments_df["segment"].unique()
        assert len(unique_segments) >= 2

    def test_experimentation_with_segments(self):
        """Test that experimentation works with segmented customers."""
        # First segment customers
        segments_df = segment_customers(self.sample_customers, method="rules")

        # Merge segments back to customers
        customers_with_segments = self.sample_customers.merge(
            segments_df[["customer_id", "segment"]], on="customer_id"
        )

        # Sample approved variants
        approved_variants = [
            {
                "variant_id": "VAR001",
                "customer_id": "C001",
                "segment": "High-Value Recent",
                "subject": "Exclusive Offer",
                "body": "Test message 1",
                "tone": "urgent",
            },
            {
                "variant_id": "VAR002",
                "customer_id": "C002",
                "segment": "New Customer",
                "subject": "Welcome Message",
                "body": "Test message 2",
                "tone": "friendly",
            },
        ]

        # Create experimentation agent
        exp_agent = ExperimentationAgent(self.config)

        # Test experiment design
        experiment = exp_agent.design_experiment(approved_variants, self.config)

        assert "experiment_id" in experiment
        assert "arms" in experiment
        assert len(experiment["arms"]) >= 2  # At least control + 1 treatment

        # Test customer assignment with segmented customers
        assignments = exp_agent.assign_customers_to_arms(
            customers_with_segments.to_dict("records"), experiment
        )

        assert len(assignments) == len(customers_with_segments)
        assert all("experiment_arm" in assignment for assignment in assignments)

        # Test engagement simulation
        engagement = exp_agent.simulate_engagement(assignments, self.config)

        assert len(engagement) == len(assignments)
        assert all("opened" in record for record in engagement)
        assert all("clicked" in record for record in engagement)

        # Test metrics calculation
        metrics = exp_agent.calculate_metrics(engagement)

        assert "arms" in metrics
        assert len(metrics["arms"]) > 0
        assert all(
            "open_rate" in arm_metrics["metrics"] for arm_metrics in metrics["arms"].values()
        )

    def test_data_flow_consistency(self):
        """Test that data formats are consistent across components."""
        # Test customer data format
        customers_df = self.sample_customers

        # Test segmentation accepts this format
        segments_df = segment_customers(customers_df, method="rules")
        assert len(segments_df) == len(customers_df)

        # Test that customer records can be converted for experimentation
        customers_records = customers_df.to_dict("records")
        assert len(customers_records) == len(customers_df)
        assert "customer_id" in customers_records[0]

        # Test that segments can be merged back
        customers_with_segments = customers_df.merge(
            segments_df[["customer_id", "segment"]], on="customer_id"
        )
        assert len(customers_with_segments) == len(customers_df)
        assert "segment" in customers_with_segments.columns

    def test_end_to_end_pipeline_structure(self):
        """Test the overall pipeline structure without external dependencies."""
        # Step 1: Segmentation
        segments_df = segment_customers(self.sample_customers, method="rules")
        assert len(segments_df) > 0

        # Step 2: Merge segments with customers
        customers_with_segments = self.sample_customers.merge(
            segments_df[["customer_id", "segment"]], on="customer_id"
        )

        # Step 3: Create mock variants (simulating generation + safety)
        unique_segments = segments_df["segment"].unique()
        approved_variants = []

        for i, segment_name in enumerate(unique_segments):
            variant = {
                "variant_id": f"VAR{i+1:03d}",
                "customer_id": f"C{i+1:03d}",
                "segment": segment_name,
                "subject": f"Message for {segment_name}",
                "body": f"This is a test message for {segment_name} customers.",
                "tone": "friendly",
            }
            approved_variants.append(variant)

        assert len(approved_variants) > 0

        # Step 4: Experimentation
        exp_agent = ExperimentationAgent(self.config)
        experiment = exp_agent.design_experiment(approved_variants, self.config)

        assert "experiment_id" in experiment

        # Assign customers
        assignments = exp_agent.assign_customers_to_arms(
            customers_with_segments.to_dict("records"), experiment
        )

        assert len(assignments) == len(customers_with_segments)

        # Simulate engagement
        engagement = exp_agent.simulate_engagement(assignments, self.config)

        assert len(engagement) == len(assignments)

        # Calculate metrics
        metrics = exp_agent.calculate_metrics(engagement)

        assert "arms" in metrics
        assert len(metrics["arms"]) > 0

        # Verify we have meaningful results
        total_customers = sum(
            arm_metrics["sample_size"] for arm_metrics in metrics["arms"].values()
        )
        assert total_customers == len(customers_with_segments)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
