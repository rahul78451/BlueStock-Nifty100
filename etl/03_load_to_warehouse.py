"""
ETL Script 3 — Load to Data Warehouse
=======================================
Loads clean CSV data into the Django-managed database (PostgreSQL or SQLite).
Uses Django ORM for idempotent upserts and data quality checks.

Usage: python etl/03_load_to_warehouse.py
"""
import os
import sys
import django
import pandas as pd
import numpy as np
from pathlib import Path
from decimal import Decimal, InvalidOperation

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from warehouse.models import (
    DimSector, DimCompany, DimYear, DimHealthLabel,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons, Document
)

CLEAN_DIR = Path('data/clean')
DATA_DIR = Path('data')

HEALTH_LABELS = [
    ('EXCELLENT', 80, 100, '#10B981'),
    ('GOOD', 60, 79.99, '#22C55E'),
    ('AVERAGE', 40, 59.99, '#F59E0B'),
    ('WEAK', 20, 39.99, '#F97316'),
    ('POOR', 0, 19.99, '#EF4444'),
]


def safe_decimal(val, default=None):
    """Safely convert a value to Decimal."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    try:
        d = Decimal(str(val))
        if d.is_nan() or d.is_infinite():
            return default
        return d
    except (InvalidOperation, ValueError, OverflowError):
        return default


def safe_str(val, default=''):
    """Safely convert a value to string, handling NaN."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    s = str(val).strip()
    return default if s in ('nan', 'None', 'none', 'NULL', 'Null') else s


def load_health_labels():
    """Load health label dimensions."""
    print("\n🏷️  Loading health labels...")
    for name, mn, mx, color in HEALTH_LABELS:
        DimHealthLabel.objects.update_or_create(
            label_name=name,
            defaults={'min_score': mn, 'max_score': mx, 'color_hex': color}
        )
    print(f"  ✓ {DimHealthLabel.objects.count()} health labels loaded")


def load_sectors():
    """Load sectors from sector_mapping.csv."""
    print("\n📁 Loading sectors...")

    SECTOR_COLORS = {
        'IT': '#6366F1', 'Banking': '#3B82F6', 'NBFC': '#8B5CF6',
        'Insurance': '#06B6D4', 'Energy': '#F59E0B', 'Power': '#EF4444',
        'Pharma': '#10B981', 'Healthcare': '#14B8A6', 'FMCG': '#F97316',
        'Auto': '#EC4899', 'Metals': '#64748B', 'Cement': '#78716C',
        'Telecom': '#A855F7', 'Capital Goods': '#0EA5E9', 'Paints': '#D946EF',
        'Real Estate': '#84CC16', 'Chemicals': '#FBBF24', 'Consumer': '#FB923C',
        'Conglomerate': '#94A3B8', 'Ports': '#2DD4BF', 'Aviation': '#38BDF8',
    }

    mapping_path = DATA_DIR / 'sector_mapping.csv'
    if not mapping_path.exists():
        print("  ⚠️ sector_mapping.csv not found")
        return

    df = pd.read_csv(mapping_path)
    sectors = df['sector'].unique()

    for sector_name in sectors:
        DimSector.objects.update_or_create(
            sector_code=sector_name,
            defaults={
                'sector_name': sector_name,
                'description': f'{sector_name} sector companies',
                'color_hex': SECTOR_COLORS.get(sector_name, '#6366F1'),
            }
        )

    print(f"  ✓ {DimSector.objects.count()} sectors loaded")


