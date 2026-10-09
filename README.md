# Motor Insurance Claims & Policy Analytics

An end-to-end Python analytics project for preparing, validating, analyzing, and visualizing motor insurance policy and claims data.

## Project Overview

This project brings five related datasets together to investigate the insurance portfolio, premiums, claims, settlements, customers, vehicles, and payments. It includes a reusable data-cleaning pipeline, validation checks, statistical analysis, visualizations, automated tests, a Jupyter notebook, and an interactive Streamlit dashboard.

## Key Features

* Load and validate five related CSV datasets.
* Check primary-key uniqueness and foreign-key relationships.
* Clean text and date columns while preserving values that cannot safely be inferred.
* Create derived columns for policy duration, customer age, vehicle age, claim processing time, settlement time, and financial ratios where the required source data is available.
* Calculate policy, premium, claim, and payment KPIs.
* Generate statistical summaries and charts.
* Produce evidence-based observations and business recommendations.
* Explore results using interactive dashboard filters.
* Preview and download filtered data.
* Run automated tests and launch the project in Docker.

## Technology Stack

* Python
* pandas and NumPy
* Matplotlib and Seaborn
* Streamlit
* Jupyter Notebook
* pytest
* Docker

## Project Structure

```text
motor_insurance_analytics/
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/
│   └── cleaned/
├── logs/
├── notebooks/
│   └── insurance_analysis.ipynb
├── reports/
│   ├── charts/
│   └── business_report.md
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── validation.py
│   ├── data_cleaner.py
│   ├── insurance_analysis.py
│   ├── visualization.py
│   ├── insights.py
│   └── logger.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_analysis.py
│   ├── test_validation.py
│   └── test_dashboard.py
├── create_notebook.py
├── run_pipeline.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

The exact files in your local project may differ as development continues. Check the directory before submission and remove or document any discrepancy.

## Dataset Relationships

The project uses the following logical relationships:

* `vehicles.customer_id` references `customers.customer_id`.
* `policies.customer_id` references `customers.customer_id`.
* `policies.vehicle_id` references `vehicles.vehicle_id`.
* `claims.policy_id` references `policies.policy_id`.
* `claims.customer_id` references `customers.customer_id`.
* `payments.claim_id` references `claims.claim_id`.
* `payments.policy_id` references `policies.policy_id`.

## Setup on Windows

### 1. Install Python

Install a compatible Python version and confirm that Python and pip are available:

```bat
python --version
python -m pip --version
```

### 2. Open the project folder

Open Command Prompt or the VS Code terminal at the project root.

### 3. Create a virtual environment

```bat
python -m venv .venv
```

Activate it in Command Prompt:

```bat
.venv\Scripts\activate.bat
```

In PowerShell, use:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Place the raw data

Place the five source files in `data/raw/`:

* `customers.csv`
* `vehicles.csv`
* `policies.csv`
* `claims.csv`
* `payments.csv`

Do not overwrite the raw files with cleaned data.

## Running the Project

Run commands from the project root.

### Step 1: Run the data pipeline

```bat
python run_pipeline.py
```

This loads the raw datasets, validates their relationships, cleans the data, generates derived columns, and writes the cleaned CSV files.

### Step 2: Run validation

```bat
python -m src.validation
```

Review any warnings or failures before proceeding.

### Step 3: Generate analytical outputs

```bat
python -m src.insurance_analysis
```

### Step 4: Generate charts and statistical outputs

```bat
python -m src.visualization
```

### Step 5: Open the notebook

```bat
python -m notebook
```

Open `notebooks/insurance_analysis.ipynb` and run all cells from top to bottom.

### Step 6: Launch the Streamlit dashboard

```bat
python -m streamlit run app/streamlit_app.py
```

Open the local address printed by Streamlit in the terminal.

### Step 7: Run automated tests

```bat
python -m pytest -v
```

## Dashboard Features

The dashboard presents portfolio KPIs, policy information, claim analysis, customer and vehicle analysis, settlement and payment information, and interactive filters.

The supplied vehicle dataset currently contains only the `Car` category. Comparisons among different vehicle types are therefore not supported by the current data.

## Data Interpretation Notes

* Missing approval and settlement dates are not automatically invented.
* Policy date anomalies are preserved and flagged for investigation.
* Claim amounts and payment amounts are different measures.
* Approved and Settled are separate recorded claim statuses.
* Claim amount divided by recorded premium is a descriptive ratio, not necessarily a formal loss ratio. A formal loss ratio requires appropriate earned-premium and exposure definitions.
* Observed associations do not establish causation.

## Testing

The automated tests cover data loading, primary keys, relationships, pipeline behavior, validation, KPI calculations, and selected dashboard interactions.

A passing test suite demonstrates that the tested conditions passed; it does not replace a full manual review of the dashboard, report, and deployment environment.

## Docker

Build the image:

```bat
docker build -t motor-insurance-analytics .
```

Run the dashboard:

```bat
docker run --rm -p 8501:8501 motor-insurance-analytics
```

Open `http://localhost:8501` in a browser.

The Docker build requires the source files, dependencies, and datasets to be included or mounted as appropriate. See the Docker section of this README and the `.dockerignore` file.

## Business Report

See `reports/business_report.md` for the executive summary, descriptive findings, data-quality observations, recommendations, and limitations.

## Responsible Use

This project is an analytical portfolio project. Its findings should not be treated as official underwriting decisions, pricing recommendations, or actuarial conclusions without further validation and appropriate business context.
