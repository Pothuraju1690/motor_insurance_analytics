
import pandas as pd

from src.data_cleaner import remove_duplicates, create_derived_columns


def test_remove_duplicates():
    data = {
        "customers": pd.DataFrame({
            "customer_id": ["C1", "C1"],
            "customer_name": ["A", "A"],
        })
    }

    result = remove_duplicates(data)

    assert len(result["customers"]) == 1


def test_create_derived_columns():
    data = {
        "customers": pd.DataFrame({
            "customer_id": ["C1"],
            "date_of_birth": ["2000-01-01"],
        }),
        "vehicles": pd.DataFrame({
            "vehicle_id": ["V1"],
            "vehicle_year": [2020],
        }),
        "policies": pd.DataFrame({
            "policy_id": ["P1"],
            "policy_start_date": ["2025-01-01"],
            "policy_end_date": ["2026-01-01"],
            "premium_amount": [1000],
            "coverage_amount": [10000],
            "policy_status": ["Active"],
        }),
        "claims": pd.DataFrame({
            "claim_id": ["CL1"],
            "policy_id": ["P1"],
            "claim_date": ["2025-02-01"],
            "approval_date": ["2025-02-04"],
            "settlement_date": ["2025-02-11"],
            "claim_amount": [500],
        }),
        "payments": pd.DataFrame({
            "payment_id": ["PAY1"],
            "claim_id": ["CL1"],
            "policy_id": ["P1"],
            "payment_amount": [400],
        }),
    }

    result = create_derived_columns(data, reference_date="2026-06-01")

    assert result["policies"].loc[0, "policy_duration_days"] == 365
    assert result["policies"].loc[0, "policy_active_flag"] == 1
    assert result["vehicles"].loc[0, "vehicle_age"] == 6
    assert result["claims"].loc[0, "claim_processing_days"] == 3
    assert result["claims"].loc[0, "claim_settlement_days"] == 10
    assert result["claims"].loc[0, "claim_to_premium_ratio"] == 0.5
    assert result["claims"].loc[0, "claim_to_coverage_ratio"] == 0.05
    assert result["claims"].loc[0, "paid_claim_ratio"] == 0.8