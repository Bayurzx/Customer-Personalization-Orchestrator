#!/usr/bin/env python3
"""
End-to-End Experiment Execution Script
Customer Personalization Orchestrator

This script orchestrates the complete personalization experiment pipeline:
1. Load and segment customers
2. Retrieve relevant content for each segment
3. Generate personalized message variants
4. Screen variants for safety compliance
5. Design and execute A/B/n experiment
6. Calculate metrics and generate results

Usage:
    python scripts/run_experiment.py [--config CONFIG_PATH] [--customers CUSTOMER_PATH]

Author: AI Assistant
Created: 2025-11-23
Task: 4.5 - Experiment Execution Script
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np
import yaml
from tqdm import tqdm

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all agents
from src.agents.segmentation_agent import segment_customers, load_customer_data
from src.agents.retrieval_agent import retrieve_content
from src.agents.generation_agent import generate_variants
from src.agents.safety_agent import check_safety
from src.agents.experimentation_agent import ExperimentationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/experiment.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ExperimentPipeline:
    """
    End-to-end experiment execution pipeline.

    Orchestrates all agents to run a complete personalization experiment
    from customer data to final results.
    """

    def __init__(self, config_path: str = "config/experiment_config.yaml"):
        """
        Initialize the experiment pipeline.

        Args:
            config_path: Path to experiment configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {}
        self.start_time = None
        self.end_time = None

        # Create output directories
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        logger.info(f"Initialized experiment pipeline: {self.config['experiment']['name']}")

    def _load_config(self) -> Dict[str, Any]:
        """Load experiment configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise

    def _json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def run_full_experiment(
        self, customer_data_path: str = "data/raw/customers.csv"
    ) -> Dict[str, Any]:
        """
        Execute the complete experiment pipeline.

        Args:
            customer_data_path: Path to customer data CSV file

        Returns:
            Dictionary containing all experiment results
        """
        self.start_time = datetime.utcnow()
        logger.info("🚀 Starting full experiment pipeline")

        try:
            # Step 1: Load and segment customers
            logger.info("📊 Step 1: Customer Segmentation")
            customers_df, segments_df = self._run_segmentation(customer_data_path)

            # Step 2: Retrieve content for each segment
            logger.info("🔍 Step 2: Content Retrieval")
            retrieved_content = self._run_content_retrieval(segments_df)

            # Step 3: Generate message variants
            logger.info("✍️ Step 3: Message Generation")
            variants = self._run_message_generation(segments_df, retrieved_content)

            # Step 4: Safety screening
            logger.info("🛡️ Step 4: Safety Screening")
            safe_variants = self._run_safety_screening(variants)

            # Step 5: Experiment design and execution
            logger.info("🧪 Step 5: Experiment Execution")
            experiment_results = self._run_experiment(customers_df, safe_variants)

            # Step 6: Generate final summary
            self.end_time = datetime.utcnow()
            final_results = self._generate_final_summary(experiment_results)

            logger.info("✅ Experiment pipeline completed successfully!")
            return final_results

        except Exception as e:
            logger.error(f"❌ Experiment pipeline failed: {e}")
            raise

    def _run_segmentation(self, customer_data_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Run customer segmentation step."""
        try:
            # Load customer data
            customers_df = load_customer_data(customer_data_path)
            logger.info(f"Loaded {len(customers_df)} customers")

            # Segment customers
            segments_df = segment_customers(customers_df, method="rules")

            # Save intermediate results
            segments_json = segments_df.to_dict(orient="records")
            with open("data/processed/segments.json", "w") as f:
                json.dump(segments_json, f, indent=2, default=self._json_serializer)

            # Log segment distribution
            segment_counts = segments_df["segment"].value_counts()
            logger.info(f"Segment distribution: {dict(segment_counts)}")

            self.results["segmentation"] = {
                "total_customers": len(customers_df),
                "segments_created": len(segment_counts),
                "segment_distribution": dict(segment_counts),
            }

            return customers_df, segments_df

        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            raise

    def _run_content_retrieval(self, segments_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Run content retrieval for each segment."""
        try:
            retrieved_content = {}
            unique_segments = segments_df["segment"].unique()

            with tqdm(unique_segments, desc="Retrieving content") as pbar:
                for segment_name in pbar:
                    pbar.set_description(f"Retrieving content for {segment_name}")

                    # Create segment dict for retrieval
                    segment_info = {
                        "name": segment_name,
                        "features": {},  # Could be enhanced with segment features
                    }

                    try:
                        content = retrieve_content(segment_info, top_k=5)
                        retrieved_content[segment_name] = content
                        logger.debug(f"Retrieved {len(content)} documents for {segment_name}")
                    except Exception as e:
                        logger.warning(f"Content retrieval failed for {segment_name}: {e}")
                        retrieved_content[segment_name] = []

            # Save intermediate results
            with open("data/processed/retrieved_content.json", "w") as f:
                json.dump(retrieved_content, f, indent=2, default=self._json_serializer)

            total_retrieved = sum(len(content) for content in retrieved_content.values())
            logger.info(
                f"Retrieved {total_retrieved} total content pieces across {len(unique_segments)} segments"
            )

            self.results["content_retrieval"] = {
                "segments_processed": len(unique_segments),
                "total_content_retrieved": total_retrieved,
                "avg_content_per_segment": (
                    total_retrieved / len(unique_segments) if unique_segments.size > 0 else 0
                ),
            }

            return retrieved_content

        except Exception as e:
            logger.error(f"Content retrieval failed: {e}")
            raise

    def _run_message_generation(
        self, segments_df: pd.DataFrame, retrieved_content: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """Generate message variants for each segment."""
        try:
            all_variants = []
            unique_segments = segments_df["segment"].unique()

            with tqdm(unique_segments, desc="Generating variants") as pbar:
                for segment_name in pbar:
                    pbar.set_description(f"Generating variants for {segment_name}")

                    # Get content for this segment
                    content = retrieved_content.get(segment_name, [])
                    if not content:
                        logger.warning(
                            f"No content available for {segment_name}, skipping generation"
                        )
                        continue

                    # Create segment dict for generation
                    segment_info = {"name": segment_name, "features": {}}

                    try:
                        # Generate variants for this segment
                        variants = generate_variants(segment_info, content)

                        # Add segment info to each variant
                        for variant in variants:
                            variant["segment"] = segment_name
                            variant["variant_id"] = (
                                f"VAR_{segment_name}_{variant.get('tone', 'unknown')}_{len(all_variants)}"
                            )

                        all_variants.extend(variants)
                        logger.debug(f"Generated {len(variants)} variants for {segment_name}")

                    except Exception as e:
                        logger.warning(f"Variant generation failed for {segment_name}: {e}")
                        continue

            # Save intermediate results
            with open("data/processed/variants.json", "w") as f:
                json.dump(all_variants, f, indent=2, default=self._json_serializer)

            logger.info(
                f"Generated {len(all_variants)} total variants across {len(unique_segments)} segments"
            )

            self.results["message_generation"] = {
                "segments_processed": len(unique_segments),
                "total_variants_generated": len(all_variants),
                "avg_variants_per_segment": (
                    len(all_variants) / len(unique_segments) if unique_segments.size > 0 else 0
                ),
            }

            return all_variants

        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            raise

    def _run_safety_screening(self, variants: List[Dict]) -> List[Dict]:
        """Screen all variants for safety compliance."""
        try:
            safe_variants = []
            blocked_variants = []

            with tqdm(variants, desc="Safety screening") as pbar:
                for variant in pbar:
                    pbar.set_description(
                        f"Screening variant {variant.get('variant_id', 'unknown')}"
                    )

                    try:
                        safety_result = check_safety(variant)

                        if safety_result["status"] == "pass":
                            safe_variants.append(variant)
                        else:
                            blocked_variants.append(
                                {"variant": variant, "safety_result": safety_result}
                            )

                    except Exception as e:
                        logger.warning(
                            f"Safety check failed for variant {variant.get('variant_id')}: {e}"
                        )
                        # Fail closed - treat as blocked
                        blocked_variants.append(
                            {
                                "variant": variant,
                                "safety_result": {
                                    "status": "block",
                                    "block_reason": f"Safety check error: {e}",
                                },
                            }
                        )

            # Save safety results
            safety_summary = {
                "total_variants": len(variants),
                "safe_variants": len(safe_variants),
                "blocked_variants": len(blocked_variants),
                "pass_rate": len(safe_variants) / len(variants) if variants else 0,
                "blocked_details": blocked_variants,
            }

            with open("data/processed/safety_results.json", "w") as f:
                json.dump(safety_summary, f, indent=2, default=self._json_serializer)

            logger.info(
                f"Safety screening: {len(safe_variants)}/{len(variants)} variants passed ({safety_summary['pass_rate']:.1%} pass rate)"
            )

            self.results["safety_screening"] = safety_summary

            return safe_variants

        except Exception as e:
            logger.error(f"Safety screening failed: {e}")
            raise

    def _run_experiment(
        self, customers_df: pd.DataFrame, safe_variants: List[Dict]
    ) -> Dict[str, Any]:
        """Design and execute the A/B/n experiment."""
        try:
            # Initialize experimentation agent
            exp_agent = ExperimentationAgent(self.config)

            # Design experiment
            logger.info("Designing experiment...")
            experiment_design = exp_agent.design_experiment(safe_variants, self.config)

            # Load segment assignments and merge with customers
            logger.info("Loading segment assignments...")
            with open("data/processed/segments.json", "r") as f:
                segments_data = json.load(f)

            segments_df = pd.DataFrame(segments_data)

            # Merge customers with their segment assignments
            customers_with_segments = customers_df.merge(
                segments_df[["customer_id", "segment"]], on="customer_id", how="left"
            )

            # Assign customers to experiment arms
            logger.info("Assigning customers to experiment arms...")
            assignments = exp_agent.assign_customers_to_arms(
                customers_with_segments.to_dict(orient="records"), experiment_design
            )

            # Save assignments
            with open("data/processed/assignments.json", "w") as f:
                json.dump(assignments, f, indent=2, default=self._json_serializer)

            # Simulate engagement
            logger.info("Simulating customer engagement...")
            engagement_data = exp_agent.simulate_engagement(assignments, self.config)

            # Save engagement data
            with open("data/processed/engagement.json", "w") as f:
                json.dump(engagement_data, f, indent=2, default=self._json_serializer)

            # Calculate metrics
            logger.info("Calculating experiment metrics...")
            metrics = exp_agent.calculate_metrics(engagement_data)

            # Save metrics
            with open("data/processed/experiment_metrics.json", "w") as f:
                json.dump(metrics, f, indent=2, default=self._json_serializer)

            experiment_results = {
                "experiment_design": experiment_design,
                "assignments": assignments,
                "engagement_data": engagement_data,
                "metrics": metrics,
            }

            logger.info(
                f"Experiment completed: {len(assignments)} customers assigned across {len(experiment_design.get('arms', []))} arms"
            )

            self.results["experiment"] = {
                "total_customers_assigned": len(assignments),
                "experiment_arms": len(experiment_design.get("arms", [])),
                "engagement_events": len(engagement_data),
                "primary_metric": metrics.get("primary_metric"),
                "lift_achieved": self._extract_best_lift(metrics),
            }

            return experiment_results

        except Exception as e:
            logger.error(f"Experiment execution failed: {e}")
            raise

    def _extract_best_lift(self, metrics: Dict[str, Any]) -> float:
        """Extract the best lift percentage from metrics."""
        try:
            lift_analysis = metrics.get("lift_analysis", [])
            if not lift_analysis:
                return 0.0

            # Find the best lift for the primary metric
            primary_metric = metrics.get("primary_metric", "click_rate")
            primary_lifts = [
                float(analysis.get("lift_percent", 0))  # Convert to float
                for analysis in lift_analysis
                if analysis.get("metric") == primary_metric
            ]

            return max(primary_lifts) if primary_lifts else 0.0

        except Exception as e:
            logger.warning(f"Could not extract lift: {e}")
            return 0.0

    def _generate_final_summary(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final experiment summary."""
        try:
            execution_time = (self.end_time - self.start_time).total_seconds()

            # Extract key metrics
            metrics = experiment_results.get("metrics", {})
            assignments = experiment_results.get("assignments", [])

            # Convert numpy types in results to native Python types for JSON serialization
            serializable_results = json.loads(
                json.dumps(self.results, default=self._json_serializer)
            )

            # Calculate summary statistics
            summary = {
                "experiment_info": {
                    "name": self.config["experiment"]["name"],
                    "experiment_id": self.config["experiment"]["experiment_id"],
                    "execution_time_seconds": execution_time,
                    "execution_time_minutes": execution_time / 60,
                    "completed_at": self.end_time.isoformat(),
                },
                "pipeline_results": serializable_results,
                "experiment_summary": {
                    "total_customers": len(assignments),
                    "experiment_arms": len(metrics.get("arms", [])),
                    "primary_metric": metrics.get("primary_metric", "click_rate"),
                    "best_lift_percent": float(self._extract_best_lift(metrics)),
                    "statistical_significance": self._check_significance(metrics),
                },
                "quality_metrics": {
                    "segmentation_success": self.results.get("segmentation", {}).get(
                        "segments_created", 0
                    )
                    >= 3,
                    "content_retrieval_success": self.results.get("content_retrieval", {}).get(
                        "total_content_retrieved", 0
                    )
                    > 0,
                    "generation_success": self.results.get("message_generation", {}).get(
                        "total_variants_generated", 0
                    )
                    > 0,
                    "safety_pass_rate": float(
                        self.results.get("safety_screening", {}).get("pass_rate", 0)
                    ),
                    "experiment_completion": len(assignments) > 0,
                },
            }

            # Save final summary
            with open("data/processed/experiment_summary.json", "w") as f:
                json.dump(summary, f, indent=2, default=self._json_serializer)

            # Print summary to console
            self._print_summary(summary)

            return summary

        except Exception as e:
            logger.error(f"Failed to generate final summary: {e}")
            raise

    def _check_significance(self, metrics: Dict[str, Any]) -> bool:
        """Check if any treatment shows statistical significance."""
        try:
            lift_analysis = metrics.get("lift_analysis", [])
            return any(
                analysis.get("statistical_significance", {}).get("significant", False)
                for analysis in lift_analysis
            )
        except Exception:
            return False

    def _print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary to console."""
        print("\n" + "=" * 80)
        print("🎉 EXPERIMENT EXECUTION COMPLETE")
        print("=" * 80)

        exp_info = summary["experiment_info"]
        print(f"📊 Experiment: {exp_info['name']}")
        print(f"⏱️  Execution Time: {exp_info['execution_time_minutes']:.1f} minutes")
        print(f"📅 Completed: {exp_info['completed_at']}")

        print("\n📈 PIPELINE RESULTS:")
        pipeline = summary["pipeline_results"]
        print(
            f"   • Customers Segmented: {pipeline.get('segmentation', {}).get('total_customers', 0)}"
        )
        print(
            f"   • Segments Created: {pipeline.get('segmentation', {}).get('segments_created', 0)}"
        )
        print(
            f"   • Content Retrieved: {pipeline.get('content_retrieval', {}).get('total_content_retrieved', 0)}"
        )
        print(
            f"   • Variants Generated: {pipeline.get('message_generation', {}).get('total_variants_generated', 0)}"
        )
        print(
            f"   • Safety Pass Rate: {pipeline.get('safety_screening', {}).get('pass_rate', 0):.1%}"
        )

        print("\n🧪 EXPERIMENT RESULTS:")
        exp_summary = summary["experiment_summary"]
        print(f"   • Total Customers: {exp_summary['total_customers']}")
        print(f"   • Experiment Arms: {exp_summary['experiment_arms']}")
        print(f"   • Primary Metric: {exp_summary['primary_metric']}")
        print(f"   • Best Lift: {exp_summary['best_lift_percent']:.1f}%")
        print(
            f"   • Statistical Significance: {'✅ Yes' if exp_summary['statistical_significance'] else '❌ No'}"
        )

        print("\n✅ QUALITY CHECKS:")
        quality = summary["quality_metrics"]
        for check, passed in quality.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   • {check.replace('_', ' ').title()}: {status}")

        print("\n📁 OUTPUT FILES:")
        output_files = [
            "data/processed/segments.json",
            "data/processed/retrieved_content.json",
            "data/processed/variants.json",
            "data/processed/safety_results.json",
            "data/processed/assignments.json",
            "data/processed/engagement.json",
            "data/processed/experiment_metrics.json",
            "data/processed/experiment_summary.json",
        ]

        for file_path in output_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (missing)")

        print("\n" + "=" * 80)
        print("🚀 Ready for Task 5.1: Experiment Report Generation")
        print("=" * 80)


def main():
    """Main entry point for the experiment execution script."""
    parser = argparse.ArgumentParser(
        description="Execute end-to-end personalization experiment pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default configuration
    python scripts/run_experiment.py
    
    # Run with custom config and customer data
    python scripts/run_experiment.py --config config/my_experiment.yaml --customers data/my_customers.csv
    
    # Run with verbose logging
    python scripts/run_experiment.py --verbose
        """,
    )

    parser.add_argument(
        "--config",
        default="config/experiment_config.yaml",
        help="Path to experiment configuration file (default: config/experiment_config.yaml)",
    )

    parser.add_argument(
        "--customers",
        default="data/raw/customers.csv",
        help="Path to customer data CSV file (default: data/raw/customers.csv)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate input files exist
        if not os.path.exists(args.config):
            print(f"❌ Configuration file not found: {args.config}")
            sys.exit(1)

        if not os.path.exists(args.customers):
            print(f"❌ Customer data file not found: {args.customers}")
            sys.exit(1)

        # Initialize and run pipeline
        pipeline = ExperimentPipeline(args.config)
        results = pipeline.run_full_experiment(args.customers)

        # Success
        print(f"\n✅ Experiment completed successfully!")
        print(f"📊 Results saved to: data/processed/experiment_summary.json")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️ Experiment interrupted by user")
        return 1

    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        logger.exception("Experiment execution failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
