"""
Module: segmentation_agent.py
Purpose: Customer segmentation using rule-based or clustering approaches.

This module implements the Segmentation Agent responsible for grouping
customers into meaningful cohorts based on behavioral and demographic features.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# Configure logger
logger = logging.getLogger(__name__)

# Segmentation constants
SEGMENT_LABELS = {
    "High-Value Recent": "High spending customers with recent engagement",
    "At-Risk": "Previously active customers with declining engagement",
    "New Customer": "Customers with low purchase frequency",
    "Standard": "Regular customers with moderate activity",
    "Loyal Frequent": "High frequency customers with consistent engagement",
}


def load_customer_data(filepath: str) -> pd.DataFrame:
    """
    Load customer data from CSV file and validate schema.

    Args:
        filepath: Path to customer CSV file

    Returns:
        Validated customer DataFrame

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing or data is invalid
    """
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} customers from {filepath}")

        # Validate schema
        required_columns = [
            "customer_id",
            "age",
            "location",
            "tier",
            "purchase_frequency",
            "avg_order_value",
            "last_engagement_days",
            "historical_open_rate",
            "historical_click_rate",
        ]

        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Validate data constraints
        if df["customer_id"].duplicated().any():
            raise ValueError("Duplicate customer IDs found")

        if not (df["age"] >= 18).all():
            raise ValueError("Age must be >= 18 for all customers")

        if not ((df["historical_open_rate"] >= 0) & (df["historical_open_rate"] <= 1)).all():
            raise ValueError("Historical open rate must be between 0 and 1")

        if not ((df["historical_click_rate"] >= 0) & (df["historical_click_rate"] <= 1)).all():
            raise ValueError("Historical click rate must be between 0 and 1")

        if not (df["purchase_frequency"] >= 0).all():
            raise ValueError("Purchase frequency must be non-negative")

        if not (df["avg_order_value"] >= 0).all():
            raise ValueError("Average order value must be non-negative")

        logger.info("✓ Customer data validation passed")
        return df

    except FileNotFoundError:
        logger.error(f"Customer data file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error loading customer data: {e}")
        raise


def segment_customers(df: pd.DataFrame, method: str = "rules") -> pd.DataFrame:
    """
    Segment customers using specified method.

    Args:
        df: Customer dataframe with required features
        method: "rules" for rule-based, "kmeans" for clustering

    Returns:
        DataFrame with segment assignments

    Raises:
        ValueError: If method is unknown or data is invalid
    """
    if method == "rules":
        return _segment_by_rules(df)
    elif method == "kmeans":
        return _segment_by_clustering(df)
    else:
        raise ValueError(f"Unknown segmentation method: {method}")


def _segment_by_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule-based segmentation using RFM-like logic.

    Args:
        df: Customer dataframe

    Returns:
        DataFrame with segment assignments
    """
    logger.info("Applying rule-based segmentation...")

    segments = []

    for _, customer in df.iterrows():
        # Calculate engagement score
        engagement_score = (
            customer["historical_open_rate"] + customer["historical_click_rate"]
        ) / 2

        # High-Value Recent: High spending + recent activity
        if customer["avg_order_value"] > 200 and customer["last_engagement_days"] < 30:
            segment = "High-Value Recent"
            segment_id = 0

        # At-Risk: Previously active, declining engagement
        elif customer["purchase_frequency"] > 6 and customer["last_engagement_days"] > 30:
            segment = "At-Risk"
            segment_id = 1

        # New Customer: Low purchase frequency
        elif customer["purchase_frequency"] < 3:
            segment = "New Customer"
            segment_id = 2

        # Loyal Frequent: High frequency + good engagement
        elif customer["purchase_frequency"] > 12 and engagement_score > 0.4:
            segment = "Loyal Frequent"
            segment_id = 4

        else:
            segment = "Standard"
            segment_id = 3

        segments.append(
            {
                "customer_id": customer["customer_id"],
                "segment": segment,
                "segment_id": segment_id,
                "confidence": 1.0,  # Rule-based has full confidence
                "features": {
                    "avg_purchase_frequency": customer["purchase_frequency"],
                    "avg_order_value": customer["avg_order_value"],
                    "engagement_score": engagement_score,
                },
            }
        )

    result_df = pd.DataFrame(segments)

    # Log segment distribution
    segment_counts = result_df["segment"].value_counts()
    logger.info(f"Rule-based segmentation complete:")
    for segment, count in segment_counts.items():
        percentage = (count / len(result_df)) * 100
        logger.info(f"  {segment}: {count} customers ({percentage:.1f}%)")

    return result_df


