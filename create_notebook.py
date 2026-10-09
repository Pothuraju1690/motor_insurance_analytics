
"""Create the required Motor Insurance Analytics Jupyter notebook."""

from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"
NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)

notebook = nbf.v4.new_notebook()
cells = []


def markdown(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))


markdown("""
# Motor Insurance Claims & Policy Analytics

**Purpose:** Explore the insurance portfolio, validate data quality, calculate KPIs,
study claim and premium behavior, and identify evidence-based business questions.

All findings should be interpreted as descriptive analysis, not proof of causation.
""")

markdown("## 1. Business Understanding")
markdown("""
The company manages customers, vehicles, policies, claims, and payments.
This analysis examines policy activity, premiums, claim volume and severity,
settlement performance, customer segments, vehicle patterns, and operational risks.

**Data model:** customers → policies; vehicles → policies; policies → claims;
customers → claims; claims → payments; policies → payments.
""")

markdown("## 2. Import Libraries")
code("""
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display

ROOT = Path.cwd()
if not (ROOT / "src").exists() and (ROOT.parent / "src").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_all_data
from src import visualization as viz
from src import insights as insight_engine

pd.set_option("display.max_columns", 100)
pd.set_option("display.float_format", lambda value: f"{value:,.2f}")
""")

markdown("## 3. Load Related Tables")
code("""
DATA_DIR = ROOT / "data" / "cleaned"
data = load_all_data(DATA_DIR)

for table_name, df in data.items():
    print(f"{table_name}: {df.shape[0]:,} rows × {df.shape[1]} columns")
    display(df.head(3))
""")

markdown("## 4. Understand Table Relationships")
code("""
relationships = pd.DataFrame([
    ["vehicles", "customer_id", "customers", "customer_id"],
    ["policies", "customer_id", "customers", "customer_id"],
    ["policies", "vehicle_id", "vehicles", "vehicle_id"],
    ["claims", "policy_id", "policies", "policy_id"],
    ["claims", "customer_id", "customers", "customer_id"],
    ["payments", "claim_id", "claims", "claim_id"],
    ["payments", "policy_id", "policies", "policy_id"],
], columns=["Child Table", "Child Key", "Parent Table", "Parent Key"])
display(relationships)
""")

markdown("## 5. Basic Data Understanding")
code("""
for name, df in data.items():
    print(f"\\n--- {name.upper()} ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    display(df.dtypes.rename("data_type").to_frame())
    display(df.describe(include="all").T.head(20))
""")

markdown("## 6. Data Quality Analysis")
code("""
quality_rows = []
primary_keys = {
    "customers": "customer_id",
    "vehicles": "vehicle_id",
    "policies": "policy_id",
    "claims": "claim_id",
    "payments": "payment_id",
}

for name, df in data.items():
    pk = primary_keys[name]
    quality_rows.append({
        "table": name,
        "rows": len(df),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "missing_primary_keys": int(df[pk].isna().sum()) if pk in df else None,
        "duplicate_primary_keys": int(df[pk].duplicated().sum()) if pk in df else None,
    })

quality_report = pd.DataFrame(quality_rows)
display(quality_report)
""")

markdown("## 7. Data Cleaning")
markdown("""
The reusable cleaning pipeline is implemented in `src/data_cleaner.py` and
orchestrated by `run_pipeline.py`. Raw files are preserved; cleaned files are
written to `data/cleaned/`. Missing workflow dates are not automatically invented.
Review the data-quality report and pipeline logs when anomalies are present.
""")
code("""
for name, df in data.items():
    print(f"{name}: {len(df):,} cleaned rows")
    print("Missing cells:", int(df.isna().sum().sum()))
""")

markdown("## 8. Derived Columns")
code("""
derived_columns = {
    "customers": ["customer_age"],
    "vehicles": ["vehicle_age"],
    "policies": ["policy_duration_days", "policy_active_flag"],
    "claims": [
        "claim_processing_days", "claim_settlement_days",
        "claim_to_premium_ratio", "claim_to_coverage_ratio",
        "paid_claim_ratio",
    ],
}

for table_name, columns in derived_columns.items():
    df = data.get(table_name, pd.DataFrame())
    print(f"\\n{table_name}:")
    for column in columns:
        print(f"  {column}: {'present' if column in df.columns else 'not present'}")
""")

