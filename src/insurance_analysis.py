
from pathlib import Path
import logging

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
CLEANED_DIR = ROOT_DIR / "data" / "cleaned"
REPORTS_DIR = ROOT_DIR / "reports"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TABLE_NAMES = ["customers", "vehicles", "policies", "claims", "payments"]


def load_analysis_data():
    """Load the five cleaned tables, supporting both current and required filenames."""
    data = {}

    for name in TABLE_NAMES:
        candidates = [
            CLEANED_DIR / f"{name}_cleaned.csv",
            CLEANED_DIR / f"{name}.csv",
        ]
        file_path = next((p for p in candidates if p.exists()), None)

        if file_path is None:
            raise FileNotFoundError(
                f"Cleaned file for '{name}' not found in {CLEANED_DIR}"
            )

        data[name] = pd.read_csv(file_path)
        logger.info("Loaded %s: %s rows", name, len(data[name]))

    return data


def number(value):
    """Convert a numeric result to a regular float, using zero for empty results."""
    result = pd.to_numeric(value, errors="coerce")
    return float(result) if pd.notna(result) else 0.0


def safe_divide(numerator, denominator):
    """Return a ratio, or NaN when the denominator is zero or unavailable."""
    numerator = number(numerator)
    denominator = number(denominator)
    return numerator / denominator if denominator else np.nan


def date_column(df, column):
    """Return a parsed date Series; invalid and missing values remain NaT."""
    if column not in df.columns:
        return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    return pd.to_datetime(df[column], errors="coerce")


def numeric_column(df, column):
    """Return a numeric Series; invalid and missing values remain NaN."""
    if column not in df.columns:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


# -------------------- Portfolio analysis --------------------

def calculate_total_customers(customers):
    return customers["customer_id"].nunique()


def calculate_total_policies(policies):
    return policies["policy_id"].nunique()


def calculate_active_policies(policies):
    return policies["policy_status"].astype("string").str.strip().str.casefold().eq("active").sum()


def calculate_expired_policies(policies):
    return policies["policy_status"].astype("string").str.strip().str.casefold().eq("expired").sum()


def calculate_cancelled_policies(policies):
    return policies["policy_status"].astype("string").str.strip().str.casefold().eq("cancelled").sum()


def calculate_renewed_policies(policies):
    return policies["policy_status"].astype("string").str.strip().str.casefold().eq("renewed").sum()


# -------------------- Premium analysis --------------------

def calculate_total_premium(policies):
    return number(numeric_column(policies, "premium_amount").sum())


def calculate_average_premium(policies):
    return number(numeric_column(policies, "premium_amount").mean())


def calculate_average_coverage(policies):
    return number(numeric_column(policies, "coverage_amount").mean())


