
"""Reusable visualizations for Motor Insurance Claims & Policy Analytics."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.data_loader import load_all_data

sns.set_theme(style="whitegrid")

BASE_DIR = Path(__file__).resolve().parents[1]
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
CHART_DIR = BASE_DIR / "reports" / "charts"
REPORT_DIR = BASE_DIR / "reports"


def _table(data, name):
    """Return a table, or an empty DataFrame when unavailable."""
    return data.get(name, pd.DataFrame()).copy()


def _date(df, column):
    if column in df.columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _numeric(df, column):
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _finish(fig, title, output_dir=None):
    """Apply layout, optionally save, and return the figure."""
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    if output_dir:
        folder = Path(output_dir)
        folder.mkdir(parents=True, exist_ok=True)
        filename = (
            title.lower()
            .replace("&", "and")
            .replace(" ", "_")
            .replace("/", "_")
            + ".png"
        )
        fig.savefig(folder / filename, dpi=150, bbox_inches="tight")

    return fig


def _empty(title, message="No valid data available.", output_dir=None):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.set_axis_off()
    return _finish(fig, title, output_dir)


def _bar(series, title, xlabel, ylabel, output_dir=None, horizontal=False):
    series = series.dropna()
    if series.empty:
        return _empty(title, output_dir=output_dir)

    fig, ax = plt.subplots(figsize=(10, 5))
    if horizontal:
        series.sort_values().plot(kind="barh", ax=ax)
    else:
        series.plot(kind="bar", ax=ax)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", labelrotation=35)
    return _finish(fig, title, output_dir)


def _hist(df, column, title, xlabel, output_dir=None):
    values = pd.to_numeric(df.get(column, pd.Series(dtype=float)), errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan).dropna()

    if values.empty:
        return _empty(title, output_dir=output_dir)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(values, bins=30, kde=True, ax=ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of records")
    return _finish(fig, title, output_dir)


def _claims_with_policy(data):
    claims = _table(data, "claims")
    policies = _table(data, "policies")
    vehicles = _table(data, "vehicles")

    if claims.empty or policies.empty or "policy_id" not in claims or "policy_id" not in policies:
        return pd.DataFrame()

    policy_columns = [
        c for c in ["policy_id", "vehicle_id", "policy_type",
                    "premium_amount", "coverage_amount", "policy_status",
                    "policy_start_date", "policy_end_date"]
        if c in policies.columns
    ]
    result = claims.merge(
        policies[policy_columns].drop_duplicates("policy_id"),
        on="policy_id",
        how="left",
        suffixes=("", "_policy"),
        validate="many_to_one",
    )

    if not vehicles.empty and "vehicle_id" in result and "vehicle_id" in vehicles:
        vehicle_columns = [
            c for c in ["vehicle_id", "vehicle_type", "vehicle_make",
                        "vehicle_model", "vehicle_year", "fuel_type", "vehicle_value"]
            if c in vehicles.columns
        ]
        result = result.merge(
            vehicles[vehicle_columns].drop_duplicates("vehicle_id"),
            on="vehicle_id",
            how="left",
            suffixes=("", "_vehicle"),
            validate="many_to_one",
        )

    return result


def _claim_customer_vehicle(data):
    result = _claims_with_policy(data)
    if result.empty:
        return result

    customers = _table(data, "customers")
    if not customers.empty and "customer_id" in result and "customer_id" in customers:
        columns = [
            c for c in ["customer_id", "customer_age", "age", "state", "city", "gender"]
            if c in customers.columns
        ]
        result = result.merge(
            customers[columns].drop_duplicates("customer_id"),
            on="customer_id",
            how="left",
            suffixes=("", "_customer"),
            validate="many_to_one",
        )

    return result


def plot_policy_status(data, output_dir=None):
    policies = _table(data, "policies")
    if "policy_status" not in policies:
        return _empty("Policy Status Distribution", output_dir=output_dir)
    return _bar(
        policies["policy_status"].value_counts(),
        "Policy Status Distribution", "Policy Status", "Number of Policies",
        output_dir,
    )


def plot_policy_type_distribution(data, output_dir=None):
    policies = _table(data, "policies")
    if "policy_type" not in policies:
        return _empty("Policy Type Distribution", output_dir=output_dir)
    return _bar(
        policies["policy_type"].value_counts(),
        "Policy Type Distribution", "Policy Type", "Number of Policies",
        output_dir,
    )


def plot_premium_by_policy_type(data, output_dir=None):
    policies = _table(data, "policies")
    if not {"policy_type", "premium_amount"}.issubset(policies.columns):
        return _empty("Premium by Policy Type", output_dir=output_dir)
    policies = _numeric(policies, "premium_amount")
    values = policies.groupby("policy_type")["premium_amount"].mean().sort_values(ascending=False)
    return _bar(values, "Average Premium by Policy Type", "Policy Type",
                "Average Premium", output_dir)


def plot_monthly_claims(data, output_dir=None):
    claims = _table(data, "claims")
    if "claim_date" not in claims:
        return _empty("Monthly Claim Volume", output_dir=output_dir)
    claims = _date(claims, "claim_date").dropna(subset=["claim_date"])
    if claims.empty:
        return _empty("Monthly Claim Volume", output_dir=output_dir)
    values = claims.groupby(claims["claim_date"].dt.to_period("M")).size()
    values.index = values.index.astype(str)
    fig, ax = plt.subplots(figsize=(11, 5))
    values.plot(ax=ax, marker="o")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Claims")
    ax.tick_params(axis="x", labelrotation=45)
    return _finish(fig, "Monthly Claim Volume", output_dir)


def plot_claim_status(data, output_dir=None):
    claims = _table(data, "claims")
    if "claim_status" not in claims:
        return _empty("Claim Status Distribution", output_dir=output_dir)
    return _bar(claims["claim_status"].value_counts(), "Claim Status Distribution",
                "Claim Status", "Number of Claims", output_dir)


def plot_claim_type_distribution(data, output_dir=None):
    claims = _table(data, "claims")
    if "claim_type" not in claims:
        return _empty("Claim Type Distribution", output_dir=output_dir)
    return _bar(claims["claim_type"].value_counts(), "Claim Type Distribution",
                "Claim Type", "Number of Claims", output_dir)


def plot_claim_amount_distribution(data, output_dir=None):
    claims = _table(data, "claims")
    if "claim_amount" not in claims:
        return _empty("Claim Amount Distribution", output_dir=output_dir)
    return _hist(claims, "claim_amount", "Claim Amount Distribution",
                 "Claim Amount", output_dir)


def plot_claim_amount_by_vehicle_type(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    if not {"vehicle_type", "claim_amount"}.issubset(df.columns):
        return _empty("Claim Amount by Vehicle Type", output_dir=output_dir)
    df = _numeric(df, "claim_amount")
    values = df.groupby("vehicle_type")["claim_amount"].mean().sort_values(ascending=False)
    return _bar(values, "Average Claim Amount by Vehicle Type", "Vehicle Type",
                "Average Claim Amount", output_dir)


def plot_claims_by_region(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    region = "accident_location" if "accident_location" in df else (
        "state" if "state" in df else None
    )
    if region is None:
        return _empty("Claims by Region", output_dir=output_dir)
    values = df[region].fillna("Unknown").value_counts().head(15)
    return _bar(values, "Claims by Region (Top 15)", region.replace("_", " ").title(),
                "Number of Claims", output_dir, horizontal=True)


def plot_claim_severity_by_region(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    region = "accident_location" if "accident_location" in df else (
        "state" if "state" in df else None
    )
    if region is None or "damage_severity" not in df:
        return _empty("Claim Severity by Region", output_dir=output_dir)
    top_regions = df[region].fillna("Unknown").value_counts().head(10).index
    subset = df[df[region].fillna("Unknown").isin(top_regions)]
    table = pd.crosstab(
        subset[region].fillna("Unknown"), subset["damage_severity"].fillna("Unknown")
    )
    if table.empty:
        return _empty("Claim Severity by Region", output_dir=output_dir)
    fig, ax = plt.subplots(figsize=(11, 6))
    table.plot(kind="bar", stacked=True, ax=ax)
    ax.set_xlabel(region.replace("_", " ").title())
    ax.set_ylabel("Number of Claims")
    ax.tick_params(axis="x", labelrotation=35)
    ax.legend(title="Damage Severity")
    return _finish(fig, "Claim Severity by Region", output_dir)


def plot_average_settlement_time(data, output_dir=None):
    claims = _table(data, "claims")
    if not {"claim_date", "settlement_date"}.issubset(claims.columns):
        return _empty("Average Claim Settlement Time", output_dir=output_dir)
    claims = _date(_date(claims, "claim_date"), "settlement_date")
    claims["settlement_days"] = (
        claims["settlement_date"] - claims["claim_date"]
    ).dt.days
    valid = claims.loc[claims["settlement_days"].ge(0), "settlement_days"]
    if valid.empty:
        return _empty("Average Claim Settlement Time", output_dir=output_dir)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(["Average"], [valid.mean()])
    ax.set_ylabel("Days")
    return _finish(fig, "Average Claim Settlement Time", output_dir)


def plot_claim_to_premium_by_policy_type(data, output_dir=None):
    policies = _table(data, "policies")
    claims = _table(data, "claims")
    if not {"policy_id", "policy_type", "premium_amount"}.issubset(policies.columns):
        return _empty("Claim Amount to Premium by Policy Type", output_dir=output_dir)
    if not {"policy_id", "claim_amount"}.issubset(claims.columns):
        return _empty("Claim Amount to Premium by Policy Type", output_dir=output_dir)

    policy_claims = claims.groupby("policy_id", as_index=False)["claim_amount"].sum()
    policy_data = policies.merge(policy_claims, on="policy_id", how="left", validate="one_to_one")
    policy_data["claim_amount"] = policy_data["claim_amount"].fillna(0)
    policy_data = _numeric(_numeric(policy_data, "premium_amount"), "claim_amount")
    grouped = policy_data.groupby("policy_type").agg(
        claim_amount=("claim_amount", "sum"),
        premium_amount=("premium_amount", "sum"),
    )
    grouped["ratio_pct"] = np.where(
        grouped["premium_amount"] != 0,
        grouped["claim_amount"] / grouped["premium_amount"] * 100,
        np.nan,
    )
    return _bar(grouped["ratio_pct"].sort_values(ascending=False),
                "Claim Amount to Premium by Policy Type",
                "Policy Type", "Claim Amount / Premium (%)", output_dir)


def plot_vehicle_age_vs_claim_amount(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    if "vehicle_age" not in df and "vehicle_year" in df:
        df["vehicle_age"] = pd.Timestamp.today().year - pd.to_numeric(
            df["vehicle_year"], errors="coerce"
        )
    if not {"vehicle_age", "claim_amount"}.issubset(df.columns):
        return _empty("Vehicle Age vs Claim Amount", output_dir=output_dir)
    df = _numeric(_numeric(df, "vehicle_age"), "claim_amount").dropna(
        subset=["vehicle_age", "claim_amount"]
    )
    if df.empty:
        return _empty("Vehicle Age vs Claim Amount", output_dir=output_dir)
    grouped = df.groupby("vehicle_age")["claim_amount"].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    grouped.plot(ax=ax, marker="o")
    ax.set_xlabel("Vehicle Age (Years)")
    ax.set_ylabel("Average Claim Amount")
    return _finish(fig, "Vehicle Age vs Average Claim Amount", output_dir)


def plot_customer_age_vs_claim_amount(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    age_col = "customer_age" if "customer_age" in df else "age"
    if age_col not in df or "claim_amount" not in df:
        return _empty("Customer Age vs Claim Amount", output_dir=output_dir)
    df = _numeric(_numeric(df, age_col), "claim_amount").dropna(
        subset=[age_col, "claim_amount"]
    )
    if df.empty:
        return _empty("Customer Age vs Claim Amount", output_dir=output_dir)
    df["age_group"] = pd.cut(
        df[age_col], bins=[0, 25, 35, 45, 55, 65, 120],
        labels=["18–25", "26–35", "36–45", "46–55", "56–65", "66+"],
        include_lowest=True,
    )
    values = df.groupby("age_group", observed=False)["claim_amount"].mean()
    return _bar(values, "Customer Age Group vs Average Claim Amount",
                "Customer Age Group", "Average Claim Amount", output_dir)


def plot_vehicle_type_claim_performance(data, output_dir=None):
    df = _claim_customer_vehicle(data)
    if not {"vehicle_type", "claim_amount"}.issubset(df.columns):
        return _empty("Vehicle Type Claim Performance", output_dir=output_dir)
    df = _numeric(df, "claim_amount")
    grouped = df.groupby("vehicle_type").agg(
        claim_count=("claim_id", "count"),
        average_claim_amount=("claim_amount", "mean"),
    )
    if grouped.empty:
        return _empty("Vehicle Type Claim Performance", output_dir=output_dir)
    fig, ax = plt.subplots(figsize=(10, 5))
    grouped["claim_count"].plot(kind="bar", ax=ax, alpha=0.8)
    ax.set_xlabel("Vehicle Type")
    ax.set_ylabel("Number of Claims")
    ax.tick_params(axis="x", labelrotation=35)
    return _finish(fig, "Vehicle Type Claim Performance (Claim Counts)", output_dir)


def plot_damage_severity_distribution(data, output_dir=None):
    claims = _table(data, "claims")
    if "damage_severity" not in claims:
        return _empty("Damage Severity Distribution", output_dir=output_dir)
    return _bar(claims["damage_severity"].fillna("Unknown").value_counts(),
                "Damage Severity Distribution", "Damage Severity",
                "Number of Claims", output_dir)


def plot_payment_status(data, output_dir=None):
    payments = _table(data, "payments")
    if "payment_status" not in payments:
        return _empty("Payment Status Distribution", output_dir=output_dir)
    return _bar(payments["payment_status"].fillna("Unknown").value_counts(),
                "Payment Status Distribution", "Payment Status",
                "Number of Payments", output_dir)


def plot_monthly_premium_trend(data, output_dir=None):
    policies = _table(data, "policies")
    if not {"policy_start_date", "premium_amount"}.issubset(policies.columns):
        return _empty("Monthly Premium Trend", output_dir=output_dir)
    policies = _date(policies, "policy_start_date")
    policies = _numeric(policies, "premium_amount").dropna(
        subset=["policy_start_date", "premium_amount"]
    )
    if policies.empty:
        return _empty("Monthly Premium Trend", output_dir=output_dir)
    values = policies.groupby(
        policies["policy_start_date"].dt.to_period("M")
    )["premium_amount"].sum()
    values.index = values.index.astype(str)
    fig, ax = plt.subplots(figsize=(11, 5))
    values.plot(ax=ax, marker="o")
    ax.set_xlabel("Policy Start Month")
    ax.set_ylabel("Total Premium")
    ax.tick_params(axis="x", labelrotation=45)
    return _finish(fig, "Monthly Premium Trend", output_dir)


def run_statistical_analysis(data, output_dir=None):
    """Save descriptive statistics and numeric correlations."""
    output_dir = Path(output_dir or REPORT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "premium_amount": _table(data, "policies").get(
            "premium_amount", pd.Series(dtype=float)
        ),
        "claim_amount": _table(data, "claims").get(
            "claim_amount", pd.Series(dtype=float)
        ),
    }

    claims = _table(data, "claims")
    if {"claim_date", "settlement_date"}.issubset(claims.columns):
        claims = _date(_date(claims, "claim_date"), "settlement_date")
        tables["settlement_days"] = (
            claims["settlement_date"] - claims["claim_date"]
        ).dt.days

    rows = []
    for name, values in tables.items():
        values = pd.to_numeric(values, errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        ).dropna()
        if values.empty:
            continue
        modes = values.mode()
        rows.append({
            "metric": name,
            "count": int(values.count()),
            "mean": values.mean(),
            "median": values.median(),
            "mode": modes.iloc[0] if not modes.empty else np.nan,
            "variance": values.var(),
            "standard_deviation": values.std(),
            "minimum": values.min(),
            "maximum": values.max(),
        })

    pd.DataFrame(rows).to_csv(output_dir / "statistical_summary.csv", index=False)

    policies = _table(data, "policies")
    claims = _table(data, "claims")

    policy_numeric = policies.select_dtypes(include="number")
    claim_numeric = claims.select_dtypes(include="number")

    policy_numeric.corr().to_csv(
        output_dir / "policy_numeric_correlations.csv"
    )
    claim_numeric.corr().to_csv(
        output_dir / "claim_numeric_correlations.csv"
    )


def main():
    """Generate all required charts and statistical reports."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all_data(CLEANED_DIR)

    chart_functions = [
        plot_policy_status,
        plot_policy_type_distribution,
        plot_premium_by_policy_type,
        plot_monthly_claims,
        plot_claim_status,
        plot_claim_type_distribution,
        plot_claim_amount_distribution,
        plot_claim_amount_by_vehicle_type,
        plot_claims_by_region,
        plot_claim_severity_by_region,
        plot_average_settlement_time,
        plot_claim_to_premium_by_policy_type,
        plot_vehicle_age_vs_claim_amount,
        plot_customer_age_vs_claim_amount,
        plot_vehicle_type_claim_performance,
        plot_damage_severity_distribution,
        plot_payment_status,
        plot_monthly_premium_trend,
    ]

    for function in chart_functions:
        try:
            function(data, CHART_DIR)
            print(f"Generated: {function.__name__}")
        except Exception as exc:
            print(f"ERROR in {function.__name__}: {exc}")
            raise

    run_statistical_analysis(data, REPORT_DIR)
    print(f"Charts saved to: {CHART_DIR}")


if __name__ == "__main__":
    main()