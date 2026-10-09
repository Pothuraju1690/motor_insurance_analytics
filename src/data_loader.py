
from pathlib import Path

import pandas as pd

TABLES = ["customers", "vehicles", "policies", "claims", "payments"]


def check_file_exists(file_path):
    """Raise a clear error when a required data file does not exist."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Required data file not found: {path}")
    return True


def load_table(file_path):
    """Load one CSV after verifying that the file exists."""
    check_file_exists(file_path)
    return pd.read_csv(file_path)


def load_all_data(data_dir):
    """Load all five datasets from a directory into a dictionary of DataFrames."""
    data_dir = Path(data_dir)
    data = {}

    for name in TABLES:
        cleaned_path = data_dir / f"{name}_cleaned.csv"
        standard_path = data_dir / f"{name}.csv"

        path = cleaned_path if cleaned_path.exists() else standard_path
        check_file_exists(path)
        data[name] = load_table(path)

    return data