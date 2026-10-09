
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "app" / "streamlit_app.py"
CLEANED_DIR = ROOT / "data" / "cleaned"


@pytest.fixture(scope="module")
def cleaned_data():
    """Load the cleaned datasets used by the dashboard."""
    filenames = {
        "customers": "customers_cleaned.csv",
        "vehicles": "vehicles_cleaned.csv",
        "policies": "policies_cleaned.csv",
        "claims": "claims_cleaned.csv",
        "payments": "payments_cleaned.csv",
    }

    data = {}
    for name, filename in filenames.items():
        path = CLEANED_DIR / filename
        assert path.exists(), f"Missing cleaned dataset: {path}"
        data[name] = pd.read_csv(path)

    return data


def test_dashboard_file_exists():
    assert APP_FILE.exists(), f"Dashboard file not found: {APP_FILE}"


def test_dashboard_starts_without_streamlit_exceptions():
    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()

    assert len(app.exception) == 0, (
        "The dashboard raised an exception: "
        + "; ".join(str(error.value) for error in app.exception)
    )


def test_dashboard_displays_main_heading():
    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()

    assert len(app.exception) == 0
    all_text = "\n".join(element.value for element in app.title)
    assert "Motor Insurance Claims & Policy Analytics" in all_text


def test_cleaned_datasets_are_not_empty(cleaned_data):
    for name, frame in cleaned_data.items():
        assert not frame.empty, f"{name} dataset is empty"


def test_core_identifiers_are_unique(cleaned_data):
    primary_keys = {
        "customers": "customer_id",
        "vehicles": "vehicle_id",
        "policies": "policy_id",
        "claims": "claim_id",
        "payments": "payment_id",
    }

    for table, key in primary_keys.items():
        assert key in cleaned_data[table].columns
        assert cleaned_data[table][key].notna().all()
        assert cleaned_data[table][key].is_unique


def test_dashboard_reference_counts(cleaned_data):
    expected_counts = {
        "customers": 20_000,
        "vehicles": 25_000,
        "policies": 25_000,
        "claims": 10_000,
        "payments": 7_000,
    }

    for table, expected in expected_counts.items():
        assert len(cleaned_data[table]) == expected, (
            f"{table} row count changed. "
            "Review the data pipeline and update the reference only "
            "if the dataset was intentionally changed."
        )


def test_premium_kpis_match_cleaned_policy_data(cleaned_data):
    policies = cleaned_data["policies"]

    premium = pd.to_numeric(
        policies["premium_amount"], errors="coerce"
    )

    assert premium.notna().all()
    assert premium.sum() == pytest.approx(795_568_771.71, abs=0.02)
    assert premium.mean() == pytest.approx(31_822.7508684, abs=0.01)


def test_claim_kpis_match_cleaned_claim_data(cleaned_data):
    claims = cleaned_data["claims"]

    amounts = pd.to_numeric(claims["claim_amount"], errors="coerce")

    assert amounts.notna().all()
    assert len(claims) == 10_000
    assert amounts.sum() == pytest.approx(2_885_436_440.65, abs=0.02)

    status_counts = (
        claims["claim_status"].astype(str).str.strip().str.lower()
        .value_counts()
    )

    assert status_counts.get("approved", 0) == 3_790
    assert status_counts.get("rejected", 0) == 1_160
    assert status_counts.get("pending", 0) == 1_791
    assert status_counts.get("settled", 0) == 3_259


def test_vehicle_type_values_match_source_data(cleaned_data):
    vehicles = cleaned_data["vehicles"]

    assert "vehicle_type" in vehicles.columns

    vehicle_types = set(
        vehicles["vehicle_type"].dropna().astype(str).str.strip()
    )

    # The supplied dataset was verified to contain only Car.
    assert vehicle_types == {"Car"}


def test_dashboard_filter_controls_exist():
    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()

    assert len(app.exception) == 0

    multiselect_labels = {
        item.label for item in app.multiselect
    }

    expected_labels = {
        "Customer state",
        "Vehicle type",
        "Policy status",
        "Policy type",
        "Claim status",
        "Claim type",
    }

    assert expected_labels.issubset(multiselect_labels)


def test_dashboard_has_reset_control():
    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()

    assert len(app.exception) == 0

    button_labels = {item.label for item in app.button}
    assert "Reset all filters" in button_labels



def test_filters_start_unselected(cleaned_data):
    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()

    assert len(app.exception) == 0

    for widget in app.multiselect:
        assert widget.value == [], (
            f"Filter '{widget.label}' should start empty "
            "so the dashboard includes all records."
        )


def test_customer_state_filter_updates_customer_metric(cleaned_data):
    customers = cleaned_data["customers"]
    state_counts = customers["state"].dropna().value_counts()

    if state_counts.empty:
        pytest.skip("No customer states available for filter testing.")

    state = str(state_counts.index[0])
    expected_customers = int(state_counts.iloc[0])

    app = AppTest.from_file(str(APP_FILE), default_timeout=30).run()
    assert len(app.exception) == 0

    state_filter = next(
        (
            widget for widget in app.multiselect
            if widget.label == "Customer state"
        ),
        None,
    )
    assert state_filter is not None

    state_filter.set_value([state]).run()
    assert len(app.exception) == 0

    customer_metrics = [
        metric for metric in app.metric
        if metric.label == "Customers"
    ]

    assert customer_metrics, (
        "Could not find the Customers KPI. Check the metric label "
        "in app/streamlit_app.py."
    )

    displayed_value = str(customer_metrics[0].value).replace(",", "")
    assert int(displayed_value) == expected_customers