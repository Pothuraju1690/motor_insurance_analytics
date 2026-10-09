
from pathlib import Path

from src.data_loader import load_all_data
from src.data_cleaner import clean_data, save_cleaned_data
from src.logger import setup_logger

ROOT_DIR = Path(__file__).resolve().parent
RAW_DIR = ROOT_DIR / "data" / "raw"


def validate_pipeline_inputs(data):
    """Check primary keys and required foreign-key relationships before cleaning."""
    primary_keys = {
        "customers": "customer_id",
        "vehicles": "vehicle_id",
        "policies": "policy_id",
        "claims": "claim_id",
        "payments": "payment_id",
    }

    for table, key in primary_keys.items():
        df = data[table]
        if key not in df.columns:
            raise ValueError(f"{table}: required primary key '{key}' is missing")
        if df[key].isna().any():
            raise ValueError(f"{table}: missing values found in primary key '{key}'")
        if df[key].duplicated().any():
            raise ValueError(f"{table}: duplicate values found in primary key '{key}'")

    relationships = [
        ("vehicles", "customer_id", "customers", "customer_id"),
        ("policies", "customer_id", "customers", "customer_id"),
        ("policies", "vehicle_id", "vehicles", "vehicle_id"),
        ("claims", "policy_id", "policies", "policy_id"),
        ("claims", "customer_id", "customers", "customer_id"),
        ("payments", "claim_id", "claims", "claim_id"),
        ("payments", "policy_id", "policies", "policy_id"),
    ]

    for child_table, child_key, parent_table, parent_key in relationships:
        child_values = data[child_table][child_key].dropna()
        parent_values = set(data[parent_table][parent_key].dropna())
        invalid = ~child_values.isin(parent_values)

        if invalid.any():
            raise ValueError(
                f"{child_table}.{child_key}: {int(invalid.sum())} "
                f"foreign-key values do not exist in {parent_table}.{parent_key}"
            )


def run_pipeline():
    """Run input validation, cleaning, derived-column creation, and file output."""
    logger = setup_logger()
    logger.info("========== PIPELINE STARTED ==========")

    try:
        data = load_all_data(RAW_DIR)
        logger.info("Loaded all five raw datasets")

        validate_pipeline_inputs(data)
        logger.info("Primary keys and foreign-key relationships passed")

        cleaned = clean_data(data)
        logger.info("Cleaning and derived-column creation completed")

        output_dir = save_cleaned_data(cleaned)
        logger.info("Cleaned files saved to %s", output_dir)
        logger.info("========== PIPELINE COMPLETED ==========")

    except Exception:
        logger.exception("Pipeline failed")
        raise


if __name__ == "__main__":
    run_pipeline()