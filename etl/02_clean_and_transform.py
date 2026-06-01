"""
ETL Script 2 — Clean and Transform
====================================
Reads raw CSVs from data/raw/, applies cleaning and standardization,
computes derived metrics, and saves to data/clean/.

Usage: python etl/02_clean_and_transform.py
"""
import os
import re
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path('data/raw')
CLEAN_DIR = Path('data/clean')
DATA_DIR = Path('data')

# ── Sector Classification for all 100 companies ──
SECTOR_MAPPING = {
    # IT
    'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT',
    'TECHM': 'IT', 'LTIM': 'IT', 'PERSISTENT': 'IT', 'COFORGE': 'IT', 'NAUKRI': 'IT',
    # Banking
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'AXISBANK': 'Banking',
    'SBIN': 'Banking', 'KOTAKBANK': 'Banking', 'BANKBARODA': 'Banking',
    'INDUSINDBK': 'Banking', 'PNB': 'Banking', 'CANBK': 'Banking', 'UNIONBANK': 'Banking',
    # NBFC
    'BAJFINANCE': 'NBFC', 'BAJAJFINSV': 'NBFC', 'SHRIRAMFIN': 'NBFC',
    'CHOLAFIN': 'NBFC', 'JIOFIN': 'NBFC', 'IRFC': 'NBFC',
    # Insurance
    'SBILIFE': 'Insurance', 'HDFCLIFE': 'Insurance', 'LICI': 'Insurance',
    # Energy
    'RELIANCE': 'Energy', 'ONGC': 'Energy', 'IOC': 'Energy',
    'BPCL': 'Energy', 'GAIL': 'Energy', 'ATGL': 'Energy',
    # Power
    'ADANIGREEN': 'Power', 'ADANIPOWER': 'Power', 'ADANIENSOL': 'Power',
    'NTPC': 'Power', 'POWERGRID': 'Power', 'TATAPOWER': 'Power', 'JSWENERGY': 'Power',
    # Conglomerate / Ports
    'ADANIENT': 'Conglomerate', 'ADANIPORTS': 'Ports',
    # Pharma & Healthcare
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
    'DIVISLAB': 'Pharma', 'MANKIND': 'Pharma', 'TORNTPHARM': 'Pharma',
    'APOLLOHOSP': 'Healthcare', 'MAXHEALTH': 'Healthcare',
    # FMCG
    'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG',
    'BRITANNIA': 'FMCG', 'TATACONSUM': 'FMCG', 'GODREJCP': 'FMCG',
    'COLPAL': 'FMCG', 'MARICO': 'FMCG', 'DABUR': 'FMCG', 'UNITDSPR': 'FMCG',
    # Auto
    'BAJAJ-AUTO': 'Auto', 'TATAMOTORS': 'Auto', 'M&M': 'Auto',
    'MARUTI': 'Auto', 'EICHERMOT': 'Auto', 'HEROMOTOCO': 'Auto',
    'TVSMOTOR': 'Auto', 'BOSCHLTD': 'Auto',
    # Metals
    'TATASTEEL': 'Metals', 'JSWSTEEL': 'Metals', 'HINDALCO': 'Metals',
    'COALINDIA': 'Metals', 'VEDL': 'Metals', 'HINDZINC': 'Metals',
    # Cement
    'ULTRACEMCO': 'Cement', 'AMBUJACEM': 'Cement', 'SHREECEM': 'Cement', 'GRASIM': 'Cement',
    # Telecom
    'BHARTIARTL': 'Telecom',
    # Capital Goods
    'LT': 'Capital Goods', 'SIEMENS': 'Capital Goods', 'ABB': 'Capital Goods',
    'HAL': 'Capital Goods', 'BEL': 'Capital Goods', 'BHARATFORG': 'Capital Goods', 'POLYCAB': 'Capital Goods',
    # Paints
    'ASIANPAINT': 'Paints',
    # Real Estate
    'DLF': 'Real Estate', 'LODHA': 'Real Estate',
    # Chemicals
    'PIDILITIND': 'Chemicals', 'SRF': 'Chemicals',
    # Consumer
    'TITAN': 'Consumer', 'HAVELLS': 'Consumer', 'ZOMATO': 'Consumer',
    'TRENT': 'Consumer', 'DMART': 'Consumer', 'PAGEIND': 'Consumer',
    # Aviation
    'INDIGO': 'Aviation',
}


