
from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import load_all_data
from src.insurance_analysis import build_kpi_summary


ROOT = Path(__file__).resolve().parents[1]
CLEANED_DIR = ROOT / "data" / "cleaned"


@pytest.fixture(scope="module")
def insurance_data():
    if not CLEANED_DIR.exists():
        pytest.skip("Run python run_pipeline.py before analysis tests.")

    data = load_all_data(CLEANED_DIR)

    if not data or any(table.empty for table in data.values()):
        pytest.skip("Cleaned datasets are missing or empty.")

    return data


def test_all_five_tables_load(insurance_data):
    assert set(insurance_data) >= {
        "customers", "vehicles", "policies", "claims", "payments"
    }


def test_expected_primary_keys_exist(insurance_data):
    expected = {
        "customers": "customer_id",
        "vehicles": "vehicle_id",
        "policies": "policy_id",
        "claims": "claim_id",
        "payments": "payment_id",
    }

    for table_name, primary_key in expected.items():
        assert primary_key in insurance_data[table_name].columns
        assert insurance_data[table_name][primary_key].is_unique


def test_numeric_amounts_are_numeric(insurance_data):
    for table_name, column in [
        ("policies", "premium_amount"),
        ("policies", "coverage_amount"),
        ("claims", "claim_amount"),
        ("payments", "payment_amount"),
    ]:
        values = pd.to_numeric(
            insurance_data[table_name][column], errors="coerce"
        )
        non_missing_original = insurance_data[table_name][column].notna()
        assert values[non_missing_original].notna().all()



def test_kpi_summary_has_core_metrics(insurance_data):
    summary = build_kpi_summary(insurance_data)

    if isinstance(summary, pd.DataFrame):
        if {"metric", "value"}.issubset(summary.columns):
            metrics = set(summary["metric"].astype(str))
        else:
            # build_kpi_summary may return a single-row DataFrame
            # with each KPI represented by a column name.
            metrics = set(summary.columns.astype(str))
    elif isinstance(summary, dict):
        metrics = set(summary.keys())
    else:
        pytest.fail(
            "build_kpi_summary must return a dictionary or pandas DataFrame."
        )

    expected_metrics = {
        "total_customers",
        "total_policies",
        "active_policies",
        "total_claims",
        "total_claim_amount",
    }

    assert expected_metrics.issubset(metrics)

def test_kpi_summary_is_not_empty(insurance_data):
    summary = build_kpi_summary(insurance_data)
    assert summary is not None
    assert len(summary) > 0


def test_relationships_use_existing_parent_ids(insurance_data):
    relations = [
        ("vehicles", "customer_id", "customers", "customer_id"),
        ("policies", "customer_id", "customers", "customer_id"),
        ("policies", "vehicle_id", "vehicles", "vehicle_id"),
        ("claims", "policy_id", "policies", "policy_id"),
        ("claims", "customer_id", "customers", "customer_id"),
        ("payments", "claim_id", "claims", "claim_id"),
        ("payments", "policy_id", "policies", "policy_id"),
    ]

    for child, child_col, parent, parent_col in relations:
        child_values = insurance_data[child][child_col].dropna()
        parent_values = insurance_data[parent][parent_col].dropna()
        assert child_values.isin(parent_values).all(), (
            f"Invalid relationship: {child}.{child_col} "
            f"to {parent}.{parent_col}"
        )