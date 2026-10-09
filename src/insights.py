
"""Evidence-based business insights for motor insurance analytics."""

import numpy as np
import pandas as pd


def _table(data, name):
    return data.get(name, pd.DataFrame()).copy()


def _insight(pattern, evidence, meaning, recommendation):
    return {
        "pattern": str(pattern),
        "evidence": str(evidence),
        "business_meaning": str(meaning),
        "recommendation": str(recommendation),
    }


def _numeric(df, column):
    if column in df:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _claims_with_policy(data):
    claims = _table(data, "claims")
    policies = _table(data, "policies")

    if claims.empty or policies.empty:
        return pd.DataFrame()

    if not {"policy_id"}.issubset(claims.columns) or not {
        "policy_id"
    }.issubset(policies.columns):
        return pd.DataFrame()

    policy_columns = [
        col for col in [
            "policy_id", "policy_type", "premium_amount",
            "coverage_amount", "vehicle_id"
        ] if col in policies.columns
    ]

    return claims.merge(
        policies[policy_columns].drop_duplicates("policy_id"),
        on="policy_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_policy"),
    )


def generate_portfolio_insights(data):
    """Generate insights about policy volume and status."""
    policies = _table(data, "policies")
    results = []

    if policies.empty or "policy_status" not in policies:
        return results

    total = len(policies)
    counts = policies["policy_status"].fillna("Unknown").value_counts()

    if total:
        top_status = counts.index[0]
        share = counts.iloc[0] / total * 100
        results.append(_insight(
            f"{top_status} is the most frequent policy status.",
            f"{counts.iloc[0]:,} of {total:,} policies ({share:.2f}%).",
            "The status mix describes the current composition of the policy portfolio.",
            "Review status definitions and compare the portfolio mix with business targets.",
        ))

    if "policy_type" in policies:
        type_counts = policies["policy_type"].fillna("Unknown").value_counts()
        if not type_counts.empty:
            results.append(_insight(
                f"{type_counts.index[0]} has the highest policy count.",
                f"{type_counts.iloc[0]:,} policies.",
                "Policy volume is concentrated in this product category.",
                "Review service capacity and performance by policy type before changing product strategy.",
            ))

    return results


def generate_claim_insights(data):
    """Generate insights about claim volume, status, and severity."""
    claims = _table(data, "claims")
    results = []

    if claims.empty:
        return results

    if "claim_status" in claims:
        counts = claims["claim_status"].fillna("Unknown").value_counts()
        total = len(claims)

        if total and not counts.empty:
            status = counts.index[0]
            results.append(_insight(
                f"{status} is the most common recorded claim status.",
                f"{counts.iloc[0]:,} of {total:,} claims ({counts.iloc[0] / total * 100:.2f}%).",
                "The distribution indicates where claims are concentrated in the recorded workflow.",
                "Review workflow definitions and investigate any status category that exceeds operational expectations.",
            ))

    if {"claim_type", "claim_amount"}.issubset(claims.columns):
        claims = _numeric(claims, "claim_amount")
        grouped = claims.groupby("claim_type")["claim_amount"].agg(
            ["mean", "count"]
        ).dropna()

        if not grouped.empty:
            top = grouped["mean"].idxmax()
            results.append(_insight(
                f"{top} has the highest average claim amount among claim types.",
                f"Average claim amount: {grouped.loc[top, 'mean']:,.2f}; records: {int(grouped.loc[top, 'count']):,}.",
                "This category may deserve closer review of claim severity and handling costs.",
                "Inspect sample claims and compare severity, exposure, and claim counts before drawing conclusions.",
            ))

    if "damage_severity" in claims:
        severity = claims["damage_severity"].fillna("Unknown").value_counts()
        if not severity.empty:
            results.append(_insight(
                f"{severity.index[0]} is the most frequently recorded damage severity.",
                f"{severity.iloc[0]:,} claims.",
                "This shows the most common recorded severity category, not necessarily the most expensive one.",
                "Compare severity categories with claim amounts and settlement times.",
            ))

    return results


def generate_premium_insights(data):
    """Generate insights about premiums and claim-to-premium ratios."""
    policies = _table(data, "policies")
    claims = _table(data, "claims")
    results = []

    if policies.empty or "premium_amount" not in policies:
        return results

    policies = _numeric(policies, "premium_amount")
    valid_premiums = policies["premium_amount"].dropna()

    if not valid_premiums.empty:
        results.append(_insight(
            "Premium values vary across the policy portfolio.",
            f"Mean premium: {valid_premiums.mean():,.2f}; median premium: {valid_premiums.median():,.2f}.",
            "A gap between mean and median can indicate a skewed premium distribution.",
            "Review the premium distribution and compare pricing across policy types and coverage levels.",
        ))

    if (
        not claims.empty
        and {"policy_id", "claim_amount"}.issubset(claims.columns)
        and "policy_id" in policies
    ):
        claims = _numeric(claims, "claim_amount")
        claim_totals = claims.groupby("policy_id")["claim_amount"].sum()
        policy_totals = policies.groupby("policy_id").agg(
            premium=("premium_amount", "sum"),
            policy_type=("policy_type", "first") if "policy_type" in policies else
            ("policy_id", "first"),
        )
        grouped = pd.DataFrame({
            "claims": claim_totals,
            "premium": policy_totals["premium"],
        }).join(policy_totals[["policy_type"]] if "policy_type" in policy_totals else pd.DataFrame())

        if "policy_type" in grouped:
            by_type = grouped.groupby("policy_type").agg(
                claims=("claims", "sum"),
                premium=("premium", "sum"),
            )
            by_type = by_type[by_type["premium"] > 0]
            if not by_type.empty:
                by_type["ratio"] = by_type["claims"] / by_type["premium"]
                top = by_type["ratio"].idxmax()
                results.append(_insight(
                    f"{top} has the highest observed claim-amount-to-premium ratio.",
                    f"Ratio of summed claim amounts to summed premiums: {by_type.loc[top, 'ratio']:.3f}.",
                    "This descriptive comparison may indicate a category requiring further portfolio analysis; it is not automatically a formal loss ratio.",
                    "Validate exposure periods, policy mix, claim maturity, and payment definitions before considering pricing or underwriting changes.",
                ))

    return results


