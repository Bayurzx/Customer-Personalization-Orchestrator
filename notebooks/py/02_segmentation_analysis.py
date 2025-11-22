# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Customer Segmentation Analysis & Validation
# 
# This notebook analyzes the quality of customer segmentation results and validates that segments meet business requirements.
# 
# **Objectives:**
# - Visualize segment distribution
# - Calculate segment statistics (mean, median per feature)
# - Validate segments are balanced (no segment <10% of total)
# - Document segment definitions

# %%
# Standard imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path().absolute().parent.parent
sys.path.insert(0, str(project_root))

# Import segmentation agent
from src.agents.segmentation_agent import (
    load_customer_data, 
    segment_customers, 
    generate_segment_summary,
    validate_segmentation
)

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("✓ Imports successful")

# %% [markdown]
# ## 1. Load Customer Data and Generate Segments

# %%
# Load customer data
print("Loading customer data...")
customers_df = load_customer_data('../../data/raw/customers.csv')
print(f"Loaded {len(customers_df)} customers")

# Display basic info
print("\nCustomer Data Overview:")
print(customers_df.info())
print("\nFirst 5 customers:")
print(customers_df.head())

# %%
# Generate segments using rule-based method
print("Generating segments using rule-based method...")
segments_df = segment_customers(customers_df, method="rules")
print(f"Generated {len(segments_df)} segment assignments")

# Validate segmentation
try:
    validate_segmentation(segments_df)
    print("✓ Segmentation validation passed")
except Exception as e:
    print(f"⚠ Segmentation validation warning: {e}")

print("\nSegment assignments preview:")
print(segments_df.head())

# %% [markdown]
# ## 2. Segment Distribution Analysis

# %%
# Calculate segment distribution
segment_counts = segments_df['segment'].value_counts()
segment_percentages = (segment_counts / len(segments_df) * 100).round(1)

print("Segment Distribution:")
for segment, count in segment_counts.items():
    percentage = segment_percentages[segment]
    print(f"  {segment}: {count} customers ({percentage}%)")

# Check balance requirement (no segment <10%)
print("\nBalance Check (>10% requirement):")
balanced = True
for segment, percentage in segment_percentages.items():
    status = "✓" if percentage >= 10 else "⚠"
    print(f"  {status} {segment}: {percentage}%")
    if percentage < 10:
        balanced = False

if balanced:
    print("✓ All segments meet the 10% minimum requirement")
else:
    print("⚠ Some segments are below 10% threshold")

# %%
# Visualize segment distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Bar chart
segment_counts.plot(kind='bar', ax=ax1, color='skyblue', edgecolor='black')
ax1.set_title('Customer Segment Distribution', fontsize=14, fontweight='bold')
ax1.set_xlabel('Segment')
ax1.set_ylabel('Number of Customers')
ax1.tick_params(axis='x', rotation=45)

# Add percentage labels on bars
for i, (segment, count) in enumerate(segment_counts.items()):
    percentage = segment_percentages[segment]
    ax1.text(i, count + 1, f'{percentage}%', ha='center', va='bottom', fontweight='bold')

# Pie chart
colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
ax2.pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%', 
        colors=colors[:len(segment_counts)], startangle=90)
