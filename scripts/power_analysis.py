#!/usr/bin/env python3
"""
Power Analysis for A/B/n Experiment
Task 4.1: Experiment Design

Calculate required sample sizes for detecting meaningful lift
in personalization experiment.
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import yaml
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config() -> Dict:
    """Load experiment configuration."""
    config_path = Path(__file__).parent.parent / "config" / "experiment_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_sample_size_proportion(
    p1: float, 
    p2: float, 
    alpha: float = 0.05, 
    power: float = 0.80
) -> int:
    """
    Calculate required sample size per group for proportion test.
    
    Args:
        p1: Control proportion (baseline rate)
        p2: Treatment proportion (baseline + lift)
        alpha: Significance level
        power: Statistical power
        
    Returns:
        Required sample size per group
    """
    # Z-scores for alpha and power
    z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-tailed test
    z_beta = stats.norm.ppf(power)
    
    # Pooled proportion
    p_pooled = (p1 + p2) / 2
    
    # Effect size
    effect_size = abs(p2 - p1)
    
    # Sample size calculation
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2
    denominator = effect_size**2
    
    n = numerator / denominator
    return int(np.ceil(n))

def power_analysis_grid(
    baseline_rates: Dict[str, float],
    effect_sizes: List[float],
    sample_sizes: List[int],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Generate power analysis grid for different scenarios.
    
    Args:
        baseline_rates: Dictionary of baseline rates for different metrics
        effect_sizes: List of relative effect sizes to test
        sample_sizes: List of sample sizes to test
        alpha: Significance level
        
    Returns:
        DataFrame with power analysis results
    """
    results = []
    
    for metric, baseline in baseline_rates.items():
        for effect_size in effect_sizes:
            treatment_rate = baseline * (1 + effect_size)
            
            for n in sample_sizes:
                # Calculate power for this scenario
                power = calculate_power_proportion(baseline, treatment_rate, n, alpha)
                
                results.append({
                    'metric': metric,
                    'baseline_rate': baseline,
                    'effect_size': effect_size,
                    'treatment_rate': treatment_rate,
                    'sample_size_per_arm': n,
                    'power': power,
                    'alpha': alpha
                })
    
    return pd.DataFrame(results)