markdown("## 9. EDA — Univariate")
code("""
policies = data["policies"]
claims = data["claims"]
vehicles = data["vehicles"]
customers = data["customers"]

for table_name, column, title in [
    ("policies", "premium_amount", "Premium Distribution"),
    ("claims", "claim_amount", "Claim Amount Distribution"),
    ("vehicles", "vehicle_age", "Vehicle Age Distribution"),
    ("customers", "customer_age", "Customer Age Distribution"),
]:
    df = data[table_name]
    if column in df:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if not values.empty:
            ax = values.plot(kind="hist", bins=30, figsize=(8, 4), title=title)
            ax.set_xlabel(column.replace("_", " ").title())
            plt.show()
        else:
            print(f"No valid values for {table_name}.{column}")
    else:
        print(f"{table_name}.{column} not available")

for table_name, column in [
    ("policies", "policy_status"),
    ("claims", "claim_status"),
    ("claims", "claim_type"),
    ("vehicles", "vehicle_type"),
]:
    df = data[table_name]
    if column in df:
        display(df[column].fillna("Unknown").value_counts().rename("count").to_frame())
""")

markdown("## 10. EDA — Bivariate")
code("""
# Premium versus policy type
if {"policy_type", "premium_amount"}.issubset(policies.columns):
    display(policies.groupby("policy_type")["premium_amount"].agg(
        ["count", "mean", "median", "sum"]
    ).sort_values("sum", ascending=False))

# Claim amount versus vehicle type
claim_vehicle = viz._claim_customer_vehicle(data)
if {"vehicle_type", "claim_amount"}.issubset(claim_vehicle.columns):
    display(claim_vehicle.groupby("vehicle_type")["claim_amount"].agg(
        ["count", "mean", "median", "sum"]
    ).sort_values("mean", ascending=False))

# Region versus claim amount
region_col = "accident_location" if "accident_location" in claims.columns else None
if region_col and "claim_amount" in claims:
    display(claims.groupby(region_col)["claim_amount"].agg(
        ["count", "mean", "sum"]
    ).sort_values("count", ascending=False).head(15))

# Claim status versus settlement time
if {"claim_status", "claim_settlement_days"}.issubset(claims.columns):
    display(claims.groupby("claim_status")["claim_settlement_days"].agg(
        ["count", "mean", "median"]
    ))
""")

markdown("## 11. EDA — Multivariate")
code("""
# Policy type, vehicle type, and claim amount
if {"policy_type", "vehicle_type", "claim_amount"}.issubset(claim_vehicle.columns):
    display(claim_vehicle.groupby(
        ["policy_type", "vehicle_type"]
    )["claim_amount"].agg(["count", "mean", "sum"]).reset_index())

# Region, claim type, and severity
if {"accident_location", "claim_type", "damage_severity"}.issubset(claims.columns):
    display(claims.groupby(
        ["accident_location", "claim_type", "damage_severity"]
    ).size().rename("claim_count").reset_index().sort_values(
        "claim_count", ascending=False
    ).head(20))

# Customer age, policy type, premium, and claims
if "customer_id" in customers and "customer_age" in customers:
    customer_age = customers[["customer_id", "customer_age"]].drop_duplicates("customer_id")
    if {"customer_id", "policy_type", "premium_amount"}.issubset(policies.columns):
        customer_policy = policies.merge(
            customer_age, on="customer_id", how="left", validate="many_to_one"
        )
        display(customer_policy.groupby("policy_type").agg(
            policies=("policy_id", "nunique"),
            average_premium=("premium_amount", "mean"),
            average_customer_age=("customer_age", "mean"),
        ))
""")

markdown("## 12. Statistical Analysis")
code("""
for table_name, column in [
    ("policies", "premium_amount"),
    ("claims", "claim_amount"),
    ("claims", "claim_settlement_days"),
]:
    df = data[table_name]
    if column in df:
        values = pd.to_numeric(df[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        ).dropna()
        if not values.empty:
            modes = values.mode()
            print(f"\\n{table_name}.{column}")
            display(pd.Series({
                "count": values.count(),
                "mean": values.mean(),
                "median": values.median(),
                "mode": modes.iloc[0] if not modes.empty else np.nan,
                "variance": values.var(),
                "standard_deviation": values.std(),
                "minimum": values.min(),
                "maximum": values.max(),
            }).to_frame("value"))
        else:
            print(f"No valid observations: {table_name}.{column}")

display(pd.read_csv(ROOT / "reports" / "policy_numeric_correlations.csv"))
display(pd.read_csv(ROOT / "reports" / "claim_numeric_correlations.csv"))
""")

