#!/usr/bin/env python3
"""
Safety Screening Test Script

This script runs comprehensive safety screening tests on all generated message variants
from the batch generation testing. It implements Task 3.7: Safety Screening Testing.

Usage:
    python scripts/safety_screening_test.py [--variants-file path] [--output-dir path]
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.safety_agent import SafetyAgent
from src.integrations.azure_content_safety import get_safety_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_generated_variants(variants_file: str) -> List[Dict[str, Any]]:
    """
    Load generated variants from JSON file.
    
    Args:
        variants_file: Path to variants JSON file
        
    Returns:
        List of variant dictionaries
        
    Raises:
        FileNotFoundError: If variants file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(variants_file, 'r') as f:
            data = json.load(f)
        
        # Extract variants from the test results structure
        if 'variants' in data:
            variants = data['variants']
        else:
            # Assume the file contains a list of variants directly
            variants = data if isinstance(data, list) else [data]
        
        logger.info(f"Loaded {len(variants)} variants from {variants_file}")
        return variants
        
    except FileNotFoundError:
        logger.error(f"Variants file not found: {variants_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in variants file: {e}")
        raise


def run_safety_screening(variants: List[Dict[str, Any]], 
                        safety_agent: SafetyAgent) -> List[Dict[str, Any]]:
    """
    Run safety screening on all variants.
    
    Args:
        variants: List of message variants to screen
        safety_agent: Initialized SafetyAgent instance
        
    Returns:
        List of safety check results
    """
    logger.info(f"Starting safety screening for {len(variants)} variants...")
    
    safety_results = []
    
    for i, variant in enumerate(variants, 1):
        try:
            logger.info(f"Screening variant {i}/{len(variants)}: {variant.get('variant_id', 'UNKNOWN')}")
            
            # Prepare variant for safety check
            safety_variant = {
                'variant_id': variant.get('variant_id', f'VAR_{i:03d}'),
                'body': variant.get('body', ''),
                'customer_id': variant.get('customer_id', ''),
                'segment': variant.get('segment', '')
            }
            
            # Run safety check
            result = safety_agent.check_safety(safety_variant)
            
            # Add original variant info to result
            result['original_variant'] = {
                'subject': variant.get('subject', ''),
                'tone': variant.get('tone', ''),
                'word_count': variant.get('validation', {}).get('word_count', 0),
                'citation_count': variant.get('validation', {}).get('citation_count', 0)
            }
            
            safety_results.append(result)
            
            # Log result
            status_emoji = "✅" if result['status'] == 'pass' else "❌"
            logger.info(
                f"{status_emoji} {result['variant_id']}: {result['status']} "
                f"(max severity: {result['max_severity']}, threshold: {result['threshold_used']})"
            )
            
            if result['status'] == 'block':
                logger.warning(
                    f"   Blocked categories: {result['blocked_categories']}"
                )
                logger.warning(
                    f"   Reason: {result['block_reason']}"
                )
            
        except Exception as e:
            logger.error(f"Failed to screen variant {i}: {e}")
            # Create error result
            error_result = {
                'variant_id': variant.get('variant_id', f'VAR_{i:03d}'),
                'status': 'error',
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }
            safety_results.append(error_result)
    
    logger.info(f"Safety screening complete for {len(variants)} variants")
    return safety_results


