"""
Unit tests for segmentation_agent.py

Tests the customer segmentation functionality including rule-based and
K-means clustering approaches.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.agents.segmentation_agent import (
    load_customer_data,
    segment_customers,
    generate_segment_summary,
    validate_segmentation,
    _segment_by_rules,
    _segment_by_clustering,
    _generate_cluster_names,
)


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004", "C005", "C006", "C007"],
            "age": [35, 28, 42, 31, 29, 45, 33],
            "location": [
                "New York",
                "Los Angeles",
                "Chicago",
                "Houston",
                "Phoenix",
                "Philadelphia",
                "San Antonio",
            ],
            "tier": ["Gold", "Silver", "Gold", "Bronze", "Silver", "Gold", "Bronze"],
            "purchase_frequency": [
                12,
                8,
                18,
                2,
                15,
                7,
                1,
            ],  # Adjusted to trigger different segments
            "avg_order_value": [
                250.0,
                150.0,
                300.0,
                75.0,
                320.0,
                180.0,
                50.0,
            ],  # Added high-value and low-value
            "last_engagement_days": [5, 35, 3, 45, 10, 50, 90],  # Mix of recent and at-risk
            "historical_open_rate": [0.45, 0.35, 0.50, 0.20, 0.52, 0.30, 0.18],
            "historical_click_rate": [0.12, 0.08, 0.15, 0.04, 0.18, 0.06, 0.03],
        }
    )


@pytest.fixture
def sample_csv_file(sample_customer_data):
    """Create temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_customer_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)


class TestLoadCustomerData:
    """Test customer data loading and validation."""

    def test_load_valid_data(self, sample_csv_file):
        """Test loading valid customer data."""
        df = load_customer_data(sample_csv_file)

        assert len(df) == 7  # Updated to match new sample data size
        assert "customer_id" in df.columns
        assert df["customer_id"].is_unique
        assert (df["age"] >= 18).all()

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_customer_data("nonexistent.csv")

    def test_missing_columns(self):
        """Test missing required columns raises error."""
        # Create CSV with missing columns
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame({"customer_id": ["C001"], "age": [25]})
            df.to_csv(f.name, index=False)

            with pytest.raises(ValueError, match="Missing required columns"):
                load_customer_data(f.name)

            os.unlink(f.name)

    def test_duplicate_customer_ids(self):
        """Test duplicate customer IDs raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame(
                {
                    "customer_id": ["C001", "C001"],  # Duplicate
                    "age": [25, 30],
                    "location": ["NY", "LA"],
                    "tier": ["Gold", "Silver"],
                    "purchase_frequency": [5, 10],
                    "avg_order_value": [100.0, 200.0],
                    "last_engagement_days": [10, 20],
                    "historical_open_rate": [0.3, 0.4],
                    "historical_click_rate": [0.1, 0.2],
                }
            )
            df.to_csv(f.name, index=False)

            with pytest.raises(ValueError, match="Duplicate customer IDs"):
                load_customer_data(f.name)

            os.unlink(f.name)

    def test_invalid_age(self):
        """Test invalid age values raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame(
                {
                    "customer_id": ["C001"],
                    "age": [15],  # Under 18
                    "location": ["NY"],
                    "tier": ["Gold"],
                    "purchase_frequency": [5],
                    "avg_order_value": [100.0],
                    "last_engagement_days": [10],
                    "historical_open_rate": [0.3],
                    "historical_click_rate": [0.1],
                }
            )
            df.to_csv(f.name, index=False)

            with pytest.raises(ValueError, match="Age must be >= 18"):
                load_customer_data(f.name)

            os.unlink(f.name)


class TestSegmentCustomers:
    """Test customer segmentation methods."""

    def test_segment_customers_rules(self, sample_customer_data):
        """Test rule-based segmentation."""
        segments = segment_customers(sample_customer_data, method="rules")

        assert len(segments) == len(sample_customer_data)
        assert "customer_id" in segments.columns
        assert "segment" in segments.columns
        assert "segment_id" in segments.columns
        assert "confidence" in segments.columns
        assert "features" in segments.columns

        # Check all customers assigned
        assert segments["customer_id"].is_unique

        # Check segment types
        unique_segments = segments["segment"].unique()
        assert len(unique_segments) >= 3
        assert len(unique_segments) <= 5

    def test_segment_customers_kmeans(self, sample_customer_data):
        """Test K-means segmentation."""
        segments = segment_customers(sample_customer_data, method="kmeans")

        assert len(segments) == len(sample_customer_data)
        assert "customer_id" in segments.columns
        assert "segment" in segments.columns
        assert "segment_id" in segments.columns

        # Check all customers assigned
        assert segments["customer_id"].is_unique

    def test_invalid_method(self, sample_customer_data):
        """Test invalid segmentation method raises error."""
        with pytest.raises(ValueError, match="Unknown segmentation method"):
            segment_customers(sample_customer_data, method="invalid")