def generate_customer_insights(data):
    """Generate insights about customer age and claim behavior."""
    customers = _table(data, "customers")
    claims = _table(data, "claims")
    results = []

    age_col = "customer_age" if "customer_age" in customers else "age"

    if customers.empty or age_col not in customers or claims.empty:
        return results

    if "customer_id" not in customers or "customer_id" not in claims:
        return results

    customer_subset = customers[["customer_id", age_col]].drop_duplicates("customer_id")
    customer_subset[age_col] = pd.to_numeric(customer_subset[age_col], errors="coerce")
    customer_subset["age_group"] = pd.cut(
        customer_subset[age_col],
        bins=[0, 25, 35, 45, 55, 65, 120],
        labels=["18–25", "26–35", "36–45", "46–55", "56–65", "66+"],
        include_lowest=True,
    )

    claim_counts = claims.groupby("customer_id").size().rename("claim_count")
    activity = customer_subset.merge(
        claim_counts, on="customer_id", how="left"
    )
    activity["claim_count"] = activity["claim_count"].fillna(0)

    grouped = activity.groupby("age_group", observed=True)["claim_count"].mean().dropna()

    if not grouped.empty:
        group = grouped.idxmax()
        results.append(_insight(
            f"Customers in age group {group} have the highest average recorded claim count per customer.",
            f"Average claims per customer: {grouped.loc[group]:.3f}.",
            "This is a descriptive segmentation result and does not establish that age causes claim activity.",
            "Compare group sizes and policy exposure before using age segments for business decisions.",
        ))

    return results


def generate_vehicle_insights(data):
    """Generate insights about vehicle groups and claims."""
    claims = _claims_with_policy(data)
    vehicles = _table(data, "vehicles")
    results = []

    if claims.empty or vehicles.empty or "vehicle_id" not in claims:
        return results

    vehicle_cols = [
        c for c in ["vehicle_id", "vehicle_type", "vehicle_make",
                    "vehicle_year", "fuel_type"]
        if c in vehicles.columns
    ]
    if len(vehicle_cols) < 2:
        return results

    df = claims.merge(
        vehicles[vehicle_cols].drop_duplicates("vehicle_id"),
        on="vehicle_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_vehicle"),
    )

    if {"vehicle_type", "claim_amount"}.issubset(df.columns):
        df = _numeric(df, "claim_amount")
        grouped = df.groupby("vehicle_type")["claim_amount"].agg(["mean", "count"]).dropna()
        if not grouped.empty:
            kind = grouped["mean"].idxmax()
            results.append(_insight(
                f"{kind} has the highest average claim amount among vehicle types represented in the claims data.",
                f"Average claim amount: {grouped.loc[kind, 'mean']:,.2f}; claims: {int(grouped.loc[kind, 'count']):,}.",
                "Average claim severity can differ from total claim volume and should be assessed alongside exposure.",
                "Compare claim frequency, sample sizes, vehicle values, and damage severity before assigning a risk label.",
            ))

    if "fuel_type" in df and "claim_id" in df:
        fuel_counts = df.groupby("fuel_type")["claim_id"].count().dropna()
        if not fuel_counts.empty:
            fuel = fuel_counts.idxmax()
            results.append(_insight(
                f"{fuel} vehicles have the largest recorded claim count in the joined claims data.",
                f"{int(fuel_counts.loc[fuel]):,} claims.",
                "Raw counts can reflect how common a fuel type is in the insured portfolio, not only its risk.",
                "Compare claim counts with the number of insured vehicles by fuel type before comparing risk.",
            ))

    return results


def generate_risk_patterns(data):
    """Identify descriptive groups that warrant further risk investigation."""
    results = []
    results.extend(generate_premium_insights(data))
    results.extend(generate_vehicle_insights(data))
    results.extend(generate_claim_insights(data))
    return results


def generate_business_recommendations(data):
    """Return recommendations tied to calculated patterns and evidence."""
    results = []
    results.extend(generate_portfolio_insights(data))
    results.extend(generate_customer_insights(data))
    results.extend(generate_risk_patterns(data))

    # Keep output concise and remove identical pattern statements.
    unique = []
    seen = set()
    for item in results:
        if item["pattern"] not in seen:
            seen.add(item["pattern"])
            unique.append(item)

    return unique