markdown("## 13. KPI Analysis")
code("""
kpi_path = ROOT / "reports" / "kpi_summary.csv"
if kpi_path.exists():
    kpis = pd.read_csv(kpi_path)
    display(kpis)
else:
    print("KPI report not found. Run: python -m src.insurance_analysis")
""")

markdown("## 14. Business Questions")
code("""
# These tables provide actual evidence for the required business questions.
if {"policy_type", "premium_amount"}.issubset(policies.columns):
    print("Policy types with the highest total premium:")
    display(policies.groupby("policy_type")["premium_amount"].sum().sort_values(
        ascending=False
    ).to_frame("total_premium"))

if {"claim_type", "claim_amount"}.issubset(claims.columns):
    print("Claim types with the highest average claim amount:")
    display(claims.groupby("claim_type")["claim_amount"].agg(
        ["count", "mean", "sum"]
    ).sort_values("mean", ascending=False))

if {"damage_severity", "claim_amount"}.issubset(claims.columns):
    print("Claim amount by damage severity:")
    display(claims.groupby("damage_severity")["claim_amount"].agg(
        ["count", "mean", "sum"]
    ).sort_values("mean", ascending=False))

if {"vehicle_type", "claim_amount"}.issubset(claim_vehicle.columns):
    print("Vehicle type claim patterns:")
    display(claim_vehicle.groupby("vehicle_type")["claim_amount"].agg(
        ["count", "mean", "sum"]
    ).sort_values("count", ascending=False))

if {"claim_status", "claim_settlement_days"}.issubset(claims.columns):
    print("Settlement time by claim status:")
    display(claims.groupby("claim_status")["claim_settlement_days"].agg(
        ["count", "mean", "median"]
    ))
""")

markdown("## 15. Visualizations")
code("""
chart_functions = [
    viz.plot_policy_status,
    viz.plot_policy_type_distribution,
    viz.plot_premium_by_policy_type,
    viz.plot_monthly_claims,
    viz.plot_claim_status,
    viz.plot_claim_type_distribution,
    viz.plot_claim_amount_distribution,
    viz.plot_claim_amount_by_vehicle_type,
    viz.plot_claims_by_region,
    viz.plot_claim_severity_by_region,
    viz.plot_average_settlement_time,
    viz.plot_claim_to_premium_by_policy_type,
    viz.plot_vehicle_age_vs_claim_amount,
    viz.plot_customer_age_vs_claim_amount,
    viz.plot_vehicle_type_claim_performance,
    viz.plot_damage_severity_distribution,
    viz.plot_payment_status,
    viz.plot_monthly_premium_trend,
]

for chart_function in chart_functions:
    fig = chart_function(data)
    display(fig)
    plt.close(fig)
""")

markdown("## 16. Evidence-Based Insights")
code("""
insight_functions = [
    insight_engine.generate_portfolio_insights,
    insight_engine.generate_claim_insights,
    insight_engine.generate_premium_insights,
    insight_engine.generate_customer_insights,
    insight_engine.generate_vehicle_insights,
    insight_engine.generate_risk_patterns,
    insight_engine.generate_business_recommendations,
]

for function in insight_functions:
    print(f"\\n### {function.__name__}")
    results = function(data)
    if not results:
        print("No insight generated: required data or valid observations were unavailable.")
    else:
        display(pd.DataFrame(results))
""")

markdown("""
## Interpretation and Limitations

- Findings describe the supplied datasets and do not establish causation.
- Claim amounts are not the same as actual payment amounts.
- A claim-to-premium ratio is a descriptive comparison unless earned premium,
  exposure periods, and an approved actuarial definition are available.
- Missing workflow dates should not be invented.
- Review anomalous policy dates and data-quality findings before making decisions.
""")

notebook["cells"] = cells
notebook["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.x"},
}

output_path = NOTEBOOK_DIR / "insurance_analysis.ipynb"
nbf.write(notebook, output_path)
print(f"Notebook created: {output_path}")
print(f"Total cells: {len(cells)}")