def load_years():
    """Load year dimension from all fact tables to discover all year labels."""
    print("\n📅 Loading year dimension...")

    # Collect all unique year labels from fact table CSVs
    year_labels = set()
    for csv_name in ['profitandloss.csv', 'balancesheet.csv', 'cashflow.csv']:
        csv_path = CLEAN_DIR / csv_name
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if 'year' in df.columns:
                year_labels.update(df['year'].dropna().unique())

    # Always include TTM
    year_labels.add('TTM')

    # Sort years: parse to get fiscal year for ordering
    import re
    sorted_labels = []
    for label in year_labels:
        label = str(label).strip()
        if label == 'TTM':
            sorted_labels.append((label, 9999, 0))  # TTM goes last
        else:
            m = re.match(r'(\w{3})\s+(\d{4})', label)
            if m:
                month, yr = m.groups()
                month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                sorted_labels.append((label, int(yr), month_order.get(month.capitalize(), 0)))

    sorted_labels.sort(key=lambda x: (x[1], x[2]))

    for order, (label, fy, _) in enumerate(sorted_labels, start=1):
        is_ttm = label == 'TTM'
        DimYear.objects.update_or_create(
            year_label=label,
            defaults={
                'fiscal_year': None if is_ttm else fy,
                'is_ttm': is_ttm,
                'sort_order': order,
            }
        )

    print(f"  ✓ {DimYear.objects.count()} year periods loaded")
    print(f"    Years: {[lbl for lbl, _, _ in sorted_labels]}")


def load_companies():
    """Load companies from clean data."""
    print("\n🏢 Loading companies...")
    companies_path = CLEAN_DIR / 'companies.csv'
    mapping_path = DATA_DIR / 'sector_mapping.csv'

    # Build sector lookup
    sector_map = {}
    if mapping_path.exists():
        mapping_df = pd.read_csv(mapping_path)
        for _, row in mapping_df.iterrows():
            sector = DimSector.objects.filter(sector_code=row['sector']).first()
            if sector:
                sector_map[row['symbol']] = sector

    if not companies_path.exists():
        print("  ⚠️ companies.csv not found, skipping")
        return

    df = pd.read_csv(companies_path)
    count = 0

    for _, row in df.iterrows():
        # The column is 'company_id' (was renamed from 'id' in extraction)
        symbol = safe_str(row.get('company_id', row.get('id', '')))
        if not symbol:
            continue

        DimCompany.objects.update_or_create(
            symbol=symbol,
            defaults={
                'company_name': safe_str(row.get('company_name', '')),
                'sector': sector_map.get(symbol),
                'face_value': safe_decimal(row.get('face_value')),
                'book_value': safe_decimal(row.get('book_value')),
                'roce_pct': safe_decimal(row.get('roce')),
                'roe_pct': safe_decimal(row.get('roe')),
                'website': safe_str(row.get('website', '')),
                'nse_url': safe_str(row.get('nse_url', '')),
                'bse_url': safe_str(row.get('bse_url', '')),
                'company_logo': safe_str(row.get('company_logo', '')),
                'about_company': safe_str(row.get('about_company', '')),
            }
        )
        count += 1

    print(f"  ✓ {count} companies loaded (total in DB: {DimCompany.objects.count()})")