def _segment_by_clustering(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """
    K-means clustering segmentation.

    Args:
        df: Customer dataframe
        n_clusters: Number of clusters (3-5 recommended)

    Returns:
        DataFrame with segment assignments
    """
    logger.info(f"Applying K-means clustering with {n_clusters} clusters...")

    # Select features for clustering
    feature_columns = [
        "age",
        "purchase_frequency",
        "avg_order_value",
        "last_engagement_days",
        "historical_open_rate",
        "historical_click_rate",
    ]

    # Prepare features
    features = df[feature_columns].copy()

    # Handle any missing values
    features = features.fillna(features.median())

    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Apply K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)

    # Calculate silhouette score
    silhouette_avg = silhouette_score(features_scaled, cluster_labels)
    logger.info(f"Silhouette score: {silhouette_avg:.3f}")

    # Generate segment names based on cluster characteristics
    segment_names = _generate_cluster_names(df, cluster_labels, features)

    # Create results
    segments = []
    for i, (_, customer) in enumerate(df.iterrows()):
        cluster_id = cluster_labels[i]
        segment_name = segment_names[cluster_id]

        # Calculate engagement score
        engagement_score = (
            customer["historical_open_rate"] + customer["historical_click_rate"]
        ) / 2

        segments.append(
            {
                "customer_id": customer["customer_id"],
                "segment": segment_name,
                "segment_id": cluster_id,
                "confidence": 0.8,  # Default confidence for clustering
                "features": {
                    "avg_purchase_frequency": customer["purchase_frequency"],
                    "avg_order_value": customer["avg_order_value"],
                    "engagement_score": engagement_score,
                },
            }
        )

    result_df = pd.DataFrame(segments)

    # Log segment distribution
    segment_counts = result_df["segment"].value_counts()
    logger.info(f"K-means segmentation complete:")
    for segment, count in segment_counts.items():
        percentage = (count / len(result_df)) * 100
        logger.info(f"  {segment}: {count} customers ({percentage:.1f}%)")

    return result_df


def _generate_cluster_names(
    df: pd.DataFrame, labels: np.ndarray, features: pd.DataFrame
) -> Dict[int, str]:
    """
    Generate human-readable names for clusters based on characteristics.

    Args:
        df: Original customer dataframe
        labels: Cluster labels
        features: Feature dataframe used for clustering

    Returns:
        Dictionary mapping cluster ID to segment name
    """
    cluster_names = {}

    for cluster_id in np.unique(labels):
        cluster_mask = labels == cluster_id
        cluster_data = df[cluster_mask]

        # Calculate cluster characteristics
        avg_order_value = cluster_data["avg_order_value"].mean()
        avg_frequency = cluster_data["purchase_frequency"].mean()
        avg_engagement_days = cluster_data["last_engagement_days"].mean()
        avg_open_rate = cluster_data["historical_open_rate"].mean()

        # Assign names based on characteristics
        if avg_order_value > 250 and avg_engagement_days < 20:
            name = "High-Value Recent"
        elif avg_frequency > 10 and avg_open_rate > 0.4:
            name = "Loyal Frequent"
        elif avg_frequency < 4:
            name = "New Customer"
        elif avg_engagement_days > 45:
            name = "At-Risk"
        else:
            name = "Standard"

        cluster_names[cluster_id] = name

    return cluster_names