def calculate_premium_by_policy_type(policies):
    return (
        policies.assign(premium_amount=numeric_column(policies, "premium_amount"))
        .groupby("policy_type", dropna=False)["premium_amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


# -------------------- Claims analysis --------------------

def calculate_total_claims(claims):
    return claims["claim_id"].nunique()


def calculate_approved_claims(claims):
    return claims["claim_status"].astype("string").str.strip().str.casefold().eq("approved").sum()


def calculate_rejected_claims(claims):
    return claims["claim_status"].astype("string").str.strip().str.casefold().eq("rejected").sum()


def calculate_pending_claims(claims):
    return claims["claim_status"].astype("string").str.strip().str.casefold().eq("pending").sum()


def calculate_settled_claims(claims):
    return claims["claim_status"].astype("string").str.strip().str.casefold().eq("settled").sum()


def calculate_total_claim_amount(claims):
    return number(numeric_column(claims, "claim_amount").sum())


def calculate_average_claim_amount(claims):
    return number(numeric_column(claims, "claim_amount").mean())


def calculate_claim_approval_rate(claims):
    # Approval rate uses all unique claims as the denominator.
    return safe_divide(calculate_approved_claims(claims), calculate_total_claims(claims)) * 100


def calculate_claim_rejection_rate(claims):
    # Rejection rate uses all unique claims as the denominator.
    return safe_divide(calculate_rejected_claims(claims), calculate_total_claims(claims)) * 100


# -------------------- Settlement and payments --------------------

def calculate_average_claim_processing_days(claims):
    claim_dates = date_column(claims, "claim_date")
    approval_dates = date_column(claims, "approval_date")
    days = (approval_dates - claim_dates).dt.days
    valid = days[(days >= 0) & days.notna()]
    return number(valid.mean())


def calculate_average_claim_settlement_days(claims):
    claim_dates = date_column(claims, "claim_date")
    settlement_dates = date_column(claims, "settlement_date")
    days = (settlement_dates - claim_dates).dt.days
    valid = days[(days >= 0) & days.notna()]
    return number(valid.mean())


def calculate_total_payment_amount(payments):
    return number(numeric_column(payments, "payment_amount").sum())


def calculate_average_payment_amount(payments):
    return number(numeric_column(payments, "payment_amount").mean())


# -------------------- Risk ratios --------------------

def calculate_claim_to_premium_ratio(claims, policies):
    """Ratio of total requested claim amount to total policy premium; not a loss ratio by earned premium."""
    claim_total = calculate_total_claim_amount(claims)
    premium_total = calculate_total_premium(policies)
    return safe_divide(claim_total, premium_total)


def calculate_claim_to_coverage_ratio(claims, policies):
    """Ratio of total requested claim amount to total policy coverage amount."""
    claim_total = calculate_total_claim_amount(claims)
    coverage_total = number(numeric_column(policies, "coverage_amount").sum())
    return safe_divide(claim_total, coverage_total)


def calculate_paid_claim_ratio(payments, claims):
    """Ratio of recorded payment amounts to requested claim amounts, using ratio of sums."""
    return safe_divide(
        calculate_total_payment_amount(payments),
        calculate_total_claim_amount(claims),
    )


# -------------------- Customer and vehicle analysis --------------------

def analyze_customer_claims(data):
    customers, claims = data["customers"], data["claims"]
    result = claims.groupby("customer_id", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index()
    return result.merge(customers, on="customer_id", how="left", validate="many_to_one")


def analyze_customer_premium(data):
    customers, policies = data["customers"], data["policies"]
    result = policies.groupby("customer_id", dropna=False).agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
    ).reset_index()
    return result.merge(customers, on="customer_id", how="left", validate="many_to_one")


def analyze_vehicle_claims(data):
    vehicles, claims, policies = data["vehicles"], data["claims"], data["policies"]
    vehicle_policies = policies[["policy_id", "vehicle_id"]].drop_duplicates("policy_id")
    linked = claims.merge(vehicle_policies, on="policy_id", how="left", validate="many_to_one")
    result = linked.groupby("vehicle_id", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index()
    return result.merge(vehicles, on="vehicle_id", how="left", validate="many_to_one")


def analyze_vehicle_risk_patterns(data):
    """Summarize observed claim frequency and amounts by vehicle characteristics."""
    vehicle_claims = analyze_vehicle_claims(data)
    outputs = {}

    for column in ["vehicle_type", "vehicle_make", "fuel_type", "vehicle_year"]:
        if column in vehicle_claims.columns:
            outputs[column] = (
                vehicle_claims.groupby(column, dropna=False)
                .agg(
                    vehicles=("vehicle_id", "nunique"),
                    total_claims=("claim_count", "sum"),
                    total_claim_amount=("total_claim_amount", "sum"),
                    average_claim_amount=("average_claim_amount", "mean"),
                )
                .reset_index()
                .sort_values("total_claims", ascending=False)
            )

    return outputs


# -------------------- Business breakdowns --------------------

def analyze_claim_type(claims):
    return claims.groupby("claim_type", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index().sort_values("claim_count", ascending=False)


def analyze_claim_status(claims):
    return claims.groupby("claim_status", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index().sort_values("claim_count", ascending=False)


def analyze_policy_type(policies):
    return policies.groupby("policy_type", dropna=False).agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
        average_coverage=("coverage_amount", "mean"),
    ).reset_index().sort_values("total_premium", ascending=False)


def analyze_region(claims):
    return claims.groupby("accident_location", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index().sort_values("claim_count", ascending=False)


def analyze_vehicle_type(data):
    return analyze_vehicle_risk_patterns(data).get("vehicle_type", pd.DataFrame())


def analyze_damage_severity(claims):
    return claims.groupby("damage_severity", dropna=False).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).reset_index().sort_values("claim_count", ascending=False)


# -------------------- Statistical analysis --------------------

def calculate_descriptive_statistics(df, columns):
    """Calculate standard descriptive statistics for selected numeric columns."""
    existing = [column for column in columns if column in df.columns]
    if not existing:
        return pd.DataFrame()
    numeric = df[existing].apply(pd.to_numeric, errors="coerce")
    return numeric.agg(["count", "mean", "median", "std", "var", "min", "max"]).T.reset_index(names="metric")


def calculate_numeric_correlations(df, columns):
    """Calculate pairwise Pearson correlations for available numeric columns."""
    existing = [column for column in columns if column in df.columns]
    if len(existing) < 2:
        return pd.DataFrame()
    numeric = df[existing].apply(pd.to_numeric, errors="coerce")
    return numeric.corr()


# -------------------- Build report outputs --------------------

def build_kpi_summary(data):
    customers = data["customers"]
    policies = data["policies"]
    claims = data["claims"]
    payments = data["payments"]

    kpis = {
        "total_customers": calculate_total_customers(customers),
        "total_policies": calculate_total_policies(policies),
        "active_policies": calculate_active_policies(policies),
        "expired_policies": calculate_expired_policies(policies),
        "cancelled_policies": calculate_cancelled_policies(policies),
        "renewed_policies": calculate_renewed_policies(policies),
        "total_premium": calculate_total_premium(policies),
        "average_premium": calculate_average_premium(policies),
        "average_coverage": calculate_average_coverage(policies),
        "total_claims": calculate_total_claims(claims),
        "approved_claims": calculate_approved_claims(claims),
        "rejected_claims": calculate_rejected_claims(claims),
        "pending_claims": calculate_pending_claims(claims),
        "settled_claims": calculate_settled_claims(claims),
        "total_claim_amount": calculate_total_claim_amount(claims),
        "average_claim_amount": calculate_average_claim_amount(claims),
        "claim_approval_rate_pct": calculate_claim_approval_rate(claims),
        "claim_rejection_rate_pct": calculate_claim_rejection_rate(claims),
        "average_claim_processing_days": calculate_average_claim_processing_days(claims),
        "average_claim_settlement_days": calculate_average_claim_settlement_days(claims),
        "total_payment_amount": calculate_total_payment_amount(payments),
        "average_payment_amount": calculate_average_payment_amount(payments),
        "claim_to_premium_ratio": calculate_claim_to_premium_ratio(claims, policies),
        "claim_to_coverage_ratio": calculate_claim_to_coverage_ratio(claims, policies),
        "paid_claim_ratio": calculate_paid_claim_ratio(payments, claims),
    }

    return pd.DataFrame([kpis])


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_analysis_data()

    kpi_summary = build_kpi_summary(data)
    kpi_path = REPORTS_DIR / "kpi_summary.csv"
    kpi_summary.to_csv(kpi_path, index=False)

    outputs = {
        "premium_by_policy_type.csv": calculate_premium_by_policy_type(data["policies"]),
        "claims_by_type.csv": analyze_claim_type(data["claims"]),
        "claims_by_status.csv": analyze_claim_status(data["claims"]),
        "claims_by_region.csv": analyze_region(data["claims"]),
        "claims_by_severity.csv": analyze_damage_severity(data["claims"]),
        "customer_claim_analysis.csv": analyze_customer_claims(data),
        "customer_premium_analysis.csv": analyze_customer_premium(data),
        "vehicle_claim_analysis.csv": analyze_vehicle_claims(data),
        "premium_statistics.csv": calculate_descriptive_statistics(
            data["policies"], ["premium_amount", "coverage_amount"]
        ),
        "claim_statistics.csv": calculate_descriptive_statistics(
            data["claims"], ["claim_amount"]
        ),
        "payment_statistics.csv": calculate_descriptive_statistics(
            data["payments"], ["payment_amount"]
        ),
    }

    for filename, result in outputs.items():
        result.to_csv(REPORTS_DIR / filename, index=False)

    print("\n========== KPI SUMMARY ==========")
    print(kpi_summary.T.to_string(header=False))
    print(f"\nKPI report: {kpi_path}")
    print(f"Analysis reports saved to: {REPORTS_DIR}")


if __name__ == "__main__":
    main()