def calculate_power_proportion(
    p1: float, 
    p2: float, 
    n: int, 
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for proportion test.
    
    Args:
        p1: Control proportion
        p2: Treatment proportion  
        n: Sample size per group
        alpha: Significance level
        
    Returns:
        Statistical power (0-1)
    """
    # Effect size
    effect_size = abs(p2 - p1)
    
    # Standard error under null hypothesis
    p_pooled = (p1 + p2) / 2
    se_null = np.sqrt(2 * p_pooled * (1 - p_pooled) / n)
    
    # Standard error under alternative hypothesis
    se_alt = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n)
    
    # Critical value
    z_alpha = stats.norm.ppf(1 - alpha/2)
    
    # Power calculation
    z_beta = (effect_size - z_alpha * se_null) / se_alt
    power = stats.norm.cdf(z_beta)
    
    return power

def analyze_current_experiment(config: Dict) -> Dict:
    """
    Analyze power for current experiment configuration.
    
    Args:
        config: Experiment configuration
        
    Returns:
        Power analysis results
    """
    # Extract configuration
    baseline_rates = config['experiment']['simulation']['baseline_rates']
    total_customers = config['experiment']['sample_size']['total_customers']
    num_arms = 4  # 1 control + 3 treatment
    per_arm_size = total_customers // num_arms
    
    expected_uplift = config['experiment']['simulation']['expected_uplift']['mean']
    alpha = config['experiment']['statistical_testing']['alpha']
    
    results = {}
    
    for metric, baseline in baseline_rates.items():
        treatment_rate = baseline * (1 + expected_uplift)
        
        # Calculate power for current sample size
        power = calculate_power_proportion(baseline, treatment_rate, per_arm_size, alpha)
        
        # Calculate required sample size for 80% power
        required_n = calculate_sample_size_proportion(baseline, treatment_rate, alpha, 0.80)
        
        results[metric] = {
            'baseline_rate': float(baseline),
            'expected_treatment_rate': float(treatment_rate),
            'expected_lift_percent': float(expected_uplift * 100),
            'current_sample_size_per_arm': int(per_arm_size),
            'current_power': float(power),
            'required_sample_size_80_power': int(required_n),
            'power_adequate': bool(power >= 0.80)
        }
    
    return results

def create_power_visualizations(power_df: pd.DataFrame, output_dir: Path):
    """Create power analysis visualizations."""
    output_dir.mkdir(exist_ok=True)
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Power vs Sample Size by Effect Size
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = power_df['metric'].unique()
    
    for i, metric in enumerate(metrics):
        metric_data = power_df[power_df['metric'] == metric]
        
        for effect_size in metric_data['effect_size'].unique():
            data = metric_data[metric_data['effect_size'] == effect_size]
            axes[i].plot(data['sample_size_per_arm'], data['power'], 
                        marker='o', label=f'{effect_size:.0%} lift')
        
        axes[i].axhline(y=0.80, color='red', linestyle='--', alpha=0.7, label='80% Power')
        axes[i].set_xlabel('Sample Size per Arm')
        axes[i].set_ylabel('Statistical Power')
        axes[i].set_title(f'Power Analysis: {metric.replace("_", " ").title()}')
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'power_analysis_by_metric.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Heatmap of Power by Sample Size and Effect Size
    for metric in metrics:
        metric_data = power_df[power_df['metric'] == metric]
        pivot_data = metric_data.pivot(index='effect_size', 
                                     columns='sample_size_per_arm', 
                                     values='power')
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn', 
                   vmin=0, vmax=1, cbar_kws={'label': 'Statistical Power'})
        plt.title(f'Power Analysis Heatmap: {metric.replace("_", " ").title()}')
        plt.xlabel('Sample Size per Arm')
        plt.ylabel('Effect Size (Relative Lift)')
        plt.tight_layout()
        plt.savefig(output_dir / f'power_heatmap_{metric}.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main power analysis execution."""
    print("🔬 Running Power Analysis for Experiment Design...")
    
    # Load configuration
    config = load_config()
    
    # Analyze current experiment setup
    print("\n📊 Analyzing Current Experiment Configuration...")
    current_results = analyze_current_experiment(config)
    
    print("\nCurrent Experiment Power Analysis:")
    print("=" * 50)
    
    for metric, results in current_results.items():
        print(f"\n{metric.replace('_', ' ').title()}:")
        print(f"  Baseline Rate: {results['baseline_rate']:.1%}")
        print(f"  Expected Treatment Rate: {results['expected_treatment_rate']:.1%}")
        print(f"  Expected Lift: {results['expected_lift_percent']:.1f}%")
        print(f"  Current Sample Size per Arm: {results['current_sample_size_per_arm']}")
        print(f"  Current Statistical Power: {results['current_power']:.1%}")
        print(f"  Required Sample Size (80% power): {results['required_sample_size_80_power']}")
        print(f"  Power Adequate: {'✅ Yes' if results['power_adequate'] else '❌ No'}")
    
    # Generate comprehensive power analysis
    print("\n📈 Generating Comprehensive Power Analysis...")
    
    baseline_rates = config['experiment']['simulation']['baseline_rates']
    effect_sizes = config['power_analysis']['effect_sizes']
    sample_sizes = config['power_analysis']['sample_sizes']
    alpha = config['experiment']['statistical_testing']['alpha']
    
    power_df = power_analysis_grid(baseline_rates, effect_sizes, sample_sizes, alpha)
    
    # Create visualizations
    output_dir = Path("reports/visualizations")
    create_power_visualizations(power_df, output_dir)
    
    # Save detailed results
    results_dir = Path("data/processed")
    results_dir.mkdir(exist_ok=True)
    
    # Save power analysis grid
    power_df.to_csv(results_dir / "power_analysis_grid.csv", index=False)
    
    # Save current experiment analysis
    with open(results_dir / "experiment_power_analysis.json", 'w') as f:
        json.dump(current_results, f, indent=2)
    
    # Summary recommendations
    print("\n💡 Recommendations:")
    print("=" * 50)
    
    # Check if current sample size is adequate
    adequate_power = all(r['power_adequate'] for r in current_results.values())
    
    if adequate_power:
        print("✅ Current sample size (62 per arm) provides adequate statistical power (>80%)")
        print("   for detecting 15% relative lift across all metrics.")
    else:
        print("⚠️  Current sample size may not provide adequate statistical power for all metrics.")
        
        # Find maximum required sample size
        max_required = max(r['required_sample_size_80_power'] for r in current_results.values())
        print(f"   Consider increasing to {max_required} customers per arm for 80% power.")
    
    print(f"\n📁 Results saved to:")
    print(f"   - Power analysis grid: {results_dir / 'power_analysis_grid.csv'}")
    print(f"   - Current experiment analysis: {results_dir / 'experiment_power_analysis.json'}")
    print(f"   - Visualizations: {output_dir}")
    
    print("\n✅ Power Analysis Complete!")

if __name__ == "__main__":
    main()