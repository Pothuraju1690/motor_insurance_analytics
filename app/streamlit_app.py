
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. APPLICATION SETUP
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_all_data

DATA_DIR = ROOT / "data" / "cleaned"

st.set_page_config(
    page_title="Motor Insurance Intelligence",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Motor Insurance Claims & Policy Analytics")
st.markdown(
    "An interactive analytical dashboard for monitoring policy portfolios, "
    "premium performance, claims, settlements, customers, and vehicles."
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 14px 16px;
        border-radius: 12px;
    }
    div[data-testid="stMetricValue"] {font-size: 1.65rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. DATA LOADING
# ---------------------------------------------------------
@st.cache_data(show_spinner="Loading cleaned insurance datasets...")
def load_datasets():
    if not DATA_DIR.exists():
        return {}
    return load_all_data(DATA_DIR)


def numeric_column(frame, column):
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def text_options(frame, column):
    if column not in frame.columns:
        return []
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def normalize_text(series):
    return series.astype("string").str.strip().str.casefold()


def money(value):
    if pd.isna(value):
        value = 0
    return f"₹{float(value):,.0f}"


def number(value):
    if pd.isna(value):
        value = 0
    return f"{float(value):,.0f}"


def percent(value):
    if pd.isna(value):
        value = 0
    return f"{float(value):,.1f}%"


def average(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if not values.empty else 0.0


def safe_divide(numerator, denominator):
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


data = load_datasets()

required_tables = {
    "customers", "vehicles", "policies", "claims", "payments"
}

if not data:
    st.error("No cleaned datasets were loaded.")
    st.info("From the project root, run: `python run_pipeline.py`")
    st.stop()

missing_tables = required_tables - set(data.keys())

if missing_tables:
    st.error("Missing datasets: " + ", ".join(sorted(missing_tables)))
    st.write("Tables detected:", ", ".join(sorted(data.keys())))
    st.stop()

for table_name in required_tables:
    if not isinstance(data[table_name], pd.DataFrame):
        st.error(f"The {table_name} dataset is not a DataFrame.")
        st.stop()

    if data[table_name].empty:
        st.error(f"The {table_name} dataset contains no rows.")
        st.stop()

# Work with copies. Original CSV files are never modified by the dashboard.
customers = data["customers"].copy()
vehicles = data["vehicles"].copy()
policies = data["policies"].copy()
claims = data["claims"].copy()
payments = data["payments"].copy()


# ---------------------------------------------------------
# 3. SIDEBAR FILTERS
# ---------------------------------------------------------

# ---------------------------------------------------------
# 3. PROFESSIONAL SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.title("Dashboard Controls")
st.sidebar.caption(
    "Choose filters to narrow the analysis. Empty selections mean All."
)

FILTER_KEYS = [
    "filter_states",
    "filter_vehicle_types",
    "filter_policy_statuses",
    "filter_policy_types",
    "filter_claim_statuses",
    "filter_claim_types",
]

# Initialize widget state before creating the widgets.
for filter_key in FILTER_KEYS:
    if filter_key not in st.session_state:
        st.session_state[filter_key] = []

if st.sidebar.button(
    "Reset all filters",
    use_container_width=True,
    type="secondary",
):
    for filter_key in FILTER_KEYS:
        st.session_state[filter_key] = []
    st.rerun()

state_options = text_options(customers, "state")
vehicle_options = text_options(vehicles, "vehicle_type")
policy_status_options = text_options(policies, "policy_status")
policy_type_options = text_options(policies, "policy_type")
claim_status_options = text_options(claims, "claim_status")
claim_type_options = text_options(claims, "claim_type")

with st.sidebar.expander("Customer & Vehicle", expanded=True):
    selected_states = st.multiselect(
        "Customer state",
        options=state_options,
        key="filter_states",
        placeholder="All states",
        help="Leave empty to include all states.",
    )

    selected_vehicle_types = st.multiselect(
        "Vehicle type",
        options=vehicle_options,
        key="filter_vehicle_types",
        placeholder="All vehicle types",
        help="The current dataset contains only Car.",
    )

with st.sidebar.expander("Policies", expanded=True):
    selected_policy_statuses = st.multiselect(
        "Policy status",
        options=policy_status_options,
        key="filter_policy_statuses",
        placeholder="All policy statuses",
    )

    selected_policy_types = st.multiselect(
        "Policy type",
        options=policy_type_options,
        key="filter_policy_types",
        placeholder="All policy types",
    )

with st.sidebar.expander("Claims", expanded=False):
    selected_claim_statuses = st.multiselect(
        "Claim status",
        options=claim_status_options,
        key="filter_claim_statuses",
        placeholder="All claim statuses",
    )

    selected_claim_types = st.multiselect(
        "Claim type",
        options=claim_type_options,
        key="filter_claim_types",
        placeholder="All claim types",
    )

active_filter_count = sum(
    bool(value)
    for value in [
        selected_states,
        selected_vehicle_types,
        selected_policy_statuses,
        selected_policy_types,
        selected_claim_statuses,
        selected_claim_types,
    ]
)

st.sidebar.divider()
st.sidebar.metric("Active filters", active_filter_count)
st.sidebar.caption(
    "No selection = All. Select one or more values to filter."
)



# ---------------------------------------------------------
# 4. APPLY FILTERS WHILE PRESERVING TABLE RELATIONSHIPS
# ---------------------------------------------------------

# ---------------------------------------------------------
# 4. APPLY FILTERS — EMPTY SELECTION MEANS ALL
# ---------------------------------------------------------
filtered_customers = customers.copy()
filtered_vehicles = vehicles.copy()
filtered_policies = policies.copy()
filtered_claims = claims.copy()
filtered_payments = payments.copy()

# Apply customer filters only when selected.
if selected_states and "state" in filtered_customers.columns:
    filtered_customers = filtered_customers[
        filtered_customers["state"].astype(str).isin(selected_states)
    ]

customer_ids = set(filtered_customers["customer_id"].dropna())

# Apply vehicle filters.
if "customer_id" in filtered_vehicles.columns:
    filtered_vehicles = filtered_vehicles[
        filtered_vehicles["customer_id"].isin(customer_ids)
    ]

if selected_vehicle_types and "vehicle_type" in filtered_vehicles.columns:
    filtered_vehicles = filtered_vehicles[
        filtered_vehicles["vehicle_type"].astype(str).isin(
            selected_vehicle_types
        )
    ]

vehicle_ids = set(filtered_vehicles["vehicle_id"].dropna())

# Apply policy filters and retain relationships.
if "customer_id" in filtered_policies.columns:
    filtered_policies = filtered_policies[
        filtered_policies["customer_id"].isin(customer_ids)
    ]

if "vehicle_id" in filtered_policies.columns:
    filtered_policies = filtered_policies[
        filtered_policies["vehicle_id"].isin(vehicle_ids)
    ]

if (
    selected_policy_statuses
    and "policy_status" in filtered_policies.columns
):
    filtered_policies = filtered_policies[
        filtered_policies["policy_status"].astype(str).isin(
            selected_policy_statuses
        )
    ]

if selected_policy_types and "policy_type" in filtered_policies.columns:
    filtered_policies = filtered_policies[
        filtered_policies["policy_type"].astype(str).isin(
            selected_policy_types
        )
    ]

policy_ids = set(filtered_policies["policy_id"].dropna())

# Apply claim filters.
if "customer_id" in filtered_claims.columns:
    filtered_claims = filtered_claims[
        filtered_claims["customer_id"].isin(customer_ids)
    ]

if "policy_id" in filtered_claims.columns:
    filtered_claims = filtered_claims[
        filtered_claims["policy_id"].isin(policy_ids)
    ]

if selected_claim_statuses and "claim_status" in filtered_claims.columns:
    filtered_claims = filtered_claims[
        filtered_claims["claim_status"].astype(str).isin(
            selected_claim_statuses
        )
    ]

if selected_claim_types and "claim_type" in filtered_claims.columns:
    filtered_claims = filtered_claims[
        filtered_claims["claim_type"].astype(str).isin(
            selected_claim_types
        )
    ]

claim_ids = set(filtered_claims["claim_id"].dropna())

# Apply payment relationships.
if "policy_id" in filtered_payments.columns:
    filtered_payments = filtered_payments[
        filtered_payments["policy_id"].isin(policy_ids)
    ]

if "claim_id" in filtered_payments.columns:
    filtered_payments = filtered_payments[
        filtered_payments["claim_id"].isin(claim_ids)
    ]

filtered = {
    "customers": filtered_customers,
    "vehicles": filtered_vehicles,
    "policies": filtered_policies,
    "claims": filtered_claims,
    "payments": filtered_payments,
}

st.caption(
    f"Current selection: {len(filtered_customers):,} customers · "
    f"{len(filtered_vehicles):,} vehicles · "
    f"{len(filtered_policies):,} policies · "
    f"{len(filtered_claims):,} claims · "
    f"{len(filtered_payments):,} payments"
)

if any(frame.empty for frame in filtered.values()):
    st.warning(
        "At least one dataset has no matching records. "
        "Clear or broaden the filters to restore the full results."
    )

# ---------------------------------------------------------
# 5. DERIVE ANALYSIS TABLES
# ---------------------------------------------------------
def build_claim_analysis(tables):
    c = tables["claims"].copy()
    p = tables["policies"].copy()
    v = tables["vehicles"].copy()
    cu = tables["customers"].copy()

    # Select only required lookup columns to avoid ambiguous merge columns.
    if "policy_id" in p.columns:
        policy_columns = [
            col for col in [
                "policy_id", "policy_type", "premium_amount",
                "coverage_amount", "vehicle_id", "customer_id",
            ] if col in p.columns
        ]
        c = c.merge(
            p[policy_columns].drop_duplicates("policy_id"),
            on="policy_id",
            how="left",
            suffixes=("", "_policy"),
        )

    if "vehicle_id" in c.columns and "vehicle_id" in v.columns:
        vehicle_columns = [
            col for col in [
                "vehicle_id", "vehicle_type", "vehicle_year",
                "fuel_type", "vehicle_value",
            ] if col in v.columns
        ]
        c = c.merge(
            v[vehicle_columns].drop_duplicates("vehicle_id"),
            on="vehicle_id",
            how="left",
            suffixes=("", "_vehicle"),
        )

    if "customer_id" in c.columns and "customer_id" in cu.columns:
        customer_columns = [
            col for col in [
                "customer_id", "age", "city", "state", "occupation",
            ] if col in cu.columns
        ]
        c = c.merge(
            cu[customer_columns].drop_duplicates("customer_id"),
            on="customer_id",
            how="left",
            suffixes=("", "_customer"),
        )

    for column in [
        "claim_amount", "premium_amount", "coverage_amount",
        "claim_processing_days", "claim_settlement_days",
        "vehicle_age", "customer_age",
    ]:
        if column in c.columns:
            c[column] = pd.to_numeric(c[column], errors="coerce")

    # Use a known DOB or current age only when it is available.
    if "customer_age" not in c.columns and "age" in c.columns:
        c["customer_age"] = pd.to_numeric(c["age"], errors="coerce")

    if (
        "vehicle_age" not in c.columns
        and "vehicle_year" in c.columns
    ):
        year = pd.to_numeric(c["vehicle_year"], errors="coerce")
        c["vehicle_age"] = pd.Timestamp.today().year - year

    if (
        "claim_settlement_days" not in c.columns
        and {"claim_date", "settlement_date"}.issubset(c.columns)
    ):
        claim_date = pd.to_datetime(c["claim_date"], errors="coerce")
        settlement_date = pd.to_datetime(
            c["settlement_date"], errors="coerce"
        )
        c["claim_settlement_days"] = (
            settlement_date - claim_date
        ).dt.days

    if (
        "claim_to_premium_ratio" not in c.columns
        and {"claim_amount", "premium_amount"}.issubset(c.columns)
    ):
        c["claim_to_premium_ratio"] = (
            c["claim_amount"]
            / c["premium_amount"].replace(0, float("nan"))
        )

    return c


claim_analysis = build_claim_analysis(filtered)


# ---------------------------------------------------------
# 6. CHART HELPERS
# ---------------------------------------------------------
def show_bar(
    frame,
    category,
    value,
    title,
    xlabel=None,
    ylabel=None,
    aggregation="sum",
    top_n=15,
):
    if category not in frame.columns:
        st.info(f"Chart unavailable: '{category}' is not present.")
        return

    if value is None:
        counts = frame[category].dropna().astype(str).value_counts().head(top_n)
        if counts.empty:
            st.info("No records are available for this chart.")
            return
        fig, ax = plt.subplots(figsize=(9, 4))
        counts.sort_values().plot(kind="barh", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel or "Number of records")
        ax.set_ylabel(ylabel or category.replace("_", " ").title())
    else:
        if value not in frame.columns:
            st.info(f"Chart unavailable: '{value}' is not present.")
            return

        temp = frame[[category, value]].copy()
        temp[value] = pd.to_numeric(temp[value], errors="coerce")
        temp = temp.dropna(subset=[category, value])

        if temp.empty:
            st.info("No valid numeric records are available for this chart.")
            return

        grouped = temp.groupby(category)[value].agg(aggregation)
        grouped = grouped.sort_values(ascending=False).head(top_n)
        grouped = grouped.sort_values()

        fig, ax = plt.subplots(figsize=(9, 4))
        grouped.plot(kind="barh", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel or value.replace("_", " ").title())
        ax.set_ylabel(ylabel or category.replace("_", " ").title())

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def show_histogram(frame, column, title, bins=25):
    if column not in frame.columns:
        st.info(f"Chart unavailable: '{column}' is not present.")
        return

    values = pd.to_numeric(frame[column], errors="coerce").dropna()

    if values.empty:
        st.info("No numeric records are available for this distribution.")
        return

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(values, bins=bins, edgecolor="black", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel(column.replace("_", " ").title())
    ax.set_ylabel("Number of records")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def show_monthly_trend(frame, date_column, value_column, title):
    if date_column not in frame.columns:
        st.info(f"Chart unavailable: '{date_column}' is not present.")
        return

    temp = frame.copy()
    temp["_date"] = pd.to_datetime(temp[date_column], errors="coerce")
    temp = temp.dropna(subset=["_date"])

    if temp.empty:
        st.info("No valid dates are available for this trend.")
        return

    temp["_month"] = temp["_date"].dt.to_period("M").astype(str)

    fig, ax = plt.subplots(figsize=(10, 4))

    if value_column and value_column in temp.columns:
        temp[value_column] = pd.to_numeric(
            temp[value_column], errors="coerce"
        )
        trend = temp.groupby("_month")[value_column].sum()
        y_label = value_column.replace("_", " ").title()
    else:
        trend = temp.groupby("_month").size()
        y_label = "Number of records"

    trend.plot(ax=ax, marker="o")
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(y_label)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def show_empty_state():
    st.warning(
        "No records match the current filter selection. "
        "Adjust the sidebar filters to see results."
    )


# ---------------------------------------------------------
# 7. EXECUTIVE KPI CALCULATIONS
# ---------------------------------------------------------
st.header("Executive Overview")

p = filtered["policies"]
c = filtered["claims"]
cu = filtered["customers"]
v = filtered["vehicles"]
pay = filtered["payments"]

total_premium = numeric_column(p, "premium_amount").sum()
total_coverage = numeric_column(p, "coverage_amount").sum()
total_claim_amount = numeric_column(c, "claim_amount").sum()
total_payment_amount = numeric_column(pay, "payment_amount").sum()

policy_status = (
    normalize_text(p["policy_status"])
    if "policy_status" in p.columns
    else pd.Series(dtype="string")
)

claim_status = (
    normalize_text(c["claim_status"])
    if "claim_status" in c.columns
    else pd.Series(dtype="string")
)

payment_status = (
    normalize_text(pay["payment_status"])
    if "payment_status" in pay.columns
    else pd.Series(dtype="string")
)

active_policies = int(policy_status.eq("active").sum())
approved_claims = int(claim_status.eq("approved").sum())
settled_claims = int(claim_status.eq("settled").sum())
rejected_claims = int(claim_status.eq("rejected").sum())
pending_claims = int(claim_status.eq("pending").sum())

approval_rate = safe_divide(approved_claims, len(c)) * 100
rejection_rate = safe_divide(rejected_claims, len(c)) * 100
settlement_rate = safe_divide(settled_claims, len(c)) * 100
claim_to_premium = safe_divide(total_claim_amount, total_premium) * 100
paid_payment_amount = numeric_column(
    pay.loc[payment_status.eq("paid")] if len(pay) else pay,
    "payment_amount",
).sum() if "payment_status" in pay.columns else 0

avg_claim = safe_divide(total_claim_amount, len(c))
avg_premium = safe_divide(total_premium, len(p))

settlement_column = (
    "claim_settlement_days"
    if "claim_settlement_days" in c.columns
    else None
)

avg_settlement_days = (
    average(c[settlement_column])
    if settlement_column
    else (
        average(claim_analysis["claim_settlement_days"])
        if "claim_settlement_days" in claim_analysis.columns
        else 0
    )
)

kpi_rows = [
    [
        ("Customers", number(len(cu))),
        ("Vehicles", number(len(v))),
        ("Policies", number(len(p))),
        ("Active policies", number(active_policies)),
    ],
    [
        ("Total premium", money(total_premium)),
        ("Average premium", money(avg_premium)),
        ("Total coverage", money(total_coverage)),
        ("Average coverage", money(safe_divide(total_coverage, len(p)))),
    ],
    [
        ("Total claims", number(len(c))),
        ("Total claim amount", money(total_claim_amount)),
        ("Average claim amount", money(avg_claim)),
        ("Claim / premium", percent(claim_to_premium)),
    ],
    [
        ("Approved claims", number(approved_claims)),
        ("Rejected claims", number(rejected_claims)),
        ("Pending claims", number(pending_claims)),
        ("Settled claims", number(settled_claims)),
    ],
    [
        ("Approval status share", percent(approval_rate)),
        ("Rejection share", percent(rejection_rate)),
        ("Settlement status share", percent(settlement_rate)),
        ("Avg. settlement days", f"{avg_settlement_days:,.1f} days"),
    ],
    [
        ("Total payments", money(total_payment_amount)),
        ("Paid payment amount", money(paid_payment_amount)),
        ("Payment records", number(len(pay))),
        ("Coverage / premium", f"{safe_divide(total_coverage, total_premium):,.1f}x"),
    ],
]

for row in kpi_rows:
    columns = st.columns(4)
    for column, (label, value) in zip(columns, row):
        column.metric(label, value)

st.caption(
    "Claim/premium is the total recorded claim amount divided by total "
    "recorded premium for the current selection. It is a descriptive ratio, "
    "not a formal actuarial loss ratio."
)

if p.empty or c.empty:
    show_empty_state()


# ---------------------------------------------------------
# 8. POLICY PORTFOLIO
# ---------------------------------------------------------
st.header("1. Policy Portfolio")

tab_status, tab_type, tab_premium = st.tabs(
    ["Policy Status", "Policy Types", "Premium Analysis"]
)

with tab_status:
    left, right = st.columns(2)
    with left:
        show_bar(
            p, "policy_status", None,
            "Policy Count by Status",
        )
    with right:
        show_bar(
            p, "policy_type", None,
            "Policy Count by Type",
        )

with tab_type:
    left, right = st.columns(2)
    with left:
        show_bar(
            p, "policy_type", "premium_amount",
            "Total Premium by Policy Type",
            aggregation="sum",
        )
    with right:
        show_bar(
            p, "policy_type", "premium_amount",
            "Average Premium by Policy Type",
            aggregation="mean",
        )

with tab_premium:
    show_monthly_trend(
        p, "policy_start_date", "premium_amount",
        "Monthly Premium Written by Policy Start Date",
    )
    show_histogram(p, "premium_amount", "Premium Amount Distribution")


# ---------------------------------------------------------
# 9. CLAIM ANALYSIS
# ---------------------------------------------------------
st.header("2. Claims & Damage Analysis")

tab_claim_status, tab_claim_amount, tab_claim_time = st.tabs(
    ["Claim Status", "Claim Amounts", "Claim Timeline"]
)

with tab_claim_status:
    left, right = st.columns(2)
    with left:
        show_bar(c, "claim_status", None, "Claims by Status")
    with right:
        show_bar(c, "claim_type", None, "Claims by Type")

    show_bar(
        c, "damage_severity", None,
        "Claims by Damage Severity",
    )

with tab_claim_amount:
    left, right = st.columns(2)
    with left:
        show_histogram(c, "claim_amount", "Claim Amount Distribution")
    with right:
        show_bar(
            claim_analysis, "vehicle_type", "claim_amount",
            "Total Claim Amount by Vehicle Type",
            aggregation="sum",
        )

    show_bar(
        claim_analysis, "policy_type", "claim_amount",
        "Average Claim Amount by Policy Type",
        aggregation="mean",
    )

    show_bar(
        claim_analysis, "claim_type", "claim_amount",
        "Average Claim Amount by Claim Type",
        aggregation="mean",
    )

with tab_claim_time:
    show_monthly_trend(
        c, "claim_date", "claim_amount",
        "Monthly Recorded Claim Amount",
    )

    show_bar(
        claim_analysis, "claim_status", "claim_settlement_days",
        "Average Settlement Days by Claim Status",
        aggregation="mean",
    )


# ---------------------------------------------------------
# 10. CUSTOMER, VEHICLE, AND GEOGRAPHIC ANALYSIS
# ---------------------------------------------------------
st.header("3. Customer, Vehicle & Geographic Analysis")

tab_customer, tab_vehicle, tab_geo = st.tabs(
    ["Customer Analysis", "Vehicle Analysis", "Geographic Analysis"]
)

with tab_customer:
    left, right = st.columns(2)

    with left:
        show_bar(cu, "occupation", None, "Customers by Occupation")

    with right:
        show_bar(cu, "gender", None, "Customers by Gender")

    show_bar(
        claim_analysis, "age", "claim_amount",
        "Average Claim Amount by Customer Age",
        aggregation="mean",
    )

    show_bar(
        claim_analysis, "state", "claim_amount",
        "Total Claim Amount by State",
        aggregation="sum",
    )

with tab_vehicle:
    left, right = st.columns(2)

    with left:
        show_bar(v, "vehicle_type", None, "Vehicles by Type")

    with right:
        show_bar(v, "fuel_type", None, "Vehicles by Fuel Type")

    show_bar(
        claim_analysis, "vehicle_type", "claim_amount",
        "Average Claim Amount by Vehicle Type",
        aggregation="mean",
    )

    show_bar(
        claim_analysis, "fuel_type", "claim_amount",
        "Total Claim Amount by Fuel Type",
        aggregation="sum",
    )

    show_histogram(v, "vehicle_age", "Vehicle Age Distribution")

with tab_geo:
    left, right = st.columns(2)

    with left:
        show_bar(
            c, "accident_location", None,
            "Claims by Accident Location",
        )

    with right:
        show_bar(
            claim_analysis, "state", "claim_amount",
            "Average Claim Amount by Customer State",
            aggregation="mean",
        )


# ---------------------------------------------------------
# 11. PAYMENT ANALYSIS
# ---------------------------------------------------------
st.header("4. Payment & Settlement Performance")

tab_payment_status, tab_payment_method, tab_settlement = st.tabs(
    ["Payment Status", "Payment Method", "Settlement"]
)

with tab_payment_status:
    left, right = st.columns(2)

    with left:
        show_bar(pay, "payment_status", None, "Payments by Status")

    with right:
        show_bar(
            pay, "payment_status", "payment_amount",
            "Payment Amount by Status",
            aggregation="sum",
        )

with tab_payment_method:
    show_bar(
        pay, "payment_method", "payment_amount",
        "Total Payments by Payment Method",
        aggregation="sum",
    )

    show_bar(
        pay, "payment_method", "payment_amount",
        "Average Payment by Payment Method",
        aggregation="mean",
    )

with tab_settlement:
    show_histogram(
        claim_analysis,
        "claim_settlement_days",
        "Claim Settlement Duration Distribution",
    )

    show_bar(
        claim_analysis, "claim_type", "claim_settlement_days",
        "Average Settlement Days by Claim Type",
        aggregation="mean",
    )


# ---------------------------------------------------------
# 12. EVIDENCE-BASED BUSINESS INSIGHTS
# ---------------------------------------------------------
st.header("5. Business Insights & Recommendations")

def add_insight(title, evidence, meaning, recommendation):
    with st.expander(title):
        st.markdown(f"**Evidence:** {evidence}")
        st.markdown(f"**Business meaning:** {meaning}")
        st.markdown(f"**Recommended action:** {recommendation}")


if not p.empty:
    if "policy_status" in p.columns:
        counts = p["policy_status"].value_counts(dropna=True)
        if not counts.empty:
            status_name = str(counts.index[0])
            status_count = int(counts.iloc[0])
            add_insight(
                f"Most common policy status: {status_name}",
                f"{status_count:,} of {len(p):,} filtered policies have this status.",
                "This describes the status composition of the selected portfolio.",
                "Review the status mix against business targets and investigate "
                "unexpected concentrations.",
            )

    if {"policy_type", "premium_amount"}.issubset(p.columns):
        totals = p.groupby("policy_type")["premium_amount"].sum().dropna()
        if not totals.empty:
            best_type = str(totals.idxmax())
            add_insight(
                f"Highest total premium: {best_type}",
                f"Recorded premium totals {money(totals.max())} for this type.",
                "This policy type contributes the largest recorded premium "
                "amount in the current selection; it does not alone indicate "
                "higher profitability.",
                "Compare policy count, average premium, claims, coverage, and "
                "available exposure before changing pricing or marketing.",
            )

if not c.empty and "claim_status" in c.columns:
    counts = c["claim_status"].value_counts(dropna=True)
    if not counts.empty:
        status_name = str(counts.index[0])
        add_insight(
            f"Most common claim status: {status_name}",
            f"{int(counts.iloc[0]):,} of {len(c):,} filtered claims have this status.",
            "This reflects the recorded claim workflow status mix.",
            "Review pending and rejected claims separately, and verify that "
            "workflow dates are consistent with each status.",
        )

if not claim_analysis.empty and {
    "claim_type", "claim_amount"
}.issubset(claim_analysis.columns):
    amounts = claim_analysis.groupby("claim_type")["claim_amount"].mean().dropna()
    if not amounts.empty:
        claim_type = str(amounts.idxmax())
        add_insight(
            f"Highest average claim amount: {claim_type}",
            f"Average recorded claim amount is {money(amounts.max())}.",
            "This identifies the highest observed average among claim types "
            "in the selected data, not the cause of those claim amounts.",
            "Review claim counts, severity, and individual cases before "
            "considering operational or underwriting changes.",
        )

if len(c) > 0 and len(p) > 0:
    add_insight(
        "Interpret portfolio ratios carefully",
        f"Total claim amount is {money(total_claim_amount)} and total premium "
        f"is {money(total_premium)} in the filtered data.",
        f"The descriptive claim-to-premium ratio is {percent(claim_to_premium)}. "
        "These totals may not represent matched policy exposure periods.",
        "Do not treat this ratio as a formal loss ratio without earned premium, "
        "appropriate exposure periods, and an agreed actuarial definition.",
    )

st.info(
    "Insights are descriptive findings calculated from the selected records. "
    "They do not establish causation or replace actuarial review."
)


# ---------------------------------------------------------
# 13. DATA EXPLORER AND DOWNLOADS
# ---------------------------------------------------------
st.header("6. Data Explorer")

table_names = [
    "customers", "vehicles", "policies", "claims", "payments"
]

selected_table = st.selectbox(
    "Select a dataset",
    table_names,
)

selected_frame = filtered[selected_table]

left, right = st.columns(2)
left.metric("Rows in selected dataset", number(len(selected_frame)))
right.metric("Columns in selected dataset", number(len(selected_frame.columns)))

st.dataframe(
    selected_frame.head(1000),
    use_container_width=True,
    height=420,
)

st.download_button(
    label=f"Download filtered {selected_table} as CSV",
    data=selected_frame.to_csv(index=False).encode("utf-8"),
    file_name=f"{selected_table}_filtered.csv",
    mime="text/csv",
)

with st.expander("View dataset column names"):
    st.write(list(selected_frame.columns))


# ---------------------------------------------------------
# 14. DATA QUALITY AND DEFINITIONS
# ---------------------------------------------------------
st.header("7. Data Quality & KPI Definitions")

st.markdown(
    """
    - **Active policies:** policy records whose recorded status is `Active`.
    - **Approval share:** records whose claim status is exactly `Approved`,
      divided by the filtered claim count. `Settled` is reported separately.
    - **Settlement share:** records whose claim status is exactly `Settled`,
      divided by the filtered claim count.
    - **Total claim amount:** sum of recorded claim amounts. This is not the
      same as the amount actually paid.
    - **Total payment amount:** sum of recorded payment amounts.
    - **Claim-to-premium ratio:** recorded claim amount divided by recorded
      premium. It is descriptive and is not automatically a formal loss ratio.
    - **Missing workflow dates:** missing approval or settlement dates may be
      valid for claims that have not reached those workflow stages.
    - **Reversed policy dates:** policies whose end date precedes their start
      date should be investigated and not silently deleted.
    - **Business insights:** observed relationships are not proof of causation.
    """
)

st.caption(
    "Motor Insurance Claims & Policy Analytics | "
    "Dashboard calculations use the cleaned project datasets."
)