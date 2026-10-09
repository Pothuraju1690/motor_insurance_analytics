@echo off
setlocal
title Motor Insurance Analytics - Project Setup

pushd "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not open the folder containing this batch file.
    pause
    exit /b 1
)

set "PROJECT=motor_insurance_analytics"

if not exist "%PROJECT%\" mkdir "%PROJECT%"
pushd "%PROJECT%"
if errorlevel 1 (
    echo ERROR: Could not create or open the project folder.
    popd
    pause
    exit /b 1
)

echo Creating project folders...

for %%D in (
    "data\raw"
    "data\cleaned"
    "notebooks"
    "src"
    "app"
    "reports"
    "tests"
    "logs"
) do (
    if not exist "%%~D\" mkdir "%%~D"
)

echo Creating project files...

if not exist "src\__init__.py" type nul > "src\__init__.py"

for %%F in (
    "src\data_loader.py"
    "src\validation.py"
    "src\data_cleaner.py"
    "src\insurance_analysis.py"
    "src\visualization.py"
    "src\insights.py"
    "src\logger.py"
    "app\streamlit_app.py"
    "reports\business_report.md"
    "tests\test_pipeline.py"
    "tests\test_analysis.py"
    "tests\test_validation.py"
    "run_pipeline.py"
    "requirements.txt"
    "Dockerfile"
    ".dockerignore"
    ".gitignore"
    "README.md"
    "logs\pipeline.log"
    "customers_cleaned.csv"
    "policies_cleaned.csv"
    "vehicles_cleaned.csv"
    "claims_cleaned.csv"
    "payments_cleaned.csv"
) do (
    if not exist "%%~F" type nul > "%%~F"
)

if not exist "notebooks\insurance_analysis.ipynb" (
    type nul > "notebooks\insurance_analysis.ipynb"
)

echo Copying raw CSV files, if they are beside flow.bat...

for %%F in (
    customers.csv
    policies.csv
    vehicles.csv
    claims.csv
    payments.csv
) do (
    if exist "%~dp0%%F" (
        if not exist "data\raw\%%F" (
            copy /Y "%~dp0%%F" "data\raw\%%F" >nul
            if errorlevel 1 (
                echo ERROR: Could not copy %%F
            ) else (
                echo COPIED: %%F
            )
        ) else (
            echo EXISTS: data\raw\%%F - preserved
        )
    ) else (
        echo MISSING: %%F - copy it into data\raw manually
    )
)

echo.
echo Project structure created at:
cd
echo.
echo Note: The cleaned CSVs and Python files are empty placeholders.
echo The notebook placeholder must be populated with valid notebook content.
echo.

popd
popd
pause
endlocal