def generate_segment_summary(segments_df: pd.DataFrame) -> Dict:
    """
    Generate segment summary report with statistics.

    Args:
        segments_df: DataFrame with segment assignments

    Returns:
        Dictionary with segment summary statistics
    """
    logger.info("Generating segment summary report...")

    total_customers = len(segments_df)
    unique_segments = segments_df["segment"].unique()

    summary = {
        "total_customers": total_customers,
        "num_segments": len(unique_segments),
        "segments": {},
    }

    for segment in unique_segments:
        segment_data = segments_df[segments_df["segment"] == segment]
        size = len(segment_data)
        percentage = (size / total_customers) * 100

        # Calculate segment characteristics
        avg_purchase_freq = (
            segment_data["features"].apply(lambda x: x["avg_purchase_frequency"]).mean()
        )
        avg_order_value = segment_data["features"].apply(lambda x: x["avg_order_value"]).mean()
        avg_engagement = segment_data["features"].apply(lambda x: x["engagement_score"]).mean()
        avg_confidence = segment_data["confidence"].mean()

        summary["segments"][segment] = {
            "size": size,
            "percentage": round(percentage, 1),
            "characteristics": {
                "avg_purchase_frequency": round(avg_purchase_freq, 1),
                "avg_order_value": round(avg_order_value, 2),
                "avg_engagement_score": round(avg_engagement, 3),
                "avg_confidence": round(avg_confidence, 3),
            },
            "definition": SEGMENT_LABELS.get(segment, "Custom segment"),
        }

    # Log summary
    logger.info(f"Segment Summary:")
    logger.info(f"  Total customers: {total_customers}")
    logger.info(f"  Number of segments: {len(unique_segments)}")

    for segment, data in summary["segments"].items():
        logger.info(f"  {segment}: {data['size']} customers ({data['percentage']}%)")

    return summary


def validate_segmentation(segments_df: pd.DataFrame) -> bool:
    """
    Validate segmentation results meet requirements.

    Args:
        segments_df: DataFrame with segment assignments

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    logger.info("Validating segmentation results...")

    # Check required columns exist first
    required_columns = ["customer_id", "segment", "segment_id", "confidence", "features"]
    missing_columns = set(required_columns) - set(segments_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Check each customer assigned exactly once
    if not segments_df["customer_id"].is_unique:
        raise ValueError("Each customer must be assigned to exactly one segment")

    # Check unique segments (3-5 required)
    unique_segments = segments_df["segment"].unique()
    if len(unique_segments) < 3 or len(unique_segments) > 5:
        raise ValueError(f"Must have 3-5 segments, got {len(unique_segments)}")

    # Check no segment is too small (< 10% of total)
    total_customers = len(segments_df)
    for segment in unique_segments:
        segment_size = len(segments_df[segments_df["segment"] == segment])
        percentage = (segment_size / total_customers) * 100
        if percentage < 10:
            logger.warning(f"Segment '{segment}' is small: {percentage:.1f}% of customers")

    logger.info("✓ Segmentation validation passed")
    return True


# Main function for testing
def main():
    """Main function for testing segmentation agent."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Load customer data
        df = load_customer_data("data/raw/customers.csv")

        # Test rule-based segmentation
        logger.info("Testing rule-based segmentation...")
        segments_rules = segment_customers(df, method="rules")
        validate_segmentation(segments_rules)
        summary_rules = generate_segment_summary(segments_rules)

        # Test K-means segmentation
        logger.info("Testing K-means segmentation...")
        segments_kmeans = segment_customers(df, method="kmeans")
        validate_segmentation(segments_kmeans)
        summary_kmeans = generate_segment_summary(segments_kmeans)

        logger.info("✓ All segmentation tests passed")

    except Exception as e:
        logger.error(f"Segmentation test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