ax2.set_title('Segment Distribution (Pie Chart)', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Segment Statistics Analysis

# %%
# Merge segments with customer data for detailed analysis
analysis_df = customers_df.merge(segments_df[['customer_id', 'segment']], on='customer_id')

print("Segment Statistics Summary:")
print("=" * 50)

# Calculate statistics by segment
numeric_features = ['age', 'purchase_frequency', 'avg_order_value', 
                   'last_engagement_days', 'historical_open_rate', 'historical_click_rate']

segment_stats = analysis_df.groupby('segment')[numeric_features].agg(['mean', 'median', 'std', 'count'])

# Display formatted statistics
for segment in segment_counts.index:
    print(f"\n{segment}:")
    segment_data = analysis_df[analysis_df['segment'] == segment]
    
    print(f"  Size: {len(segment_data)} customers ({segment_percentages[segment]}%)")
    print(f"  Age: {segment_data['age'].mean():.1f} ± {segment_data['age'].std():.1f} years")
    print(f"  Purchase Frequency: {segment_data['purchase_frequency'].mean():.1f} ± {segment_data['purchase_frequency'].std():.1f} per year")
    print(f"  Avg Order Value: ${segment_data['avg_order_value'].mean():.2f} ± ${segment_data['avg_order_value'].std():.2f}")
    print(f"  Last Engagement: {segment_data['last_engagement_days'].mean():.1f} ± {segment_data['last_engagement_days'].std():.1f} days ago")
    print(f"  Open Rate: {segment_data['historical_open_rate'].mean():.3f} ± {segment_data['historical_open_rate'].std():.3f}")
    print(f"  Click Rate: {segment_data['historical_click_rate'].mean():.3f} ± {segment_data['historical_click_rate'].std():.3f}")

# %%
# Create detailed statistics table
stats_summary = []

for segment in segment_counts.index:
    segment_data = analysis_df[analysis_df['segment'] == segment]
    
    stats_summary.append({
        'Segment': segment,
        'Count': len(segment_data),
        'Percentage': f"{segment_percentages[segment]}%",
        'Avg Age': f"{segment_data['age'].mean():.1f}",
        'Avg Purchase Freq': f"{segment_data['purchase_frequency'].mean():.1f}",
        'Avg Order Value': f"${segment_data['avg_order_value'].mean():.2f}",
        'Avg Days Since Engagement': f"{segment_data['last_engagement_days'].mean():.1f}",
        'Avg Open Rate': f"{segment_data['historical_open_rate'].mean():.3f}",
        'Avg Click Rate': f"{segment_data['historical_click_rate'].mean():.3f}"
    })

stats_table = pd.DataFrame(stats_summary)
print("\nSegment Statistics Table:")
print(stats_table.to_string(index=False))

# %% [markdown]
# ## 4. Feature Distribution by Segment

# %%
# Visualize key features by segment
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.ravel()

features_to_plot = [
    ('age', 'Age Distribution'),
    ('purchase_frequency', 'Purchase Frequency'),
    ('avg_order_value', 'Average Order Value ($)'),
    ('last_engagement_days', 'Days Since Last Engagement'),
    ('historical_open_rate', 'Historical Open Rate'),
    ('historical_click_rate', 'Historical Click Rate')
]

for i, (feature, title) in enumerate(features_to_plot):
    # Box plot for each feature by segment
    sns.boxplot(data=analysis_df, x='segment', y=feature, ax=axes[i])
    axes[i].set_title(title, fontweight='bold')
    axes[i].tick_params(axis='x', rotation=45)
    
    # Add mean markers
    segment_means = analysis_df.groupby('segment')[feature].mean()
    for j, (segment, mean_val) in enumerate(segment_means.items()):
        axes[i].plot(j, mean_val, marker='D', color='red', markersize=8, label='Mean' if j == 0 else "")
    
    if i == 0:  # Add legend only to first subplot
        axes[i].legend()

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Segment Definitions and Business Interpretation

# %%
# Generate comprehensive segment summary
segment_summary = generate_segment_summary(segments_df)

print("SEGMENT DEFINITIONS AND BUSINESS INTERPRETATION")
print("=" * 60)

# Define business interpretations for each segment
business_interpretations = {
    "High-Value Recent": {
        "description": "Premium customers with high spending and recent engagement",
        "characteristics": "High AOV (>$200), recent activity (<30 days), likely Gold tier",
        "marketing_strategy": "Exclusive offers, premium product launches, VIP treatment",
        "retention_priority": "High - protect and nurture these valuable customers"
    },
    "At-Risk": {
        "description": "Previously active customers showing signs of disengagement", 
        "characteristics": "Moderate purchase history but declining engagement (>30 days)",
        "marketing_strategy": "Re-engagement campaigns, win-back offers, personalized outreach",
        "retention_priority": "Critical - immediate intervention needed"
    },
    "New Customer": {
        "description": "Recently acquired customers with limited purchase history",
        "characteristics": "Low purchase frequency (<3), learning about brand",
        "marketing_strategy": "Onboarding sequences, educational content, first-purchase incentives",
        "retention_priority": "Medium - focus on conversion and education"
    },
    "Standard": {
        "description": "Regular customers with moderate activity levels",
        "characteristics": "Consistent but not exceptional engagement or spending",
        "marketing_strategy": "Regular promotions, loyalty programs, upselling opportunities",
        "retention_priority": "Medium - maintain engagement and encourage growth"
    },
    "Loyal Frequent": {
        "description": "High-frequency customers with strong engagement",
        "characteristics": "High purchase frequency (>12), good engagement rates (>0.4)",
        "marketing_strategy": "Loyalty rewards, referral programs, brand advocacy",
        "retention_priority": "High - leverage for growth and advocacy"
    }
}

for segment_name, segment_data in segment_summary["segments"].items():
    print(f"\n{segment_name.upper()}")
    print("-" * len(segment_name))
    
    # Basic stats
    print(f"Size: {segment_data['size']} customers ({segment_data['percentage']}%)")
    print(f"Definition: {segment_data['definition']}")
    
    # Characteristics
    chars = segment_data['characteristics']
    print(f"Key Metrics:")
    print(f"  • Avg Purchase Frequency: {chars['avg_purchase_frequency']}/year")
    print(f"  • Avg Order Value: ${chars['avg_order_value']}")
    print(f"  • Avg Engagement Score: {chars['avg_engagement_score']}")
    
    # Business interpretation
    if segment_name in business_interpretations:
        interp = business_interpretations[segment_name]
        print(f"Business Description: {interp['description']}")
        print(f"Key Characteristics: {interp['characteristics']}")
        print(f"Marketing Strategy: {interp['marketing_strategy']}")
        print(f"Retention Priority: {interp['retention_priority']}")

# %% [markdown]
# ## 6. Validation Summary and Recommendations

# %%
print("SEGMENTATION VALIDATION SUMMARY")
print("=" * 40)

# Check all validation criteria
validation_results = {
    "Total Customers": len(segments_df),
    "Number of Segments": len(segments_df['segment'].unique()),
    "Unique Assignment": segments_df['customer_id'].is_unique,
    "Segment Range": 3 <= len(segments_df['segment'].unique()) <= 5,
    "Balance Check": all(percentage >= 10 for percentage in segment_percentages),
    "Human-Readable Labels": all(segment in business_interpretations for segment in segment_counts.index)
}

print("Validation Criteria:")
for criterion, result in validation_results.items():
    status = "✓" if result else "✗"
    print(f"  {status} {criterion}: {result}")

# Overall validation status
all_passed = all(validation_results.values())
print(f"\nOverall Validation: {'✓ PASSED' if all_passed else '✗ FAILED'}")

# Recommendations
print("\nRECOMMENDATIONS:")
if all_passed:
    print("✓ Segmentation meets all requirements and is ready for production use")
    print("✓ Segments are well-balanced and have clear business interpretations")
    print("✓ Proceed to next phase: Content Retrieval & Indexing")
else:
    print("⚠ Address validation issues before proceeding:")
    if not validation_results["Balance Check"]:
        print("  - Consider adjusting segmentation rules to improve balance")
    if not validation_results["Segment Range"]:
        print("  - Adjust number of segments to be between 3-5")

# Final statistics
print(f"\nFINAL STATISTICS:")
print(f"  Total Customers Segmented: {len(segments_df)}")
print(f"  Segments Created: {len(segments_df['segment'].unique())}")
print(f"  Largest Segment: {segment_counts.iloc[0]} customers ({segment_percentages.iloc[0]}%)")
print(f"  Smallest Segment: {segment_counts.iloc[-1]} customers ({segment_percentages.iloc[-1]}%)")

print("\n" + "="*60)
print("SEGMENTATION ANALYSIS COMPLETE")
print("="*60)