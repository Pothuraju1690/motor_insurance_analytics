
import pandas as pd

from src.validation import (
    validate_customers,
    validate_vehicles,
    validate_policies,
    validate_claims,
    validate_payments,
    validate_relationships,
    validate_all_tables,
)


def sample_data():
    customers = pd.DataFrame({
        "customer_id": [1],
        "customer_name": ["Test Customer"],
        "gender": ["Male"],
        "date_of_birth": ["1995-01-01"],
        "age": [31],
        "city": ["Hyderabad"],
        "state": ["Telangana"],
        "occupation": ["Engineer"],
    })

    vehicles = pd.DataFrame({
        "vehicle_id": [101],
        "customer_id": [1],
        "vehicle_type": ["Car"],
        "vehicle_make": ["Test Make"],
        "vehicle_model": ["Test Model"],
        "vehicle_year": [2022],
        "fuel_type": ["Petrol"],
        "vehicle_value": [800000],
    })

    policies = pd.DataFrame({
        "policy_id": [201],
        "customer_id": [1],
        "vehicle_id": [101],
        "policy_start_date": ["2025-01-01"],
        "policy_end_date": ["2026-01-01"],
        "policy_type": ["Comprehensive"],
        "premium_amount": [12000],
        "coverage_amount": [800000],
        "policy_status": ["Active"],
        "payment_frequency": ["Annual"],
    })

    claims = pd.DataFrame({
        "claim_id": [301],
        "policy_id": [201],
        "customer_id": [1],
        "claim_date": ["2025-06-01"],
        "accident_date": ["2025-05-30"],
        "claim_type": ["Accident"],
        "accident_location": ["Hyderabad"],
        "claim_amount": [50000],
        "claim_status": ["Pending"],
        "approval_date": [None],
        "settlement_date": [None],
        "damage_severity": ["Moderate"],
    })

    payments = pd.DataFrame({
        "payment_id": [401],
        "claim_id": [301],
        "policy_id": [201],
        "payment_date": ["2025-06-15"],
        "payment_amount": [0],
        "payment_status": ["Pending"],
        "payment_method": ["Bank Transfer"],
    })

    return {
        "customers": customers,
        "vehicles": vehicles,
        "policies": policies,
        "claims": claims,
        "payments": payments,
    }


def test_all_valid_tables_pass():
    results = validate_all_tables(sample_data())
    assert results["passed"] is True


def test_duplicate_customer_primary_key_fails():
    data = sample_data()
    data["customers"] = pd.concat(
        [data["customers"], data["customers"]],
        ignore_index=True,
    )
    result = validate_customers(data["customers"])
    assert result["passed"] is False
    assert any("duplicate" in issue.lower() for issue in result["issues"])


def test_missing_required_column_fails():
    data = sample_data()["vehicles"].drop(columns=["vehicle_type"])
    result = validate_vehicles(data)
    assert result["passed"] is False
    assert any("vehicle_type" in issue for issue in result["issues"])


def test_orphan_foreign_key_fails():
    data = sample_data()
    data["vehicles"].loc[0, "customer_id"] = 9999
    result = validate_relationships(data)
    assert result["passed"] is False
    assert any("do not exist" in issue for issue in result["issues"])


def test_missing_claim_dates_are_warnings_not_failures():
    data = sample_data()
    result = validate_claims(data["claims"])
    assert result["passed"] is True
    assert result.get("warnings")


def test_reversed_policy_dates_are_reported_and_preserved():
    data = sample_data()["policies"]
    data.loc[0, "policy_start_date"] = "2026-01-01"
    data.loc[0, "policy_end_date"] = "2025-01-01"

    result = validate_policies(data)

    assert result["passed"] is True
    assert len(data) == 1
    assert any("end dates before start dates" in issue for issue in result["issues"])


def test_missing_table_is_reported():
    data = sample_data()
    del data["payments"]

    result = validate_all_tables(data)

    assert result["passed"] is False
    assert result["payments"]["passed"] is False