
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):
    root_dir = Path(__file__).resolve().parents[1]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from src.logger import setup_logger

logger = setup_logger("validation", "reports/validation.log")

TABLE_NAMES = [
    "customers",
    "vehicles",
    "policies",
    "claims",
    "payments",
]

PRIMARY_KEYS = {
    "customers": "customer_id",
    "vehicles": "vehicle_id",
    "policies": "policy_id",
    "claims": "claim_id",
    "payments": "payment_id",
}

FOREIGN_KEYS = {
    "vehicles": {"customer_id": ("customers", "customer_id")},
    "policies": {
        "customer_id": ("customers", "customer_id"),
        "vehicle_id": ("vehicles", "vehicle_id"),
    },
    "claims": {
        "policy_id": ("policies", "policy_id"),
        "customer_id": ("customers", "customer_id"),
    },
    "payments": {
        "claim_id": ("claims", "claim_id"),
        "policy_id": ("policies", "policy_id"),
    },
}


def _report(table_name, data, required_columns, primary_key):
    """Return structural and primary-key validation results."""
    issues = []

    if not isinstance(data, pd.DataFrame):
        return {
            "table": table_name,
            "rows": 0,
            "passed": False,
            "issues": ["Input is not a pandas DataFrame."],
        }

    missing_columns = sorted(set(required_columns) - set(data.columns))
    if missing_columns:
        issues.append(f"Missing columns: {missing_columns}")

    if primary_key in data.columns:
        if data[primary_key].isna().any():
            issues.append(f"{primary_key} contains missing values.")
        if data[primary_key].duplicated().any():
            issues.append(f"{primary_key} contains duplicate values.")

    return {
        "table": table_name,
        "rows": len(data),
        "passed": len(issues) == 0,
        "issues": issues,
    }


def validate_customers(data):
    required = [
        "customer_id", "customer_name", "gender", "date_of_birth",
        "age", "city", "state", "occupation",
    ]
    return _report("customers", data, required, "customer_id")


def validate_vehicles(data):
    required = [
        "vehicle_id", "customer_id", "vehicle_type", "vehicle_make",
        "vehicle_model", "vehicle_year", "fuel_type", "vehicle_value",
    ]
    return _report("vehicles", data, required, "vehicle_id")


def validate_policies(data):
    required = [
        "policy_id", "customer_id", "vehicle_id", "policy_start_date",
        "policy_end_date", "policy_type", "premium_amount",
        "coverage_amount", "policy_status", "payment_frequency",
    ]
    result = _report("policies", data, required, "policy_id")

    if {"policy_start_date", "policy_end_date"}.issubset(data.columns):
        start = pd.to_datetime(data["policy_start_date"], errors="coerce")
        end = pd.to_datetime(data["policy_end_date"], errors="coerce")
        invalid = (start.notna() & end.notna() & (end < start)).sum()
        if invalid:
            result["issues"].append(
                f"{invalid} policies have end dates before start dates."
            )
            # This is a data-quality warning, not a reason to discard the row.
            logger.warning(
                "%s policies have end dates before start dates; preserved.",
                invalid,
            )

    return result


def validate_claims(data):
    required = [
        "claim_id", "policy_id", "customer_id", "claim_date",
        "accident_date", "claim_type", "accident_location",
        "claim_amount", "claim_status", "approval_date",
        "settlement_date", "damage_severity",
    ]
    result = _report("claims", data, required, "claim_id")

    # Missing approval/settlement dates can be legitimate for pending,
    # rejected, or not-yet-settled claims, so report them as context.
    for column in ("approval_date", "settlement_date"):
        if column in data.columns:
            missing = int(data[column].isna().sum())
            if missing:
                result.setdefault("warnings", []).append(
                    f"{column}: {missing} missing values; preserved."
                )

    return result


def validate_payments(data):
    required = [
        "payment_id", "claim_id", "policy_id", "payment_date",
        "payment_amount", "payment_status", "payment_method",
    ]
    return _report("payments", data, required, "payment_id")


def validate_relationships(data):
    """Check declared foreign keys without changing the source tables."""
    issues = []

    for child_name, relations in FOREIGN_KEYS.items():
        child = data.get(child_name)

        if child is None:
            issues.append(f"Missing table: {child_name}")
            continue

        for child_column, (parent_name, parent_column) in relations.items():
            parent = data.get(parent_name)

            if parent is None:
                issues.append(f"Missing parent table: {parent_name}")
                continue

            if child_column not in child.columns:
                issues.append(
                    f"{child_name} is missing foreign-key column {child_column}."
                )
                continue

            if parent_column not in parent.columns:
                issues.append(
                    f"{parent_name} is missing referenced column {parent_column}."
                )
                continue

            # Empty child references are reported separately from orphan IDs.
            non_null = child[child_column].dropna()
            orphan_mask = ~non_null.isin(parent[parent_column].dropna())
            orphan_count = int(orphan_mask.sum())

            if orphan_count:
                issues.append(
                    f"{child_name}.{child_column}: {orphan_count} "
                    f"references do not exist in {parent_name}.{parent_column}."
                )

            null_count = int(child[child_column].isna().sum())
            if null_count:
                issues.append(
                    f"{child_name}.{child_column}: {null_count} missing references."
                )

    return {
        "table": "relationships",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def validate_all_tables(data):
    """Run table-level and relationship checks and return one report."""
    validators = {
        "customers": validate_customers,
        "vehicles": validate_vehicles,
        "policies": validate_policies,
        "claims": validate_claims,
        "payments": validate_payments,
    }

    results = {}

    for name, validator in validators.items():
        if name not in data:
            results[name] = {
                "table": name,
                "rows": 0,
                "passed": False,
                "issues": [f"Missing table: {name}"],
            }
        else:
            results[name] = validator(data[name])

    results["relationships"] = validate_relationships(data)
    results["passed"] = all(
        result.get("passed", False)
        for key, result in results.items()
        if key != "passed"
    )

    return results


def main():
    from src.data_loader import load_all_data

    root = Path(__file__).resolve().parents[1]
    cleaned_dir = root / "data" / "cleaned"
    raw_dir = root / "data" / "raw"
    data_dir = cleaned_dir if cleaned_dir.exists() else raw_dir

    data = load_all_data(data_dir)
    results = validate_all_tables(data)

    print("\n=== VALIDATION REPORT ===")
    for name, result in results.items():
        if name == "passed":
            continue

        status = "PASS" if result.get("passed") else "CHECK"
        print(f"\n{name.upper()}: {status}")

        for issue in result.get("issues", []):
            print(f"  - {issue}")

        for warning in result.get("warnings", []):
            print(f"  - WARNING: {warning}")

    print(f"\nOverall validation passed: {results['passed']}")


if __name__ == "__main__":
    main()