def calculate_safety_metrics(safety_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate safety screening metrics and statistics.
    
    Args:
        safety_results: List of safety check results
        
    Returns:
        Dict containing comprehensive safety metrics
    """
    total_variants = len(safety_results)
    passed_variants = [r for r in safety_results if r.get('status') == 'pass']
    blocked_variants = [r for r in safety_results if r.get('status') == 'block']
    error_variants = [r for r in safety_results if r.get('status') == 'error']
    
    pass_count = len(passed_variants)
    block_count = len(blocked_variants)
    error_count = len(error_variants)
    
    pass_rate = (pass_count / max(1, total_variants)) * 100
    block_rate = (block_count / max(1, total_variants)) * 100
    error_rate = (error_count / max(1, total_variants)) * 100
    
    # Category breakdown
    category_blocks = {
        'hate': 0,
        'violence': 0,
        'self_harm': 0,
        'sexual': 0,
        'api_error': 0
    }
    
    for result in blocked_variants:
        blocked_cats = result.get('blocked_categories', [])
        for cat in blocked_cats:
            if cat in category_blocks:
                category_blocks[cat] += 1
    
    # Count API errors
    for result in error_variants:
        category_blocks['api_error'] += 1
    
    # Severity distribution
    severity_distribution = {
        'safe_0': 0,
        'low_2': 0,
        'medium_4': 0,
        'high_6': 0
    }
    
    for result in safety_results:
        max_sev = result.get('max_severity', 0)
        if max_sev == 0:
            severity_distribution['safe_0'] += 1
        elif max_sev == 2:
            severity_distribution['low_2'] += 1
        elif max_sev == 4:
            severity_distribution['medium_4'] += 1
        elif max_sev == 6:
            severity_distribution['high_6'] += 1
    
    # Segment breakdown
    segment_stats = {}
    for result in safety_results:
        segment = result.get('segment', 'Unknown')
        if segment not in segment_stats:
            segment_stats[segment] = {'total': 0, 'passed': 0, 'blocked': 0}
        
        segment_stats[segment]['total'] += 1
        if result.get('status') == 'pass':
            segment_stats[segment]['passed'] += 1
        elif result.get('status') == 'block':
            segment_stats[segment]['blocked'] += 1
    
    # Calculate segment pass rates
    for segment, stats in segment_stats.items():
        stats['pass_rate'] = (stats['passed'] / max(1, stats['total'])) * 100
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'total_variants': total_variants,
        'passed_variants': pass_count,
        'blocked_variants': block_count,
        'error_variants': error_count,
        'pass_rate_percent': round(pass_rate, 2),
        'block_rate_percent': round(block_rate, 2),
        'error_rate_percent': round(error_rate, 2),
        'category_blocks': category_blocks,
        'severity_distribution': severity_distribution,
        'segment_breakdown': segment_stats,
        'meets_90_percent_target': pass_rate >= 90.0
    }


def review_blocked_variants(safety_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Review and analyze blocked variants for manual inspection.
    
    Args:
        safety_results: List of safety check results
        
    Returns:
        List of blocked variants with analysis
    """
    blocked_variants = [r for r in safety_results if r.get('status') == 'block']
    
    logger.info(f"Reviewing {len(blocked_variants)} blocked variants...")
    
    reviewed_variants = []
    
    for result in blocked_variants:
        # Extract key information for review
        review_info = {
            'variant_id': result.get('variant_id'),
            'segment': result.get('segment'),
            'blocked_categories': result.get('blocked_categories', []),
            'severity_scores': {
                'hate': result.get('hate_severity', 0),
                'violence': result.get('violence_severity', 0),
                'self_harm': result.get('self_harm_severity', 0),
                'sexual': result.get('sexual_severity', 0)
            },
            'max_severity': result.get('max_severity', 0),
            'threshold_used': result.get('threshold_used', 4),
            'block_reason': result.get('block_reason'),
            'original_variant': result.get('original_variant', {}),
            'review_notes': []
        }
        
        # Add automated review notes
        if result.get('max_severity', 0) == 6:
            review_info['review_notes'].append("HIGH SEVERITY: Requires immediate attention")
        
        if 'api_error' in result.get('blocked_categories', []):
            review_info['review_notes'].append("API ERROR: Technical failure, not content issue")
        
        if len(result.get('blocked_categories', [])) > 1:
            review_info['review_notes'].append("MULTIPLE CATEGORIES: Multiple policy violations detected")
        
        reviewed_variants.append(review_info)
        
        # Log blocked variant details
        logger.warning(f"BLOCKED: {review_info['variant_id']} ({review_info['segment']})")
        logger.warning(f"  Categories: {review_info['blocked_categories']}")
        logger.warning(f"  Max Severity: {review_info['max_severity']}")
        logger.warning(f"  Reason: {review_info['block_reason']}")
    
    return reviewed_variants


def verify_audit_log_completeness(safety_agent: SafetyAgent, 
                                 expected_count: int) -> Dict[str, Any]:
    """
    Verify that the audit log contains all expected entries.
    
    Args:
        safety_agent: SafetyAgent instance with audit log
        expected_count: Expected number of audit entries
        
    Returns:
        Dict containing audit log verification results
    """
    logger.info("Verifying audit log completeness...")
    
    try:
        # Generate audit report to get current statistics
        audit_report = safety_agent.generate_audit_report()
        
        actual_count = audit_report.get('total_checks', 0)
        
        verification_result = {
            'expected_entries': expected_count,
            'actual_entries': actual_count,
            'complete': actual_count >= expected_count,
            'audit_log_path': safety_agent.audit_log_path,
            'verification_time': datetime.utcnow().isoformat()
        }
        
        if verification_result['complete']:
            logger.info(f"✅ Audit log complete: {actual_count}/{expected_count} entries")
        else:
            logger.warning(f"⚠️ Audit log incomplete: {actual_count}/{expected_count} entries")
        
        return verification_result
        
    except Exception as e:
        logger.error(f"Failed to verify audit log: {e}")
        return {
            'expected_entries': expected_count,
            'actual_entries': 0,
            'complete': False,
            'error': str(e),
            'verification_time': datetime.utcnow().isoformat()
        }


def generate_safety_summary_report(safety_metrics: Dict[str, Any],
                                  blocked_variants: List[Dict[str, Any]],
                                  audit_verification: Dict[str, Any],
                                  output_dir: str) -> str:
    """
    Generate comprehensive safety summary report.
    
    Args:
        safety_metrics: Safety screening metrics
        blocked_variants: List of blocked variants with review
        audit_verification: Audit log verification results
        output_dir: Output directory for report
        
    Returns:
        Path to generated report file
    """
    logger.info("Generating safety summary report...")
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create comprehensive report
    report = {
        'report_metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': 'Safety Screening Test Results',
            'task': 'Task 3.7: Safety Screening Testing'
        },
        'executive_summary': {
            'total_variants_screened': safety_metrics['total_variants'],
            'pass_rate_percent': safety_metrics['pass_rate_percent'],
            'meets_90_percent_target': safety_metrics['meets_90_percent_target'],
            'blocked_variants_count': safety_metrics['blocked_variants'],
            'screening_errors': safety_metrics['error_variants'],
            'audit_log_complete': audit_verification['complete']
        },
        'detailed_metrics': safety_metrics,
        'blocked_variants_review': blocked_variants,
        'audit_verification': audit_verification,
        'recommendations': []
    }
    
    # Add recommendations based on results
    if safety_metrics['pass_rate_percent'] < 90:
        report['recommendations'].append(
            f"Pass rate ({safety_metrics['pass_rate_percent']:.1f}%) is below 90% target. "
            "Review content generation prompts and safety thresholds."
        )
    
    if safety_metrics['error_variants'] > 0:
        report['recommendations'].append(
            f"{safety_metrics['error_variants']} variants had screening errors. "
            "Check Azure Content Safety API connectivity and configuration."
        )
    
    if not audit_verification['complete']:
        report['recommendations'].append(
            "Audit log is incomplete. Verify all safety checks are being logged properly."
        )
    
    if len(blocked_variants) > 0:
        high_severity_blocks = [v for v in blocked_variants if v['max_severity'] == 6]
        if high_severity_blocks:
            report['recommendations'].append(
                f"{len(high_severity_blocks)} variants blocked with HIGH severity. "
                "Review content generation prompts to reduce policy violations."
            )
    
    # Save report to file
    report_file = os.path.join(output_dir, 'safety_screening_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Safety summary report saved to: {report_file}")
    return report_file


def print_summary_results(safety_metrics: Dict[str, Any], 
                         blocked_variants: List[Dict[str, Any]],
                         audit_verification: Dict[str, Any]):
    """
    Print summary results to console.
    
    Args:
        safety_metrics: Safety screening metrics
        blocked_variants: List of blocked variants
        audit_verification: Audit log verification results
    """
    print("\n" + "="*60)
    print("SAFETY SCREENING TEST RESULTS")
    print("="*60)
    
    # Overall results
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total Variants Screened: {safety_metrics['total_variants']}")
    print(f"   Passed: {safety_metrics['passed_variants']} ({safety_metrics['pass_rate_percent']:.1f}%)")
    print(f"   Blocked: {safety_metrics['blocked_variants']} ({safety_metrics['block_rate_percent']:.1f}%)")
    print(f"   Errors: {safety_metrics['error_variants']} ({safety_metrics['error_rate_percent']:.1f}%)")
    
    # Target achievement
    target_met = "✅" if safety_metrics['meets_90_percent_target'] else "❌"
    print(f"\n🎯 TARGET ACHIEVEMENT:")
    print(f"   90% Pass Rate Target: {target_met} ({safety_metrics['pass_rate_percent']:.1f}%)")
    
    # Category breakdown
    print(f"\n🚫 BLOCKED BY CATEGORY:")
    for category, count in safety_metrics['category_blocks'].items():
        if count > 0:
            print(f"   {category.title()}: {count}")
    
    # Segment breakdown
    print(f"\n📈 SEGMENT BREAKDOWN:")
    for segment, stats in safety_metrics['segment_breakdown'].items():
        print(f"   {segment}: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']:.1f}%)")
    
    # Audit log verification
    audit_status = "✅" if audit_verification['complete'] else "❌"
    print(f"\n📋 AUDIT LOG VERIFICATION:")
    print(f"   Complete: {audit_status} ({audit_verification['actual_entries']}/{audit_verification['expected_entries']} entries)")
    
    # Blocked variants summary
    if blocked_variants:
        print(f"\n⚠️  BLOCKED VARIANTS REVIEW:")
        print(f"   Total Blocked: {len(blocked_variants)}")
        
        high_severity = [v for v in blocked_variants if v['max_severity'] == 6]
        if high_severity:
            print(f"   High Severity (6): {len(high_severity)}")
        
        api_errors = [v for v in blocked_variants if 'api_error' in v['blocked_categories']]
        if api_errors:
            print(f"   API Errors: {len(api_errors)}")
    
    print("\n" + "="*60)


def main():
    """Main function to run safety screening tests."""
    parser = argparse.ArgumentParser(description='Run safety screening tests on generated variants')
    parser.add_argument(
        '--variants-file',
        default='data/processed/generation_test_results.json',
        help='Path to variants JSON file (default: data/processed/generation_test_results.json)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/processed',
        help='Output directory for results (default: data/processed)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        print("🔒 Starting Safety Screening Testing (Task 3.7)")
        print(f"   Variants file: {args.variants_file}")
        print(f"   Output directory: {args.output_dir}")
        
        # Load generated variants
        variants = load_generated_variants(args.variants_file)
        
        # Initialize safety agent
        logger.info("Initializing Safety Agent...")
        safety_agent = SafetyAgent()
        
        # Run safety screening on all variants
        safety_results = run_safety_screening(variants, safety_agent)
        
        # Calculate safety metrics
        safety_metrics = calculate_safety_metrics(safety_results)
        
        # Review blocked variants
        blocked_variants = review_blocked_variants(safety_results)
        
        # Verify audit log completeness
        audit_verification = verify_audit_log_completeness(safety_agent, len(variants))
        
        # Generate comprehensive report
        report_file = generate_safety_summary_report(
            safety_metrics, blocked_variants, audit_verification, args.output_dir
        )
        
        # Save detailed results
        results_file = os.path.join(args.output_dir, 'safety_screening_results.json')
        with open(results_file, 'w') as f:
            json.dump({
                'safety_results': safety_results,
                'safety_metrics': safety_metrics,
                'blocked_variants_review': blocked_variants,
                'audit_verification': audit_verification
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detailed results saved to: {results_file}")
        
        # Print summary to console
        print_summary_results(safety_metrics, blocked_variants, audit_verification)
        
        # Final status
        if safety_metrics['meets_90_percent_target'] and audit_verification['complete']:
            print("\n✅ Task 3.7: Safety Screening Testing - COMPLETED SUCCESSFULLY")
            return 0
        else:
            print("\n⚠️ Task 3.7: Safety Screening Testing - COMPLETED WITH ISSUES")
            return 1
            
    except Exception as e:
        logger.error(f"Safety screening test failed: {e}")
        print(f"\n❌ Task 3.7: Safety Screening Testing - FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit(main())