class TestRuleBasedSegmentation:
    """Test rule-based segmentation logic."""

    def test_high_value_recent_segment(self, sample_customer_data):
        """Test High-Value Recent segment assignment."""
        segments = _segment_by_rules(sample_customer_data)

        # Check that High-Value Recent segment exists and has expected characteristics
        high_value_customers = segments[segments["segment"] == "High-Value Recent"]

        if len(high_value_customers) > 0:
            # Verify characteristics of High-Value Recent customers
            for _, customer in high_value_customers.iterrows():
                customer_id = customer["customer_id"]
                orig_data = sample_customer_data[
                    sample_customer_data["customer_id"] == customer_id
                ].iloc[0]

                # Should have high AOV (>200) and recent engagement (<30 days)
                assert orig_data["avg_order_value"] > 200
                assert orig_data["last_engagement_days"] < 30

    def test_at_risk_segment(self, sample_customer_data):
        """Test At-Risk segment assignment."""
        segments = _segment_by_rules(sample_customer_data)

        # Check At-Risk segment characteristics
        at_risk_customers = segments[segments["segment"] == "At-Risk"]

        if len(at_risk_customers) > 0:
            # Verify characteristics of At-Risk customers
            for _, customer in at_risk_customers.iterrows():
                customer_id = customer["customer_id"]
                orig_data = sample_customer_data[
                    sample_customer_data["customer_id"] == customer_id
                ].iloc[0]

                # Should have high frequency (>6) and poor recent engagement (>30 days)
                assert orig_data["purchase_frequency"] > 6
                assert orig_data["last_engagement_days"] > 30

        # At minimum, should be a DataFrame
        assert isinstance(at_risk_customers, pd.DataFrame)

    def test_new_customer_segment(self, sample_customer_data):
        """Test New Customer segment assignment."""
        segments = _segment_by_rules(sample_customer_data)

        # Check New Customer segment characteristics
        new_customers = segments[segments["segment"] == "New Customer"]

        if len(new_customers) > 0:
            # Verify characteristics of New Customers
            for _, customer in new_customers.iterrows():
                customer_id = customer["customer_id"]
                orig_data = sample_customer_data[
                    sample_customer_data["customer_id"] == customer_id
                ].iloc[0]

                # Should have low purchase frequency (<3)
                assert orig_data["purchase_frequency"] < 3

        # At minimum, should be a DataFrame
        assert isinstance(new_customers, pd.DataFrame)

    def test_confidence_scores(self, sample_customer_data):
        """Test confidence scores for rule-based segmentation."""
        segments = _segment_by_rules(sample_customer_data)

        # Rule-based should have confidence = 1.0
        assert (segments["confidence"] == 1.0).all()

    def test_features_calculation(self, sample_customer_data):
        """Test feature calculation in segmentation."""
        segments = _segment_by_rules(sample_customer_data)

        # Check features are calculated correctly
        for _, row in segments.iterrows():
            features = row["features"]
            assert "avg_purchase_frequency" in features
            assert "avg_order_value" in features
            assert "engagement_score" in features

            # Engagement score should be between 0 and 1
            assert 0 <= features["engagement_score"] <= 1


class TestKMeansSegmentation:
    """Test K-means clustering segmentation."""

    def test_clustering_with_valid_data(self, sample_customer_data):
        """Test K-means clustering with valid data."""
        segments = _segment_by_clustering(sample_customer_data, n_clusters=3)

        assert len(segments) == len(sample_customer_data)
        assert segments["customer_id"].is_unique

        # Check cluster IDs are in valid range
        cluster_ids = segments["segment_id"].unique()
        assert len(cluster_ids) <= 3
        assert all(0 <= cid < 3 for cid in cluster_ids)

    def test_cluster_name_generation(self, sample_customer_data):
        """Test cluster name generation."""
        # Mock clustering results - must match sample data length (7 customers)
        labels = np.array([0, 1, 0, 2, 1, 2, 3])  # 7 labels for 7 customers
        features = sample_customer_data[
            [
                "age",
                "purchase_frequency",
                "avg_order_value",
                "last_engagement_days",
                "historical_open_rate",
                "historical_click_rate",
            ]
        ]

        names = _generate_cluster_names(sample_customer_data, labels, features)

        assert isinstance(names, dict)
        assert len(names) == 4  # 4 unique clusters (0, 1, 2, 3)

        # Check all names are valid segment types
        valid_segments = {
            "High-Value Recent",
            "At-Risk",
            "New Customer",
            "Standard",
            "Loyal Frequent",
        }
        for name in names.values():
            assert name in valid_segments


