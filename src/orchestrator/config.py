"""
Configuration management for Customer Personalization Orchestrator.

This module provides centralized configuration loading with automatic
structure normalization and backward compatibility.

Author: AI Assistant
Created: 2025-11-23
Purpose: Fix configuration issues from Task 4.3 analysis
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Centralized configuration loader with automatic structure normalization.
    
    This class addresses the configuration issues identified in Task 4.3:
    - Inconsistent nesting (experiment.simulation vs simulation)
    - Missing default values
    - Poor error handling
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize ConfigLoader.
        
        Args:
            project_root: Project root directory. If None, auto-detected.
        """
        if project_root is None:
            # Auto-detect project root (3 levels up from this file)
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
    
    def load_experiment_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load experiment configuration with automatic structure normalization.
        
        Args:
            config_path: Path to config file. If None, uses default location.
            
        Returns:
            Normalized configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        if config_path is None:
            config_path = self.project_root / "config" / "experiment_config.yaml"
        else:
            config_path = Path(config_path)
        
        logger.info(f"Loading experiment config from: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file: {e}")
            raise
        
        # Normalize configuration structure
        normalized_config = self._normalize_experiment_config(raw_config)
        
        logger.info("✅ Experiment configuration loaded and normalized")
        return normalized_config
    
    def _normalize_experiment_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize experiment configuration structure for backward compatibility.
        
        This method fixes the main issues from Task 4.3:
        1. Moves experiment.simulation to top-level simulation
        2. Adds missing default values
        3. Ensures consistent structure
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Normalized configuration dictionary
        """
        normalized = config.copy()
        
        # Fix Issue #1: Move nested experiment.simulation to top level
        if 'experiment' in config:
            experiment_config = config['experiment']
            
            # Move simulation config to top level if not already there
            if 'simulation' in experiment_config and 'simulation' not in normalized:
                normalized['simulation'] = experiment_config['simulation']
                logger.debug("Moved experiment.simulation to top-level simulation")
            
            # Move other experiment configs if needed
            for key in ['metrics', 'statistical_testing', 'sample_allocation']:
                if key in experiment_config and key not in normalized:
                    normalized[key] = experiment_config[key]
        
        # Fix Issue #2: Ensure simulation config has all required fields
        if 'simulation' not in normalized:
            normalized['simulation'] = {}
        
        sim_config = normalized['simulation']
        
        # Add default baseline rates
        if 'baseline_rates' not in sim_config:
            sim_config['baseline_rates'] = {
                'open_rate': 0.25,
                'click_rate': 0.05,
                'conversion_rate': 0.01
            }
        else:
            # Ensure all baseline rates are present
            baseline_defaults = {
                'open_rate': 0.25,
                'click_rate': 0.05,
                'conversion_rate': 0.01
            }
            for key, default_value in baseline_defaults.items():
                sim_config['baseline_rates'].setdefault(key, default_value)
        
        # Add default uplift config
        if 'expected_uplift' not in sim_config:
            sim_config['expected_uplift'] = {
                'mean': 0.15,
                'std_dev': 0.05,
                'min_uplift': 0.05,
                'max_uplift': 0.30
            }
        else:
            # Ensure all uplift parameters are present
            uplift_defaults = {
                'mean': 0.15,
                'std_dev': 0.05,
                'min_uplift': 0.05,
                'max_uplift': 0.30
            }
            for key, default_value in uplift_defaults.items():
                sim_config['expected_uplift'].setdefault(key, default_value)
        
        # Add other simulation defaults
        sim_config.setdefault('noise_factor', 0.02)
        sim_config.setdefault('random_seed', 42)
        sim_config.setdefault('use_historical_data', False)
        
        # Fix Issue #3: Ensure segments config exists
        if 'segments' not in normalized:
            normalized['segments'] = {}
        
        # Add default segment configs if missing
        default_segments = {
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
        }
        
        for segment_name, segment_config in default_segments.items():
            if segment_name not in normalized['segments']:
                normalized['segments'][segment_name] = segment_config
        
        # Add other top-level defaults
        normalized.setdefault('random_seed', 42)
        
        logger.debug("Configuration normalization completed")
        return normalized
    
    def load_azure_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load Azure services configuration.
        
        Args:
            config_path: Path to Azure config file. If None, uses default location.
            
        Returns:
            Azure configuration dictionary
        """
        if config_path is None:
            config_path = self.project_root / "config" / "azure_config.yaml"
        else:
            config_path = Path(config_path)
        
        logger.info(f"Loading Azure config from: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("✅ Azure configuration loaded")
            return config
        except FileNotFoundError:
            logger.warning(f"Azure config file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in Azure config file: {e}")
            raise
    
    def load_safety_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load safety thresholds configuration.
        
        Args:
            config_path: Path to safety config file. If None, uses default location.
            
        Returns:
            Safety configuration dictionary
        """
        if config_path is None:
            config_path = self.project_root / "config" / "safety_thresholds.yaml"
        else:
            config_path = Path(config_path)
        
        logger.info(f"Loading safety config from: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("✅ Safety configuration loaded")
            return config
        except FileNotFoundError:
            logger.warning(f"Safety config file not found: {config_path}")
            # Return safe defaults
            return {
                'safety_policy': {
                    'threshold': 4,
                    'categories': ['hate', 'violence', 'self_harm', 'sexual']
                }
            }
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in safety config file: {e}")
            raise


# Convenience functions for backward compatibility
def load_experiment_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load experiment config.
    
    This function provides backward compatibility for existing code
    that doesn't want to instantiate ConfigLoader directly.
    
    Args:
        config_path: Path to config file. If None, uses default location.
        
    Returns:
        Normalized experiment configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load_experiment_config(config_path)


def load_azure_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load Azure config.
    
    Args:
        config_path: Path to Azure config file. If None, uses default location.
        
    Returns:
        Azure configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load_azure_config(config_path)


def load_safety_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load safety config.
    
    Args:
        config_path: Path to safety config file. If None, uses default location.
        
    Returns:
        Safety configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load_safety_config(config_path)