
from pathlib import Path
import logging

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
REPORTS_DIR = ROOT_DIR / "reports"

TABLES = ["customers", "vehicles", "policies", "claims", "payments"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(REPORTS_DIR / "data_cleaning.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def clean_text_columns(data):
    """Strip surrounding whitespace from text values without modifying identifiers."""
    if isinstance(data, pd.DataFrame):
        frames = {"table": data}
    else:
        frames = data

    for df in frames.values():
        for column in df.select_dtypes(include=["object", "string"]).columns:
            df[column] = df[column].astype("string").str.strip()
            df[column] = df[column].replace("", pd.NA)

    return data


def clean_date_columns(data):
    """Parse known date columns consistently, retaining unavailable dates as NaT."""
    date_columns = {
        "customers": ["date_of_birth"],
        "policies": ["policy_start_date", "policy_end_date"],
        "claims": [
            "claim_date", "accident_date", "approval_date", "settlement_date"
        ],
        "payments": ["payment_date"],
    }

    for table, columns in date_columns.items():
        if table not in data:
            continue
        for column in columns:
            if column in data[table].columns:
                data[table][column] = pd.to_datetime(
                    data[table][column], errors="coerce"
                )

    return data


def validate_numeric_columns(data):
    """Convert known numeric fields safely and retain invalid values as missing."""
    numeric_columns = {
        "customers": ["age"],
        "vehicles": ["vehicle_year", "vehicle_value"],
        "policies": ["premium_amount", "coverage_amount"],
        "claims": ["claim_amount"],
        "payments": ["payment_amount"],
    }

    for table, columns in numeric_columns.items():
        if table not in data:
            continue
        for column in columns:
            if column in data[table].columns:
                data[table][column] = pd.to_numeric(
                    data[table][column], errors="coerce"
                )

    return data


def handle_missing_values(data):
    """Preserve missing values when a reliable replacement cannot be justified."""
    # Claim approval and settlement dates are legitimately unavailable
    # for Pending and Rejected claims. Financial values are not filled with zero.
    return data


def remove_duplicates(data):
    """Remove exact duplicate rows only; do not discard rows with duplicate IDs silently."""
    for table, df in data.items():
        before = len(df)
        data[table] = df.drop_duplicates().copy()
        removed = before - len(data[table])
        if removed:
            logger.warning("%s: removed %s exact duplicate rows", table, removed)

    return data


def validate_business_rules(data):
    """Log suspicious values and date sequences without silently deleting records."""
    for table, columns in {
        "vehicles": ["vehicle_value"],
        "policies": ["premium_amount", "coverage_amount"],
        "claims": ["claim_amount"],
        "payments": ["payment_amount"],
    }.items():
        if table not in data:
            continue
        for column in columns:
            if column in data[table]:
                invalid = data[table][column].lt(0).fillna(False)
                if invalid.any():
                    logger.warning(
                        "%s.%s has %s negative values",
                        table, column, int(invalid.sum())
                    )

    policies = data.get("policies")
    if policies is not None and {
        "policy_start_date", "policy_end_date"
    }.issubset(policies.columns):
        invalid = (
            policies["policy_start_date"].notna()
            & policies["policy_end_date"].notna()
            & (policies["policy_end_date"] < policies["policy_start_date"])
        )
        if invalid.any():
            logger.warning(
                "%s policies have end dates before start dates; preserved and flagged",
                int(invalid.sum()),
            )

    return data


def create_derived_columns(data, reference_date=None):
    """Create the nine required derived columns with invalid ratios/dates left missing."""
    reference_date = (
        pd.Timestamp(reference_date).normalize()
        if reference_date is not None
        else pd.Timestamp.today().normalize()
    )

    customers = data["customers"]
    vehicles = data["vehicles"]
    policies = data["policies"]
    claims = data["claims"]
    payments = data["payments"]

    # 1. Policy duration
    start = pd.to_datetime(policies["policy_start_date"], errors="coerce")
    end = pd.to_datetime(policies["policy_end_date"], errors="coerce")
    duration = (end - start).dt.days
    policies["policy_duration_days"] = duration.where(duration >= 0)

    # 2. Customer age based on date of birth and analysis reference date
    dob = pd.to_datetime(customers["date_of_birth"], errors="coerce")
    age = reference_date.year - dob.dt.year
    before_birthday = (
        (dob.dt.month > reference_date.month)
        | (
            (dob.dt.month == reference_date.month)
            & (dob.dt.day > reference_date.day)
        )
    )
    customers["customer_age"] = (age - before_birthday.astype("Int64")).astype("Int64")
    customers.loc[
        dob.isna() | (dob > reference_date), "customer_age"
    ] = pd.NA

    # 3. Vehicle age using the reference year
    vehicle_year = pd.to_numeric(vehicles["vehicle_year"], errors="coerce")
    vehicle_age = reference_date.year - vehicle_year
    vehicles["vehicle_age"] = vehicle_age.where(
        (vehicle_age >= 0) & vehicle_year.notna()
    )

    # 4 and 5. Claim processing and settlement durations
    claim_date = pd.to_datetime(claims["claim_date"], errors="coerce")
    approval_date = pd.to_datetime(claims["approval_date"], errors="coerce")
    settlement_date = pd.to_datetime(claims["settlement_date"], errors="coerce")

    processing = (approval_date - claim_date).dt.days
    settlement = (settlement_date - claim_date).dt.days

    claims["claim_processing_days"] = processing.where(processing >= 0)
    claims["claim_settlement_days"] = settlement.where(settlement >= 0)

    # Link policy-level financial values without multiplying claims by payments.
    policy_values = policies[
        ["policy_id", "premium_amount", "coverage_amount"]
    ].drop_duplicates("policy_id")

    claims = claims.drop(
        columns=["premium_amount", "coverage_amount"],
        errors="ignore",
    ).merge(
        policy_values,
        on="policy_id",
        how="left",
        validate="many_to_one",
    )

    # 6 and 7. Claim-level ratios; undefined denominators remain missing.
    claims["claim_to_premium_ratio"] = (
        pd.to_numeric(claims["claim_amount"], errors="coerce")
        / pd.to_numeric(claims["premium_amount"], errors="coerce").replace(0, np.nan)
    )
    claims["claim_to_coverage_ratio"] = (
        pd.to_numeric(claims["claim_amount"], errors="coerce")
        / pd.to_numeric(claims["coverage_amount"], errors="coerce").replace(0, np.nan)
    )

    # 8. Aggregate payments to claim level first to avoid one-to-many duplication.
    payment_totals = payments.groupby("claim_id", dropna=False).agg(
        total_payment_amount=("payment_amount", "sum")
    ).reset_index()

    claims = claims.merge(
        payment_totals,
        on="claim_id",
        how="left",
        validate="one_to_one",
    )
    claims["paid_claim_ratio"] = (
        pd.to_numeric(claims["total_payment_amount"], errors="coerce")
        / pd.to_numeric(claims["claim_amount"], errors="coerce").replace(0, np.nan)
    )

    # 9. Active flag
    policies["policy_active_flag"] = (
        policies["policy_status"]
        .astype("string")
        .str.strip()
        .str.casefold()
        .eq("active")
        .astype("int8")
    )

    data["claims"] = claims
    data["policies"] = policies
    return data


def clean_data(data):
    """Apply the cleaning steps and create derived columns for all five tables."""
    data = {name: df.copy() for name, df in data.items()}
    data = clean_text_columns(data)
    data = clean_date_columns(data)
    data = validate_numeric_columns(data)
    data = handle_missing_values(data)
    data = remove_duplicates(data)
    data = validate_business_rules(data)
    data = create_derived_columns(data)
    return data


def save_cleaned_data(data, output_dir=None):
    """Save all five cleaned tables using the required filenames."""
    output_dir = Path(output_dir) if output_dir else ROOT_DIR / "data" / "cleaned"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name in TABLES:
        if name not in data:
            raise KeyError(f"Required dataset is missing: {name}")

        output_path = output_dir / f"{name}_cleaned.csv"
        data[name].to_csv(output_path, index=False, date_format="%Y-%m-%d")
        logger.info("Saved %s (%s rows)", output_path.name, len(data[name]))

    return output_dir


def main():
    """Load raw CSVs, clean them, and save the cleaned outputs and summary."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {}

    for name in TABLES:
        path = RAW_DIR / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Required raw dataset not found: {path}")
        data[name] = pd.read_csv(path)
        logger.info("Loaded %s: %s rows", name, len(data[name]))

    original_counts = {name: len(df) for name, df in data.items()}
    cleaned = clean_data(data)
    output_dir = save_cleaned_data(cleaned)

    summary = pd.DataFrame([
        {
            "dataset": name,
            "original_rows": original_counts[name],
            "cleaned_rows": len(cleaned[name]),
            "rows_removed": original_counts[name] - len(cleaned[name]),
            "missing_cells": int(cleaned[name].isna().sum().sum()),
            "duplicate_rows": int(cleaned[name].duplicated().sum()),
            "output_file": f"data/cleaned/{name}_cleaned.csv",
        }
        for name in TABLES
    ])

    summary.to_csv(REPORTS_DIR / "data_cleaning_summary.csv", index=False)
    print("\n========== CLEANING SUMMARY ==========")
    print(summary.to_string(index=False))
    print(f"\nCleaned data saved to: {output_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Data cleaning failed")
        raise