def standardize_year(year_str: str) -> dict:
    """
    Convert various year formats to a standardized dict.

    Examples:
        'Mar 2024' → {'year_label': 'Mar 2024', 'fiscal_year': 2024, 'is_ttm': False}
        'Mar-24'   → {'year_label': 'Mar 2024', 'fiscal_year': 2024, 'is_ttm': False}
        'Sep 2024' → {'year_label': 'Sep 2024', 'fiscal_year': 2024, 'is_ttm': False}
        'Dec 2012' → {'year_label': 'Dec 2012', 'fiscal_year': 2012, 'is_ttm': False}
        'TTM'      → {'year_label': 'TTM', 'fiscal_year': None, 'is_ttm': True}
    """
    if not year_str or str(year_str).strip() in ('', 'nan', 'None'):
        return {'year_label': '', 'fiscal_year': None, 'is_ttm': False}

    s = str(year_str).strip()

    if s.upper() == 'TTM':
        return {'year_label': 'TTM', 'fiscal_year': None, 'is_ttm': True}

    # Match 'Mar-24' or 'Sep-23' format
    m = re.match(r'(\w{3})-([\d]{2})$', s)
    if m:
        month, yr = m.groups()
        full_year = int(yr) + 2000 if int(yr) < 50 else int(yr) + 1900
        label = f"{month.capitalize()} {full_year}"
        return {'year_label': label, 'fiscal_year': full_year, 'is_ttm': False}

    # Match 'Mar 2024' or 'Dec 2012' format
    m = re.match(r'(\w{3})\s+([\d]{4})$', s)
    if m:
        month, yr = m.groups()
        return {'year_label': f"{month.capitalize()} {yr}", 'fiscal_year': int(yr), 'is_ttm': False}

    # Match plain year '2024'
    m = re.match(r'^(\d{4})$', s)
    if m:
        return {'year_label': f"Mar {m.group(1)}", 'fiscal_year': int(m.group(1)), 'is_ttm': False}

    return {'year_label': s, 'fiscal_year': None, 'is_ttm': False}


def parse_analysis_metric(text: str) -> tuple:
    """
    Parse analysis strings like '10 Years: 21%' or 'TTM: -3%' or '5 Years       24%'

    Returns: (period_label, value_pct) e.g. ('10Y', 21.0)
    """
    if not text or str(text).strip() in ('', 'nan', 'None', 'NULL'):
        return (None, None)

    s = str(text).strip()

    # Handle "10 Years: 21%" or "10 Years:     21%" or "5 Years       24%"
    m = re.match(r'(\d+)\s*Years?[:\s]+\s*([-\d.]+)\s*%?', s, re.IGNORECASE)
    if m:
        years, pct = m.groups()
        period = f"{years}Y"
        return (period, float(pct))

    # Handle "TTM: -3%" or "TTM     5%"
    m = re.match(r'TTM[:\s]+\s*([-\d.]+)\s*%?', s, re.IGNORECASE)
    if m:
        return ('TTM', float(m.group(1)))

    # Handle "Last Year: 52%" or "Last Year     14%"
    m = re.match(r'Last\s*Year[:\s]+\s*([-\d.]+)\s*%?', s, re.IGNORECASE)
    if m:
        return ('1Y', float(m.group(1)))

    return (None, None)


def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert a column to numeric, handling commas and percentage signs."""
    if series.dtype == 'object':
        series = series.str.replace(',', '', regex=False)
        series = series.str.replace('%', '', regex=False)
        series = series.str.strip()
        series = series.replace(['NULL', 'Null', 'null', '', 'None', 'nan'], np.nan)
    return pd.to_numeric(series, errors='coerce')


def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the companies table."""
    if 'company_name' in df.columns:
        df['company_name'] = df['company_name'].str.strip().str.replace(r'[\r\n]+', '', regex=True)
    return df


