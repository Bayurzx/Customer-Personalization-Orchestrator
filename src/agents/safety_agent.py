"""
Safety Agent Module

This module implements the Safety Agent responsible for enforcing content safety policies
by screening all generated message variants before they are sent to customers.

The agent integrates with Azure AI Content Safety API and maintains a complete audit trail
of all safety decisions for compliance purposes.
"""

import os
import csv
import logging
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.integrations.azure_content_safety import ContentSafetyClient, get_safety_client

# Configure logging
logger = logging.getLogger(__name__)


class SafetyAgent:
    """
    Safety Agent for content policy enforcement and audit logging.
    
    This agent screens all message variants against Azure AI Content Safety policies
    and maintains a complete audit trail for compliance purposes.
    """
    
    def __init__(self, 
                 safety_client: Optional[ContentSafetyClient] = None,
                 config_path: str = "config/safety_thresholds.yaml",
                 audit_log_path: str = "logs/safety_audit.log"):
        """
        Initialize the Safety Agent.
        
        Args:
            safety_client: Azure Content Safety client (creates new if None)
            config_path: Path to safety configuration file
            audit_log_path: Path to audit log file
        """
        self.safety_client = safety_client or get_safety_client()
        self.config_path = config_path
        self.audit_log_path = audit_log_path
        
        # Load configuration
        self.config = self._load_config()
        self.threshold = self.config.get('safety_policy', {}).get('threshold', 4)
        
        # Initialize audit log
        self._initialize_audit_log()
        
        # Statistics tracking
        self.total_checks = 0
        self.total_passed = 0
        self.total_blocked = 0
        self.blocked_by_category = {
            'hate': 0,
            'violence': 0,
            'self_harm': 0,
            'sexual': 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load safety configuration from YAML file.
        
        Returns:
            Dict containing safety configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded safety configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Safety configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in safety configuration: {e}")
            raise
    
    def _initialize_audit_log(self):
        """Initialize the audit log file with CSV headers if it doesn't exist."""
        # Ensure logs directory exists
        log_dir = Path(self.audit_log_path).parent
        log_dir.mkdir(exist_ok=True)
        
        # Check if audit log exists and has headers
        if not os.path.exists(self.audit_log_path) or os.path.getsize(self.audit_log_path) == 0:
            headers = [
                'timestamp',
                'variant_id',
                'customer_id',
                'segment',
                'status',
                'hate_severity',
                'violence_severity',
                'self_harm_severity',
                'sexual_severity',
                'max_severity',
                'threshold_used',
                'blocked_categories',
                'block_reason'
            ]
            
            with open(self.audit_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Initialized audit log: {self.audit_log_path}")
    
    def check_safety(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a message variant against safety policies.
        
        Args:
            variant: Message variant dictionary containing:
                - variant_id: Unique variant identifier
                - body: Message body text to analyze
                - customer_id: Customer ID (optional)
                - segment: Customer segment (optional)
        
        Returns:
            Dict containing safety check results:
                - variant_id: Variant identifier
                - status: "pass" or "block"
                - hate_severity: Hate category severity (0-6)
                - violence_severity: Violence category severity (0-6)
                - self_harm_severity: Self-harm category severity (0-6)
                - sexual_severity: Sexual category severity (0-6)
                - max_severity: Maximum severity across all categories
                - threshold_used: Policy threshold applied
                - blocked_categories: List of categories that exceeded threshold
                - block_reason: Explanation if blocked
                - checked_at: ISO timestamp of check
        
        Raises:
            ValueError: If variant is missing required fields
            Exception: If safety API call fails
        """
        # Validate input
        if not isinstance(variant, dict):
            raise ValueError("Variant must be a dictionary")
        
        if 'variant_id' not in variant:
            raise ValueError("Variant must contain 'variant_id'")
        
        if 'body' not in variant or not variant['body'] or not variant['body'].strip():
            raise ValueError("Variant must contain non-empty 'body'")
        
        variant_id = variant['variant_id']
        text_to_analyze = variant['body']
        
        logger.debug(f"Checking safety for variant {variant_id}")
        
        try:
            # Analyze text with Azure Content Safety
            safety_result = self.safety_client.analyze_text(text_to_analyze)
            
            # Extract severity scores
            severity_scores = safety_result.get('severity_scores', {})
            
            # Build result structure
            result = {
                'variant_id': variant_id,
                'customer_id': variant.get('customer_id', ''),
                'segment': variant.get('segment', ''),
                'hate_severity': severity_scores.get('hate', 0),
                'violence_severity': severity_scores.get('violence', 0),
                'self_harm_severity': severity_scores.get('self_harm', 0),
                'sexual_severity': severity_scores.get('sexual', 0),
                'max_severity': safety_result.get('max_severity', 0),
                'threshold_used': self.threshold,
                'checked_at': datetime.utcnow().isoformat()
            }
            
            # Apply policy threshold
            policy_result = self.apply_policy_threshold(severity_scores, self.threshold)
            result.update(policy_result)
            
            # Update statistics
            self.total_checks += 1
            if result['status'] == 'pass':
                self.total_passed += 1
            else:
                self.total_blocked += 1
                # Track blocked categories
                for category in result['blocked_categories']:
                    if category in self.blocked_by_category:
                        self.blocked_by_category[category] += 1
            
            # Log the decision
            self._log_safety_decision(result)
            
            logger.info(
                f"Safety check complete for {variant_id}: {result['status']} "
                f"(max severity: {result['max_severity']}, threshold: {self.threshold})"
            )
            
            return result
            
        except Exception as e:
            # Fail closed - block on error
            logger.error(f"Safety check failed for variant {variant_id}: {e}")
            
            error_result = {
                'variant_id': variant_id,
                'customer_id': variant.get('customer_id', ''),
                'segment': variant.get('segment', ''),
                'status': 'block',
                'hate_severity': 0,
                'violence_severity': 0,
                'self_harm_severity': 0,
                'sexual_severity': 0,
                'max_severity': 0,
                'threshold_used': self.threshold,
                'blocked_categories': ['api_error'],
                'block_reason': f"Safety API error: {str(e)}",
                'checked_at': datetime.utcnow().isoformat()
            }
            
            # Update statistics
            self.total_checks += 1
            self.total_blocked += 1
            
            # Log the error decision
            self._log_safety_decision(error_result)
            
            return error_result
    
    def apply_policy_threshold(self, severity_scores: Dict[str, int], threshold: int = None) -> Dict[str, Any]:
        """
        Apply safety policy threshold to severity scores.
        
        Args:
            severity_scores: Dict with category severity scores
            threshold: Severity threshold (uses instance default if None)
        
        Returns:
            Dict containing policy decision:
                - status: "pass" or "block"
                - blocked_categories: List of categories exceeding threshold
                - block_reason: Explanation if blocked
        """
        if threshold is None:
            threshold = self.threshold
        
        blocked_categories = []
        
        # Check each category against threshold
        for category, severity in severity_scores.items():
            if severity > threshold:
                blocked_categories.append(category)
        
        if blocked_categories:
            status = 'block'
            block_reason = f"Categories {blocked_categories} exceeded threshold {threshold}"
        else:
            status = 'pass'
            block_reason = None
        
        return {
            'status': status,
            'blocked_categories': blocked_categories,
            'block_reason': block_reason
        }
    
    def _log_safety_decision(self, result: Dict[str, Any]):
        """
        Log safety decision to CSV audit log.
        
        Args:
            result: Safety check result dictionary
        """
        try:
            with open(self.audit_log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Format blocked categories as comma-separated string
                blocked_categories_str = ','.join(result.get('blocked_categories', []))
                
                row = [
                    result.get('checked_at', ''),
                    result.get('variant_id', ''),
                    result.get('customer_id', ''),
                    result.get('segment', ''),
                    result.get('status', ''),
                    result.get('hate_severity', 0),
                    result.get('violence_severity', 0),
                    result.get('self_harm_severity', 0),
                    result.get('sexual_severity', 0),
                    result.get('max_severity', 0),
                    result.get('threshold_used', self.threshold),
                    blocked_categories_str,
                    result.get('block_reason', '')
                ]
                
                writer.writerow(row)
                
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report from the safety log.
        
        Returns:
            Dict containing audit statistics and summary
        """
        try:
            # Read audit log
            audit_entries = []
            if os.path.exists(self.audit_log_path):
                with open(self.audit_log_path, 'r') as f:
                    reader = csv.DictReader(f)
                    audit_entries = list(reader)
            
            # Calculate statistics
            total_entries = len(audit_entries)
            passed_entries = [e for e in audit_entries if e['status'] == 'pass']
            blocked_entries = [e for e in audit_entries if e['status'] == 'block']
            
            pass_rate = (len(passed_entries) / max(1, total_entries)) * 100
            block_rate = (len(blocked_entries) / max(1, total_entries)) * 100
            
            # Category breakdown
            category_blocks = {
                'hate': 0,
                'violence': 0,
                'self_harm': 0,
                'sexual': 0,
                'api_error': 0
            }
            
            for entry in blocked_entries:
                blocked_cats = entry.get('blocked_categories', '').split(',')
                for cat in blocked_cats:
                    cat = cat.strip()
                    if cat in category_blocks:
                        category_blocks[cat] += 1
            
            # Severity distribution
            severity_distribution = {
                'safe_0': 0,
                'low_2': 0,
                'medium_4': 0,
                'high_6': 0
            }
            
            for entry in audit_entries:
                max_sev = int(entry.get('max_severity', 0))
                if max_sev == 0:
                    severity_distribution['safe_0'] += 1
                elif max_sev == 2:
                    severity_distribution['low_2'] += 1
                elif max_sev == 4:
                    severity_distribution['medium_4'] += 1
                elif max_sev == 6:
                    severity_distribution['high_6'] += 1
            
            # Recent activity (last 24 hours)
            now = datetime.utcnow()
            recent_entries = []
            for entry in audit_entries:
                try:
                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    if (now - entry_time.replace(tzinfo=None)).total_seconds() < 86400:  # 24 hours
                        recent_entries.append(entry)
                except (ValueError, KeyError):
                    continue
            
            report = {
                'generated_at': now.isoformat(),
                'audit_log_path': self.audit_log_path,
                'threshold_used': self.threshold,
                'total_checks': total_entries,
                'passed_checks': len(passed_entries),
                'blocked_checks': len(blocked_entries),
                'pass_rate_percent': round(pass_rate, 2),
                'block_rate_percent': round(block_rate, 2),
                'category_blocks': category_blocks,
                'severity_distribution': severity_distribution,
                'recent_activity_24h': len(recent_entries),
                'session_statistics': {
                    'total_checks': self.total_checks,
                    'total_passed': self.total_passed,
                    'total_blocked': self.total_blocked,
                    'blocked_by_category': self.blocked_by_category.copy()
                }
            }
            
            logger.info(f"Generated audit report: {total_entries} total checks, {pass_rate:.1f}% pass rate")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current session statistics.
        
        Returns:
            Dict containing current session statistics
        """
        pass_rate = (self.total_passed / max(1, self.total_checks)) * 100
        block_rate = (self.total_blocked / max(1, self.total_checks)) * 100
        
        return {
            'total_checks': self.total_checks,
            'total_passed': self.total_passed,
            'total_blocked': self.total_blocked,
            'pass_rate_percent': round(pass_rate, 2),
            'block_rate_percent': round(block_rate, 2),
            'blocked_by_category': self.blocked_by_category.copy(),
            'threshold_used': self.threshold
        }


# Convenience functions for backward compatibility
def check_safety(variant: Dict[str, Any], 
                 config_path: str = "config/safety_thresholds.yaml") -> Dict[str, Any]:
    """
    Check a message variant against safety policies (convenience function).
    
    Args:
        variant: Message variant to check
        config_path: Path to safety configuration file
    
    Returns:
        Dict containing safety check results
    """
    agent = SafetyAgent(config_path=config_path)
    return agent.check_safety(variant)


def apply_policy_threshold(severity_scores: Dict[str, int], threshold: int = 4) -> Dict[str, Any]:
    """
    Apply safety policy threshold to severity scores (convenience function).
    
    Args:
        severity_scores: Dict with category severity scores
        threshold: Severity threshold
    
    Returns:
        Dict containing policy decision
    """
    agent = SafetyAgent()
    return agent.apply_policy_threshold(severity_scores, threshold)


def generate_audit_report(audit_log_path: str = "logs/safety_audit.log") -> Dict[str, Any]:
    """
    Generate audit report from safety log (convenience function).
    
    Args:
        audit_log_path: Path to audit log file
    
    Returns:
        Dict containing audit report
    """
    agent = SafetyAgent(audit_log_path=audit_log_path)
    return agent.generate_audit_report()


if __name__ == "__main__":
    # Test the safety agent
    test_variant = {
        'variant_id': 'TEST001',
        'customer_id': 'C001',
        'segment': 'Test',
        'body': 'This is a safe test message for the safety agent.'
    }
    
    try:
        agent = SafetyAgent()
        result = agent.check_safety(test_variant)
        print(f"✅ Safety check result: {result['status']}")
        
        stats = agent.get_statistics()
        print(f"✅ Session stats: {stats}")
        
        report = agent.generate_audit_report()
        print(f"✅ Audit report generated with {report['total_checks']} total checks")
        
    except Exception as e:
        print(f"❌ Safety agent test failed: {e}")