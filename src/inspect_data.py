from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"


def main():
    claims = pd.read_csv(RAW_DIR / "claims.csv")
    policies = pd.read_csv(RAW_DIR / "policies.csv")

    print("\n========== CLAIM STATUS COUNTS ==========")
    print(claims["claim_status"].value_counts(dropna=False).to_string())

    print("\n========== MISSING DATES BY CLAIM STATUS ==========")
    print(
        claims.groupby("claim_status", dropna=False)
        .agg(
            total_claims=("claim_id", "size"),
            missing_approval_date=("approval_date", lambda s: s.isna().sum()),
            missing_settlement_date=("settlement_date", lambda s: s.isna().sum()),
        )
        .to_string()
    )

    print("\n========== POLICY DATE PROBLEMS ==========")
    policies["policy_start_date"] = pd.to_datetime(
        policies["policy_start_date"], errors="coerce"
    )
    policies["policy_end_date"] = pd.to_datetime(
        policies["policy_end_date"], errors="coerce"
    )

    invalid = policies[
        policies["policy_start_date"].notna()
        & policies["policy_end_date"].notna()
        & (policies["policy_end_date"] < policies["policy_start_date"])
    ]

    print(f"Invalid policy date rows: {len(invalid)}")
    print(
        invalid[
            ["policy_id", "policy_start_date", "policy_end_date", "policy_status"]
        ].head(15).to_string(index=False)
    )


if __name__ == "__main__":
    main()