def clean_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the analysis table from wide format (one row per company with
    embedded 'period: value%' strings) into a long format with proper columns.

    Input columns:  company_id, compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe
    Output columns: company_id, period_label, compounded_sales_growth_pct, compounded_profit_growth_pct,
                    stock_price_cagr_pct, roe_pct
    """
    metric_cols = {
        'compounded_sales_growth': 'compounded_sales_growth_pct',
        'compounded_profit_growth': 'compounded_profit_growth_pct',
        'stock_price_cagr': 'stock_price_cagr_pct',
        'roe': 'roe_pct',
    }

    records = []
    for _, row in df.iterrows():
        company_id = row.get('company_id', '')

        # Each row already has a period embedded in the metric strings
        # All 4 metrics in a single row share the same period
        # Parse the first available metric to get the period
        period = None
        values = {}

        for src_col, dst_col in metric_cols.items():
            if src_col in row.index:
                p, v = parse_analysis_metric(str(row[src_col]))
                if p and period is None:
                    period = p
                values[dst_col] = v

        if period and company_id:
            record = {'company_id': company_id, 'period_label': period}
            record.update(values)
            records.append(record)

    result = pd.DataFrame(records)
    print(f"    → Parsed {len(result)} analysis records from {len(df)} raw rows")
    return result


def compute_profit_loss_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed metrics to the profit & loss data."""
    num_cols = ['sales', 'expenses', 'operating_profit', 'net_profit', 'interest',
                'opm_pct', 'other_income', 'depreciation', 'profit_before_tax',
                'tax_pct', 'eps', 'dividend_payout_pct']
    for col in num_cols:
        if col in df.columns:
            df[col] = clean_numeric(df[col])

    if 'sales' in df.columns and 'net_profit' in df.columns:
        df['net_profit_margin_pct'] = ((df['net_profit'] / df['sales'].replace(0, np.nan)) * 100).round(2)
    if 'sales' in df.columns and 'expenses' in df.columns:
        df['expense_ratio_pct'] = ((df['expenses'] / df['sales'].replace(0, np.nan)) * 100).round(2)
    if 'operating_profit' in df.columns and 'interest' in df.columns:
        df['interest_coverage'] = (df['operating_profit'] / df['interest'].replace(0, np.nan)).round(2)

    return df


def compute_balance_sheet_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed metrics to balance sheet data."""
    num_cols = ['equity_capital', 'reserves', 'borrowings', 'other_liabilities',
                'total_liabilities', 'fixed_assets', 'cwip', 'investments',
                'other_assets', 'total_assets']
    for col in num_cols:
        if col in df.columns:
            df[col] = clean_numeric(df[col])

    if 'borrowings' in df.columns:
        equity_total = (df.get('equity_capital', 0).fillna(0) + df.get('reserves', 0).fillna(0))
        equity_total = equity_total.replace(0, np.nan)
        df['debt_to_equity'] = (df['borrowings'] / equity_total).round(4)

    if 'equity_capital' in df.columns and 'total_assets' in df.columns:
        equity_total = (df.get('equity_capital', 0).fillna(0) + df.get('reserves', 0).fillna(0))
        df['equity_ratio'] = (equity_total / df['total_assets'].replace(0, np.nan)).round(4)

    return df


def compute_cashflow_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add free cash flow to cash flow data."""
    for col in ['operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow']:
        if col in df.columns:
            df[col] = clean_numeric(df[col])

    if 'operating_activity' in df.columns and 'investing_activity' in df.columns:
        df['free_cash_flow'] = (df['operating_activity'] + df['investing_activity']).round(2)

    return df


def main():
    """Main ETL cleaning pipeline."""
    print("🧹 Starting data cleaning and transformation...\n")

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # Save sector mapping
    sector_df = pd.DataFrame([
        {'symbol': sym, 'sector': sec} for sym, sec in SECTOR_MAPPING.items()
    ])
    sector_path = DATA_DIR / 'sector_mapping.csv'
    sector_df.to_csv(sector_path, index=False)
    print(f"  ✓ Sector mapping: {len(sector_df)} companies → {sector_path}")

    # Process each table if raw CSVs exist
    tables = ['companies', 'balancesheet', 'profitandloss', 'cashflow', 'analysis', 'prosandcons', 'documents']

    for table in tables:
        raw_path = RAW_DIR / f'{table}.csv'
        if not raw_path.exists():
            print(f"  ⚠️ {raw_path} not found, skipping")
            continue

        df = pd.read_csv(raw_path)
        print(f"\n📊 Processing {table}: {len(df)} rows, {len(df.columns)} columns")

        # Replace NULL strings
        df = df.replace(['NULL', 'Null', 'null', 'None', 'none', '', 'nan'], np.nan)

        # Table-specific transformations
        if table == 'companies':
            df = clean_companies(df)
        elif table == 'profitandloss':
            df = compute_profit_loss_metrics(df)
        elif table == 'balancesheet':
            df = compute_balance_sheet_metrics(df)
        elif table == 'cashflow':
            df = compute_cashflow_metrics(df)
        elif table == 'analysis':
            df = clean_analysis(df)

        # Year standardization for tables with year columns
        if table != 'analysis':  # analysis is already transformed
            year_cols = [c for c in df.columns if c.lower() == 'year']
            for ycol in year_cols:
                df[ycol] = df[ycol].apply(
                    lambda x: standardize_year(str(x))['year_label'] if pd.notna(x) else x
                )

        # Save clean version
        clean_path = CLEAN_DIR / f'{table}.csv'
        df.to_csv(clean_path, index=False)
        print(f"  ✓ Saved {clean_path}: {len(df)} rows, {len(df.columns)} cols")

    print("\n✅ Cleaning complete!")


if __name__ == '__main__':
    main()