class TestSegmentSummary:
    """Test segment summary generation."""

    def test_generate_summary(self, sample_customer_data):
        """Test segment summary generation."""
        segments = segment_customers(sample_customer_data, method="rules")
        summary = generate_segment_summary(segments)

        assert "total_customers" in summary
        assert "num_segments" in summary
        assert "segments" in summary

        assert summary["total_customers"] == len(sample_customer_data)
        assert summary["num_segments"] > 0

        # Check segment details
        for segment_name, segment_data in summary["segments"].items():
            assert "size" in segment_data
            assert "percentage" in segment_data
            assert "characteristics" in segment_data
            assert "definition" in segment_data

            # Check characteristics
            chars = segment_data["characteristics"]
            assert "avg_purchase_frequency" in chars
            assert "avg_order_value" in chars
            assert "avg_engagement_score" in chars
            assert "avg_confidence" in chars

    def test_summary_percentages_sum_to_100(self, sample_customer_data):
        """Test that segment percentages sum to approximately 100%."""
        segments = segment_customers(sample_customer_data, method="rules")
        summary = generate_segment_summary(segments)

        total_percentage = sum(data["percentage"] for data in summary["segments"].values())
        assert abs(total_percentage - 100.0) < 0.1  # Allow small rounding errors


class TestValidateSegmentation:
    """Test segmentation validation."""

    def test_valid_segmentation(self, sample_customer_data):
        """Test validation of valid segmentation."""
        segments = segment_customers(sample_customer_data, method="rules")

        # Should not raise any exceptions
        assert validate_segmentation(segments) is True

    def test_too_few_segments(self, sample_customer_data):
        """Test validation fails with too few segments."""
        # Create segmentation with only 2 segments
        segments = pd.DataFrame(
            {
                "customer_id": ["C001", "C002", "C003"],
                "segment": ["A", "A", "B"],  # Only 2 unique segments
                "segment_id": [0, 0, 1],
                "confidence": [1.0, 1.0, 1.0],
                "features": [{"test": 1}, {"test": 2}, {"test": 3}],
            }
        )

        with pytest.raises(ValueError, match="Must have 3-5 segments"):
            validate_segmentation(segments)

    def test_duplicate_customers(self, sample_customer_data):
        """Test validation fails with duplicate customers."""
        segments = pd.DataFrame(
            {
                "customer_id": ["C001", "C001", "C002", "C003"],  # Duplicate C001
                "segment": ["A", "B", "C", "A"],  # 3 unique segments
                "segment_id": [0, 1, 2, 0],
                "confidence": [1.0, 1.0, 1.0, 1.0],
                "features": [{"test": 1}, {"test": 2}, {"test": 3}, {"test": 4}],
            }
        )

        with pytest.raises(ValueError, match="exactly one segment"):
            validate_segmentation(segments)

    def test_missing_columns(self):
        """Test validation fails with missing columns."""
        segments = pd.DataFrame(
            {
                "customer_id": ["C001", "C002", "C003"],
                "segment": ["A", "B", "C"],
                # Missing required columns: segment_id, confidence, features
            }
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_segmentation(segments)


class TestIntegration:
    """Integration tests for the full segmentation workflow."""

    def test_full_workflow_rules(self, sample_csv_file):
        """Test complete workflow with rule-based segmentation."""
        # Load data
        df = load_customer_data(sample_csv_file)

        # Segment customers
        segments = segment_customers(df, method="rules")

        # Validate segmentation
        validate_segmentation(segments)

        # Generate summary
        summary = generate_segment_summary(segments)

        # Verify results
        assert len(segments) == len(df)
        assert summary["total_customers"] == len(df)
        assert summary["num_segments"] >= 3

    def test_full_workflow_kmeans(self, sample_csv_file):
        """Test complete workflow with K-means segmentation."""
        # Load data
        df = load_customer_data(sample_csv_file)

        # Segment customers
        segments = segment_customers(df, method="kmeans")

        # Validate segmentation
        validate_segmentation(segments)

        # Generate summary
        summary = generate_segment_summary(segments)

        # Verify results
        assert len(segments) == len(df)
        assert summary["total_customers"] == len(df)


if __name__ == "__main__":
    pytest.main([__file__])