def load_profit_loss():
    """Load profit & loss fact table."""
    print("\n📈 Loading Profit & Loss...")
    csv_path = CLEAN_DIR / 'profitandloss.csv'
    if not csv_path.exists():
        print("  ⚠️ profitandloss.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        year_label = safe_str(row.get('year', ''))

        company = DimCompany.objects.filter(symbol=symbol).first()
        year = DimYear.objects.filter(year_label=year_label).first()

        if not company or not year:
            skipped += 1
            continue

        FactProfitLoss.objects.update_or_create(
            company=company, year=year,
            defaults={
                'sales': safe_decimal(row.get('sales')),
                'expenses': safe_decimal(row.get('expenses')),
                'operating_profit': safe_decimal(row.get('operating_profit')),
                'opm_pct': safe_decimal(row.get('opm_pct')),
                'other_income': safe_decimal(row.get('other_income')),
                'interest': safe_decimal(row.get('interest')),
                'depreciation': safe_decimal(row.get('depreciation')),
                'profit_before_tax': safe_decimal(row.get('profit_before_tax')),
                'tax_pct': safe_decimal(row.get('tax_pct')),
                'net_profit': safe_decimal(row.get('net_profit')),
                'eps': safe_decimal(row.get('eps')),
                'dividend_payout_pct': safe_decimal(row.get('dividend_payout_pct')),
                'net_profit_margin_pct': safe_decimal(row.get('net_profit_margin_pct')),
                'expense_ratio_pct': safe_decimal(row.get('expense_ratio_pct')),
                'interest_coverage': safe_decimal(row.get('interest_coverage')),
            }
        )
        count += 1

    print(f"  ✓ {count} P&L rows loaded, {skipped} skipped")


def load_balance_sheet():
    """Load balance sheet fact table."""
    print("\n🏦 Loading Balance Sheet...")
    csv_path = CLEAN_DIR / 'balancesheet.csv'
    if not csv_path.exists():
        print("  ⚠️ balancesheet.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        year_label = safe_str(row.get('year', ''))

        company = DimCompany.objects.filter(symbol=symbol).first()
        year = DimYear.objects.filter(year_label=year_label).first()

        if not company or not year:
            skipped += 1
            continue

        FactBalanceSheet.objects.update_or_create(
            company=company, year=year,
            defaults={
                'equity_capital': safe_decimal(row.get('equity_capital')),
                'reserves': safe_decimal(row.get('reserves')),
                'borrowings': safe_decimal(row.get('borrowings')),
                'other_liabilities': safe_decimal(row.get('other_liabilities')),
                'total_liabilities': safe_decimal(row.get('total_liabilities')),
                'fixed_assets': safe_decimal(row.get('fixed_assets')),
                'cwip': safe_decimal(row.get('cwip')),
                'investments': safe_decimal(row.get('investments')),
                'other_assets': safe_decimal(row.get('other_assets')),
                'total_assets': safe_decimal(row.get('total_assets')),
                'debt_to_equity': safe_decimal(row.get('debt_to_equity')),
                'equity_ratio': safe_decimal(row.get('equity_ratio')),
            }
        )
        count += 1

    print(f"  ✓ {count} Balance Sheet rows loaded, {skipped} skipped")


def load_cash_flow():
    """Load cash flow fact table."""
    print("\n💰 Loading Cash Flow...")
    csv_path = CLEAN_DIR / 'cashflow.csv'
    if not csv_path.exists():
        print("  ⚠️ cashflow.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        year_label = safe_str(row.get('year', ''))

        company = DimCompany.objects.filter(symbol=symbol).first()
        year = DimYear.objects.filter(year_label=year_label).first()

        if not company or not year:
            skipped += 1
            continue

        FactCashFlow.objects.update_or_create(
            company=company, year=year,
            defaults={
                'operating_activity': safe_decimal(row.get('operating_activity')),
                'investing_activity': safe_decimal(row.get('investing_activity')),
                'financing_activity': safe_decimal(row.get('financing_activity')),
                'net_cash_flow': safe_decimal(row.get('net_cash_flow')),
                'free_cash_flow': safe_decimal(row.get('free_cash_flow')),
            }
        )
        count += 1

    print(f"  ✓ {count} Cash Flow rows loaded, {skipped} skipped")


def load_analysis():
    """Load growth analysis fact table."""
    print("\n📊 Loading Growth Analysis...")
    csv_path = CLEAN_DIR / 'analysis.csv'
    if not csv_path.exists():
        print("  ⚠️ analysis.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        period = safe_str(row.get('period_label', ''))

        company = DimCompany.objects.filter(symbol=symbol).first()
        if not company or not period:
            skipped += 1
            continue

        FactAnalysis.objects.update_or_create(
            company=company, period_label=period,
            defaults={
                'compounded_sales_growth_pct': safe_decimal(row.get('compounded_sales_growth_pct')),
                'compounded_profit_growth_pct': safe_decimal(row.get('compounded_profit_growth_pct')),
                'stock_price_cagr_pct': safe_decimal(row.get('stock_price_cagr_pct')),
                'roe_pct': safe_decimal(row.get('roe_pct')),
            }
        )
        count += 1

    print(f"  ✓ {count} Analysis rows loaded, {skipped} skipped")


def load_pros_cons():
    """Load pros and cons fact table."""
    print("\n✅❌ Loading Pros & Cons...")
    csv_path = CLEAN_DIR / 'prosandcons.csv'
    if not csv_path.exists():
        print("  ⚠️ prosandcons.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0

    # Clear existing manual entries to avoid duplicates on re-run
    FactProsCons.objects.filter(source='MANUAL').delete()

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        company = DimCompany.objects.filter(symbol=symbol).first()
        if not company:
            continue

        # Each row has a 'pros' column and a 'cons' column
        pros_text = safe_str(row.get('pros', ''))
        cons_text = safe_str(row.get('cons', ''))

        if pros_text:
            FactProsCons.objects.create(
                company=company, is_pro=True,
                text=pros_text, source='MANUAL'
            )
            count += 1

        if cons_text:
            FactProsCons.objects.create(
                company=company, is_pro=False,
                text=cons_text, source='MANUAL'
            )
            count += 1

    print(f"  ✓ {count} Pros/Cons rows loaded")


def load_documents():
    """Load document links."""
    print("\n📄 Loading Documents...")
    csv_path = CLEAN_DIR / 'documents.csv'
    if not csv_path.exists():
        print("  ⚠️ documents.csv not found")
        return

    df = pd.read_csv(csv_path)
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        symbol = safe_str(row.get('company_id', ''))
        year_label = safe_str(row.get('year', ''))
        url = safe_str(row.get('annual_report_url', ''))

        company = DimCompany.objects.filter(symbol=symbol).first()
        year = DimYear.objects.filter(year_label=year_label).first()

        if not company or not year or not url:
            skipped += 1
            continue

        Document.objects.update_or_create(
            company=company, year=year, document_type='Annual Report',
            defaults={'url': url}
        )
        count += 1

    print(f"  ✓ {count} Document links loaded, {skipped} skipped")


def run_quality_checks():
    """Run data quality checks after loading."""
    print("\n🔍 Running data quality checks...")
    checks = [
        ('Companies', DimCompany.objects.count(), '~92'),
        ('Sectors', DimSector.objects.count(), '~15-21'),
        ('Years', DimYear.objects.count(), '~15-20'),
        ('Health Labels', DimHealthLabel.objects.count(), '5'),
        ('P&L rows', FactProfitLoss.objects.count(), '~1276'),
        ('Balance Sheet rows', FactBalanceSheet.objects.count(), '~1312'),
        ('Cash Flow rows', FactCashFlow.objects.count(), '~1187'),
        ('Analysis rows', FactAnalysis.objects.count(), '>0'),
        ('Pros/Cons rows', FactProsCons.objects.count(), '>0'),
        ('Document links', Document.objects.count(), '~1585'),
    ]

    print(f"\n  {'Table':<25} {'Count':>8}   {'Expected':<12}")
    print(f"  {'─'*25} {'─'*8}   {'─'*12}")
    all_ok = True
    for name, count, expected in checks:
        status = "✅" if count > 0 else "❌"
        if count == 0:
            all_ok = False
        print(f"  {status} {name:<23} {count:>8}   ({expected})")

    if all_ok:
        print("\n  🎉 All tables have data!")
    else:
        print("\n  ⚠️ Some tables are empty — check the logs above for errors.")


def main():
    print("🏗️  Loading clean data into warehouse...\n")
    print("=" * 60)

    # Load dimensions first (order matters — FKs depend on these)
    load_health_labels()
    load_sectors()
    load_years()
    load_companies()

    # Load fact tables
    load_profit_loss()
    load_balance_sheet()
    load_cash_flow()
    load_analysis()
    load_pros_cons()
    load_documents()

    # Quality checks
    run_quality_checks()

    print("\n" + "=" * 60)
    print("✅ Warehouse load complete!")


if __name__ == '__main__':
    main()
