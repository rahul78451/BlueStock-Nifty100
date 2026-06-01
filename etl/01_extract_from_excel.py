"""
ETL Script 1 — Extract from Excel Files
==========================================
Reads 7 Excel (.xlsx) files from data/source/ and exports them as
clean CSV files into data/raw/ for downstream processing.

Source files (from Google Drive):
  analysis.xlsx, balancesheet.xlsx, cashflow.xlsx, companies.xlsx,
  documents.xlsx, profitandloss.xlsx, prosandcons.xlsx

Usage: python etl/01_extract_from_excel.py
"""
import os
import sys
import pandas as pd
from pathlib import Path

SOURCE_DIR = Path('data/source')
RAW_DIR = Path('data/raw')

# Map of Excel filenames → output CSV name and the header row index
# Row 0 = title row ("Bluestock Fintech — Nifty 100 | …"), Row 1 = column headers
FILE_MAP = {
    'companies.xlsx':      {'csv': 'companies.csv',      'header': 1},
    'analysis.xlsx':       {'csv': 'analysis.csv',        'header': 1},
    'balancesheet.xlsx':   {'csv': 'balancesheet.csv',    'header': 1},
    'profitandloss.xlsx':  {'csv': 'profitandloss.csv',   'header': 1},
    'cashflow.xlsx':       {'csv': 'cashflow.csv',        'header': 1},
    'prosandcons.xlsx':    {'csv': 'prosandcons.csv',      'header': 1},
    'documents.xlsx':      {'csv': 'documents.csv',        'header': 1},
}

# Column renames to standardize across all files
COLUMN_RENAMES = {
    # companies.xlsx
    'roce_percentage': 'roce',
    'roe_percentage': 'roe',
    'nse_profile': 'nse_url',
    'bse_profile': 'bse_url',

    # profitandloss.xlsx
    'opm_percentage': 'opm_pct',
    'tax_percentage': 'tax_pct',
    'dividend_payout': 'dividend_payout_pct',

    # balancesheet.xlsx
    'other_asset': 'other_assets',

    # documents.xlsx
    'Annual_Report': 'annual_report_url',
    'Year': 'year',
}


def extract_all():
    """Read all Excel files and save as cleaned CSVs."""
    print("📥 Starting Excel extraction...\n")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    extracted = 0

    for xlsx_name, config in FILE_MAP.items():
        xlsx_path = SOURCE_DIR / xlsx_name
        if not xlsx_path.exists():
            print(f"  ⚠️  {xlsx_name} not found in {SOURCE_DIR}, skipping")
            continue

        try:
            # Read Excel — header row is at index 1 (row 0 is the title)
            df = pd.read_excel(
                xlsx_path,
                header=config['header'],
                engine='openpyxl'
            )

            # Drop completely empty rows
            df = df.dropna(how='all')

            # Rename columns for consistency
            df = df.rename(columns=COLUMN_RENAMES)

            # Clean string columns
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'None', 'none', 'NaN'], '')

            # For companies.xlsx, the 'id' column IS the symbol (company_id)
            if xlsx_name == 'companies.xlsx':
                if 'id' in df.columns and 'company_id' not in df.columns:
                    df = df.rename(columns={'id': 'company_id'})

            # Save as CSV
            csv_path = RAW_DIR / config['csv']
            df.to_csv(csv_path, index=False)

            rows = len(df)
            total_rows += rows
            extracted += 1
            print(f"  ✅ {xlsx_name:25s} → {config['csv']:25s} | {rows:>5} rows | {len(df.columns)} cols")
            print(f"     Columns: {list(df.columns)}")

        except Exception as e:
            print(f"  ❌ Error reading {xlsx_name}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Extraction complete: {extracted}/{len(FILE_MAP)} files, {total_rows:,} total rows")
    print(f"   Output directory: {RAW_DIR.resolve()}")


if __name__ == '__main__':
    extract_all()
