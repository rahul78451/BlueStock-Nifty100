"""
Seed Data Command — Populates the data warehouse with realistic Nifty 100 data.
================================================================================
Generates dimensional and fact data for all 100 companies across ~12 years.
Usage: python manage.py seed_data
"""
import random
import math
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from warehouse.models import (
    DimSector, DimCompany, DimYear, DimHealthLabel,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons,
)

# ── All 100 Nifty companies with sector assignments ──
COMPANIES = [
    # IT
    ('TCS', 'Tata Consultancy Services', 'IT', 1420000, 47.5, 51.2, "India's largest IT services company"),
    ('INFY', 'Infosys', 'IT', 720000, 38.9, 33.4, "Global leader in consulting and digital services"),
    ('WIPRO', 'Wipro', 'IT', 260000, 18.2, 16.8, "Leading global IT consulting company"),
    ('HCLTECH', 'HCL Technologies', 'IT', 380000, 30.1, 24.5, "Diversified technology company"),
    ('TECHM', 'Tech Mahindra', 'IT', 145000, 18.5, 15.2, "Specialist in digital transformation"),
    ('LTIM', 'LTIMindtree', 'IT', 170000, 32.8, 28.4, "Global technology consulting company"),
    # Banking
    ('HDFCBANK', 'HDFC Bank', 'Banking', 1280000, 19.2, 17.5, "India's largest private sector bank"),
    ('ICICIBANK', 'ICICI Bank', 'Banking', 850000, 16.8, 18.3, "Leading private sector bank"),
    ('AXISBANK', 'Axis Bank', 'Banking', 380000, 14.2, 17.6, "Third largest private sector bank"),
    ('SBIN', 'State Bank of India', 'Banking', 720000, 12.5, 20.3, "India's largest public sector bank"),
    ('KOTAKBANK', 'Kotak Mahindra Bank', 'Banking', 410000, 21.3, 14.8, "Premium private sector bank"),
    ('BANKBARODA', 'Bank of Baroda', 'Banking', 145000, 10.8, 18.1, "Major public sector bank"),
    ('INDUSINDBK', 'IndusInd Bank', 'Banking', 105000, 15.6, 15.2, "New generation private sector bank"),
    ('PNB', 'Punjab National Bank', 'Banking', 115000, 8.2, 12.3, "Oldest nationalised bank"),
    # NBFC / Finance
    ('BAJFINANCE', 'Bajaj Finance', 'NBFC', 480000, 22.5, 24.1, "India's largest NBFC"),
    ('BAJAJFINSV', 'Bajaj Finserv', 'NBFC', 280000, 18.3, 16.2, "Diversified financial services"),
    ('SHRIRAMFIN', 'Shriram Finance', 'NBFC', 95000, 16.8, 18.5, "Leading retail NBFC"),
    ('CHOLAFIN', 'Cholamandalam Inv & Fin', 'NBFC', 110000, 20.1, 22.3, "Vehicle financing leader"),
    # Insurance
    ('SBILIFE', 'SBI Life Insurance', 'Insurance', 165000, 65.2, 18.5, "Joint venture life insurance company"),
    ('HDFCLIFE', 'HDFC Life Insurance', 'Insurance', 145000, 58.3, 15.2, "Leading private life insurer"),
    # Energy / Oil & Gas
    ('RELIANCE', 'Reliance Industries', 'Energy', 1850000, 12.1, 9.5, "India's most valuable private company"),
    ('ONGC', 'Oil & Natural Gas Corp', 'Energy', 320000, 14.2, 15.8, "Largest crude oil producer in India"),
    ('IOC', 'Indian Oil Corporation', 'Energy', 230000, 18.5, 22.1, "India's largest commercial oil company"),
    ('BPCL', 'Bharat Petroleum', 'Energy', 155000, 20.3, 25.4, "Major oil refining company"),
    ('GAIL', 'GAIL India', 'Energy', 120000, 12.8, 13.5, "India's largest natural gas company"),
    # Adani Group
    ('ADANIENT', 'Adani Enterprises', 'Conglomerate', 350000, 14.5, 18.2, "Adani Group flagship company"),
    ('ADANIGREEN', 'Adani Green Energy', 'Power', 280000, 8.2, 12.5, "Largest renewable energy company"),
    ('ADANIPORTS', 'Adani Ports & SEZ', 'Ports', 310000, 18.3, 16.8, "Largest port operator in India"),
    ('ADANIPOWER', 'Adani Power', 'Power', 220000, 22.1, 35.6, "Largest private thermal power producer"),
    ('ATGL', 'Adani Total Gas', 'Energy', 95000, 42.5, 28.3, "City gas distribution company"),
    ('ADANIENSOL', 'Adani Energy Solutions', 'Power', 105000, 10.2, 8.5, "Power transmission company"),
    # Pharma & Healthcare
    ('SUNPHARMA', 'Sun Pharmaceutical', 'Pharma', 420000, 22.8, 18.5, "India's largest pharma company"),
    ('DRREDDY', 'Dr. Reddy\'s Labs', 'Pharma', 115000, 20.5, 19.2, "Global pharmaceutical company"),
    ('CIPLA', 'Cipla', 'Pharma', 120000, 18.3, 16.8, "Leading global pharma company"),
    ('DIVISLAB', 'Divi\'s Laboratories', 'Pharma', 105000, 25.2, 22.1, "Leading API manufacturer"),
    ('APOLLOHOSP', 'Apollo Hospitals', 'Healthcare', 95000, 18.5, 16.2, "Asia's largest healthcare group"),
    ('MANKIND', 'Mankind Pharma', 'Pharma', 85000, 24.1, 21.5, "Major pharmaceutical company"),
    # FMCG / Consumer
    ('HINDUNILVR', 'Hindustan Unilever', 'FMCG', 580000, 95.2, 82.3, "India's largest FMCG company"),
    ('ITC', 'ITC', 'FMCG', 570000, 32.5, 28.1, "Diversified conglomerate"),
    ('NESTLEIND', 'Nestle India', 'FMCG', 220000, 108.5, 72.3, "Leading food company"),
    ('BRITANNIA', 'Britannia Industries', 'FMCG', 125000, 62.3, 55.2, "Leading food company"),
    ('TATACONSUM', 'Tata Consumer Products', 'FMCG', 110000, 12.5, 10.8, "Consumer products company"),
    ('GODREJCP', 'Godrej Consumer Products', 'FMCG', 95000, 22.5, 18.3, "FMCG company"),
    ('COLPAL', 'Colgate-Palmolive India', 'FMCG', 85000, 85.2, 72.1, "Oral care leader"),
    ('MARICO', 'Marico', 'FMCG', 78000, 42.3, 38.5, "Consumer goods company"),
    ('DABUR', 'Dabur India', 'FMCG', 92000, 28.5, 22.1, "Ayurvedic products company"),
    # Auto
    ('BAJAJ-AUTO', 'Bajaj Auto', 'Auto', 245000, 32.5, 25.3, "Two & three-wheeler manufacturer"),
    ('TATAMOTORS', 'Tata Motors', 'Auto', 320000, 15.8, 32.5, "Leading automobile manufacturer"),
    ('M&M', 'Mahindra & Mahindra', 'Auto', 350000, 18.2, 20.1, "Auto and farm equipment major"),
    ('MARUTI', 'Maruti Suzuki India', 'Auto', 380000, 25.3, 18.5, "India's largest car maker"),
    ('EICHERMOT', 'Eicher Motors', 'Auto', 135000, 32.1, 25.8, "Royal Enfield manufacturer"),
    ('HEROMOTOCO', 'Hero MotoCorp', 'Auto', 105000, 28.5, 22.3, "World's largest two-wheeler company"),
    ('TVSMOTOR', 'TVS Motor Company', 'Auto', 98000, 22.1, 25.6, "Leading two-wheeler company"),
    # Metals & Mining
    ('TATASTEEL', 'Tata Steel', 'Metals', 185000, 12.5, 15.8, "Global steel company"),
    ('JSWSTEEL', 'JSW Steel', 'Metals', 225000, 14.2, 18.3, "Leading steel producer"),
    ('HINDALCO', 'Hindalco Industries', 'Metals', 145000, 11.8, 12.5, "Aluminium and copper producer"),
    ('COALINDIA', 'Coal India', 'Metals', 280000, 52.3, 45.2, "World's largest coal producer"),
    # Cement
    ('ULTRACEMCO', 'UltraTech Cement', 'Cement', 195000, 14.8, 12.5, "India's largest cement company"),
    ('AMBUJACEM', 'Ambuja Cements', 'Cement', 85000, 12.5, 10.8, "Leading cement manufacturer"),
    ('SHREECEM', 'Shree Cement', 'Cement', 95000, 16.2, 14.5, "Major cement producer"),
    # Telecom
    ('BHARTIARTL', 'Bharti Airtel', 'Telecom', 850000, 18.5, 22.3, "India's largest telecom operator"),
    ('JIOFIN', 'Jio Financial Services', 'NBFC', 185000, 3.2, 2.8, "Digital financial services company"),
    # Infra / Capital Goods
    ('LT', 'Larsen & Toubro', 'Capital Goods', 520000, 18.3, 15.2, "Engineering and construction major"),
    ('SIEMENS', 'Siemens', 'Capital Goods', 175000, 22.5, 18.3, "Engineering conglomerate"),
    ('ABB', 'ABB India', 'Capital Goods', 135000, 28.5, 22.1, "Power and automation technology"),
    ('HAL', 'Hindustan Aeronautics', 'Capital Goods', 320000, 32.5, 28.3, "Defence aerospace company"),
    ('BEL', 'Bharat Electronics', 'Capital Goods', 195000, 28.1, 25.2, "Defence electronics company"),
    # Power & Utilities
    ('NTPC', 'NTPC', 'Power', 380000, 12.5, 14.8, "India's largest power utility"),
    ('POWERGRID', 'Power Grid Corporation', 'Power', 310000, 16.8, 20.5, "Power transmission company"),
    ('TATAPOWER', 'Tata Power', 'Power', 145000, 10.5, 12.3, "Integrated power company"),
    # Paints
    ('ASIANPAINT', 'Asian Paints', 'Paints', 295000, 32.5, 25.8, "India's largest paint company"),
    # Real Estate
    ('DLF', 'DLF', 'Real Estate', 165000, 8.5, 6.2, "India's largest real estate company"),
    ('LODHA', 'Macrotech Developers', 'Real Estate', 95000, 12.3, 18.5, "Premium real estate developer"),
    # Chemicals
    ('PIDILITIND', 'Pidilite Industries', 'Chemicals', 135000, 32.5, 25.8, "Adhesives and sealants company"),
    ('SRF', 'SRF', 'Chemicals', 78000, 18.5, 15.2, "Chemical and packaging company"),
    # Consumer Durables
    ('TITAN', 'Titan Company', 'Consumer', 295000, 32.1, 28.5, "Jewellery and watches company"),
    ('HAVELLS', 'Havells India', 'Consumer', 110000, 28.3, 22.5, "Electrical equipment company"),
    # Holding / Diversified
    ('LICI', 'Life Insurance Corp', 'Insurance', 620000, 65.8, 72.5, "India's largest insurer"),
    ('IRFC', 'Indian Railway Finance', 'NBFC', 195000, 8.5, 12.3, "Railway financing company"),
    # Transport & Logistics
    ('ZOMATO', 'Zomato', 'Consumer', 185000, -5.2, -8.5, "Food delivery platform"),
    ('TRENT', 'Trent', 'Consumer', 135000, 18.5, 22.3, "Retail company (Westside, Zudio)"),
    ('NAUKRI', 'Info Edge India', 'IT', 85000, 15.2, 12.5, "Online recruitment platform"),
    ('DMART', 'Avenue Supermarts', 'Consumer', 295000, 22.5, 15.8, "Value retail chain"),
    # Others
    ('JSWENERGY', 'JSW Energy', 'Power', 85000, 10.2, 12.5, "Integrated power company"),
    ('TORNTPHARM', 'Torrent Pharmaceuticals', 'Pharma', 78000, 28.5, 25.2, "Pharmaceutical company"),
    ('INDIGO', 'InterGlobe Aviation', 'Aviation', 95000, 45.2, 52.3, "India's largest airline"),
    ('MAXHEALTH', 'Max Healthcare', 'Healthcare', 85000, 22.5, 18.3, "Healthcare services company"),
    ('CANBK', 'Canara Bank', 'Banking', 95000, 9.5, 15.8, "Public sector bank"),
    ('UNIONBANK', 'Union Bank of India', 'Banking', 85000, 8.8, 14.2, "Public sector bank"),
    ('BHARATFORG', 'Bharat Forge', 'Capital Goods', 72000, 18.5, 15.2, "Forging company"),
    ('POLYCAB', 'Polycab India', 'Capital Goods', 85000, 25.3, 22.1, "Wire and cable manufacturer"),
    ('PERSISTENT', 'Persistent Systems', 'IT', 68000, 28.5, 25.2, "Software services company"),
    ('COFORGE', 'Coforge', 'IT', 48000, 22.3, 18.5, "IT solutions company"),
    ('VEDL', 'Vedanta', 'Metals', 145000, 18.5, 35.2, "Diversified mining company"),
    ('GRASIM', 'Grasim Industries', 'Cement', 125000, 10.5, 8.2, "Aditya Birla Group flagship"),
    ('HINDZINC', 'Hindustan Zinc', 'Metals', 185000, 42.5, 35.8, "Zinc and lead producer"),
    ('BOSCHLTD', 'Bosch', 'Auto', 95000, 15.2, 12.5, "Auto component manufacturer"),
    ('PAGEIND', 'Page Industries', 'Consumer', 52000, 55.2, 42.3, "Jockey brand licensee"),
    ('UNITDSPR', 'United Spirits', 'FMCG', 78000, 18.5, 15.2, "Alcoholic beverages company"),
]

# Sector definitions with colors
SECTORS = [
    ('IT', 'Information Technology', '#6366F1', 'Software services, consulting, and digital transformation'),
    ('Banking', 'Banking', '#3B82F6', 'Commercial and retail banking services'),
    ('NBFC', 'Non-Banking Finance', '#8B5CF6', 'Lending, leasing, and financial services outside banking'),
    ('Insurance', 'Insurance', '#06B6D4', 'Life and general insurance companies'),
    ('Energy', 'Energy & Oil/Gas', '#F59E0B', 'Oil refining, gas distribution, and energy production'),
    ('Power', 'Power & Utilities', '#EF4444', 'Power generation, transmission, and distribution'),
    ('Pharma', 'Pharmaceuticals', '#10B981', 'Drug manufacturing and healthcare products'),
    ('Healthcare', 'Healthcare Services', '#14B8A6', 'Hospitals, diagnostics, and health services'),
    ('FMCG', 'FMCG', '#F97316', 'Fast-moving consumer goods'),
    ('Auto', 'Automobile', '#EC4899', 'Vehicle manufacturers and auto components'),
    ('Metals', 'Metals & Mining', '#64748B', 'Steel, aluminium, mining, and minerals'),
    ('Cement', 'Cement & Building', '#78716C', 'Cement and building materials'),
    ('Telecom', 'Telecommunications', '#A855F7', 'Telecom service providers'),
    ('Capital Goods', 'Capital Goods', '#0EA5E9', 'Engineering, construction, and defence equipment'),
    ('Paints', 'Paints & Coatings', '#D946EF', 'Decorative and industrial paints'),
    ('Real Estate', 'Real Estate', '#84CC16', 'Property development and construction'),
    ('Chemicals', 'Chemicals', '#FBBF24', 'Specialty and commodity chemicals'),
    ('Consumer', 'Consumer Durables', '#FB923C', 'Jewellery, retail, and consumer products'),
    ('Conglomerate', 'Conglomerate', '#94A3B8', 'Multi-sector holding companies'),
    ('Ports', 'Ports & Logistics', '#2DD4BF', 'Port operations and logistics'),
    ('Aviation', 'Aviation', '#38BDF8', 'Airlines and aviation services'),
]

HEALTH_LABELS = [
    ('EXCELLENT', 80, 100, '#10B981'),
    ('GOOD', 60, 79.99, '#22C55E'),
    ('AVERAGE', 40, 59.99, '#F59E0B'),
    ('WEAK', 20, 39.99, '#F97316'),
    ('POOR', 0, 19.99, '#EF4444'),
]

YEAR_LABELS = [
    ('Mar 2013', 2013, 1), ('Mar 2014', 2014, 2), ('Mar 2015', 2015, 3),
    ('Mar 2016', 2016, 4), ('Mar 2017', 2017, 5), ('Mar 2018', 2018, 6),
    ('Mar 2019', 2019, 7), ('Mar 2020', 2020, 8), ('Mar 2021', 2021, 9),
    ('Mar 2022', 2022, 10), ('Mar 2023', 2023, 11), ('Mar 2024', 2024, 12),
    ('TTM', None, 13),
]


class Command(BaseCommand):
    help = 'Seed the data warehouse with realistic Nifty 100 financial data'

    def handle(self, *args, **options):
        random.seed(42)  # Reproducible data
        self.stdout.write(self.style.WARNING('[*] Seeding BlueStock Nifty 100 Data Warehouse...'))

        self._seed_health_labels()
        self._seed_sectors()
        self._seed_years()
        self._seed_companies()
        self._seed_financials()
        self._seed_analysis()
        self._seed_ml_scores()
        self._seed_pros_cons()

        self.stdout.write(self.style.SUCCESS('[OK] Seed complete! All tables populated.'))

    def _seed_health_labels(self):
        for name, mn, mx, color in HEALTH_LABELS:
            DimHealthLabel.objects.update_or_create(
                label_name=name,
                defaults={'min_score': mn, 'max_score': mx, 'color_hex': color}
            )
        self.stdout.write(f'  [+] {DimHealthLabel.objects.count()} health labels')

    def _seed_sectors(self):
        for code, name, color, desc in SECTORS:
            DimSector.objects.update_or_create(
                sector_code=code,
                defaults={'sector_name': name, 'color_hex': color, 'description': desc}
            )
        self.stdout.write(f'  [+] {DimSector.objects.count()} sectors')

    def _seed_years(self):
        for label, fy, order in YEAR_LABELS:
            DimYear.objects.update_or_create(
                year_label=label,
                defaults={
                    'fiscal_year': fy,
                    'is_ttm': label == 'TTM',
                    'sort_order': order,
                }
            )
        self.stdout.write(f'  [+] {DimYear.objects.count()} year periods')

    def _seed_companies(self):
        sector_map = {s.sector_code: s for s in DimSector.objects.all()}
        for sym, name, sec, mcap, roce, roe, about in COMPANIES:
            DimCompany.objects.update_or_create(
                symbol=sym,
                defaults={
                    'company_name': name,
                    'sector': sector_map.get(sec),
                    'face_value': Decimal(random.choice([1, 2, 5, 10])),
                    'book_value': Decimal(str(round(random.uniform(50, 800), 2))),
                    'roce_pct': Decimal(str(roce)),
                    'roe_pct': Decimal(str(roe)),
                    'about_company': about,
                    'market_cap_cr': Decimal(str(mcap)),
                    'website': f'https://www.{sym.lower().replace("-", "")}.com',
                    'nse_url': f'https://www.nseindia.com/get-quotes/equity?symbol={sym}',
                    'bse_url': f'https://www.bseindia.com/stock-share-price/{sym}',
                }
            )
        self.stdout.write(f'  [+] {DimCompany.objects.count()} companies')

    def _seed_financials(self):
        """Generate 12 years of P&L, Balance Sheet, Cash Flow for each company."""
        companies = list(DimCompany.objects.all())
        years = list(DimYear.objects.all().order_by('sort_order'))

        pl_count = 0
        bs_count = 0
        cf_count = 0

        for comp in companies:
            mcap = float(comp.market_cap_cr or 100000)
            scale = mcap / 200000  # Revenue scale factor
            base_sales = max(500, scale * random.uniform(8000, 60000))
            growth = random.uniform(1.05, 1.18)
            margin = random.uniform(0.08, 0.35)

            for i, yr in enumerate(years):
                sales = round(base_sales * (growth ** i) * random.uniform(0.92, 1.08), 2)
                expenses = round(sales * random.uniform(0.62, 0.88), 2)
                op_profit = round(sales - expenses, 2)
                opm = round((op_profit / sales) * 100, 2) if sales else 0
                other_inc = round(sales * random.uniform(0.01, 0.05), 2)
                interest = round(sales * random.uniform(0.01, 0.08), 2)
                deprec = round(sales * random.uniform(0.02, 0.06), 2)
                pbt = round(op_profit + other_inc - interest - deprec, 2)
                tax_pct = round(random.uniform(18, 30), 2)
                net_profit = round(pbt * (1 - tax_pct / 100), 2)
                eps = round(net_profit / random.uniform(20, 200), 2)
                div_pct = round(random.uniform(5, 45), 2)
                npm = round((net_profit / sales) * 100, 2) if sales else 0
                exp_ratio = round((expenses / sales) * 100, 2) if sales else 0
                int_cov = round(op_profit / interest, 2) if interest else 0

                FactProfitLoss.objects.update_or_create(
                    company=comp, year=yr,
                    defaults={
                        'sales': sales, 'expenses': expenses,
                        'operating_profit': op_profit, 'opm_pct': opm,
                        'other_income': other_inc, 'interest': interest,
                        'depreciation': deprec, 'profit_before_tax': pbt,
                        'tax_pct': tax_pct, 'net_profit': net_profit,
                        'eps': eps, 'dividend_payout_pct': div_pct,
                        'net_profit_margin_pct': npm,
                        'expense_ratio_pct': exp_ratio,
                        'interest_coverage': int_cov,
                    }
                )
                pl_count += 1

                # Balance Sheet
                equity = round(sales * random.uniform(0.05, 0.15), 2)
                reserves = round(sales * random.uniform(1.0, 4.0), 2)
                borrowings = round(sales * random.uniform(0.1, 1.5), 2)
                other_liab = round(sales * random.uniform(0.2, 0.8), 2)
                total_liab = round(equity + reserves + borrowings + other_liab, 2)
                fixed_assets = round(total_liab * random.uniform(0.2, 0.5), 2)
                cwip = round(total_liab * random.uniform(0.02, 0.1), 2)
                investments = round(total_liab * random.uniform(0.1, 0.3), 2)
                other_assets = round(total_liab - fixed_assets - cwip - investments, 2)
                total_assets = total_liab
                dte = round(borrowings / (equity + reserves), 4) if (equity + reserves) else 0
                eq_ratio = round((equity + reserves) / total_assets, 4) if total_assets else 0

                FactBalanceSheet.objects.update_or_create(
                    company=comp, year=yr,
                    defaults={
                        'equity_capital': equity, 'reserves': reserves,
                        'borrowings': borrowings, 'other_liabilities': other_liab,
                        'total_liabilities': total_liab,
                        'fixed_assets': fixed_assets, 'cwip': cwip,
                        'investments': investments, 'other_assets': other_assets,
                        'total_assets': total_assets,
                        'debt_to_equity': dte, 'equity_ratio': eq_ratio,
                    }
                )
                bs_count += 1

                # Cash Flow
                ocf = round(net_profit * random.uniform(0.8, 1.5), 2)
                icf = round(-abs(sales * random.uniform(0.05, 0.3)), 2)
                fcf_val = round(ocf + icf, 2)
                fin_cf = round(random.uniform(-abs(sales * 0.2), sales * 0.1), 2)
                net_cf = round(ocf + icf + fin_cf, 2)

                FactCashFlow.objects.update_or_create(
                    company=comp, year=yr,
                    defaults={
                        'operating_activity': ocf,
                        'investing_activity': icf,
                        'financing_activity': fin_cf,
                        'net_cash_flow': net_cf,
                        'free_cash_flow': fcf_val,
                    }
                )
                cf_count += 1

        self.stdout.write(f'  [+] {pl_count} P&L rows, {bs_count} BS rows, {cf_count} CF rows')

    def _seed_analysis(self):
        count = 0
        for comp in DimCompany.objects.all():
            for period in ['10Y', '5Y', '3Y', 'TTM']:
                FactAnalysis.objects.update_or_create(
                    company=comp, period_label=period,
                    defaults={
                        'compounded_sales_growth_pct': round(random.uniform(2, 28), 2),
                        'compounded_profit_growth_pct': round(random.uniform(-5, 35), 2),
                        'stock_price_cagr_pct': round(random.uniform(-2, 40), 2),
                        'roe_pct': round(random.uniform(5, 45), 2),
                    }
                )
                count += 1
        self.stdout.write(f'  [+] {count} analysis rows')

    def _seed_ml_scores(self):
        labels = {l.label_name: l for l in DimHealthLabel.objects.all()}
        count = 0
        for comp in DimCompany.objects.all():
            overall = round(random.uniform(25, 95), 2)
            if overall >= 80:
                lbl = labels.get('EXCELLENT')
            elif overall >= 60:
                lbl = labels.get('GOOD')
            elif overall >= 40:
                lbl = labels.get('AVERAGE')
            elif overall >= 20:
                lbl = labels.get('WEAK')
            else:
                lbl = labels.get('POOR')

            FactMLScore.objects.update_or_create(
                company=comp,
                defaults={
                    'overall_score': overall,
                    'profitability_score': round(random.uniform(20, 95), 2),
                    'growth_score': round(random.uniform(15, 90), 2),
                    'leverage_score': round(random.uniform(25, 95), 2),
                    'cashflow_score': round(random.uniform(20, 90), 2),
                    'dividend_score': round(random.uniform(10, 85), 2),
                    'trend_score': round(random.uniform(15, 90), 2),
                    'health_label': lbl,
                }
            )
            count += 1
        self.stdout.write(f'  [+] {count} ML score rows')

    def _seed_pros_cons(self):
        PRO_TEMPLATES = [
            ("Company has delivered good profit growth of {v:.1f}% CAGR over last 5 years", "Growth"),
            ("Company has a good return on equity (ROE) track record: 3 year ROE {v:.1f}%", "Profitability"),
            ("Company has been maintaining a healthy dividend payout of {v:.1f}%", "Dividend"),
            ("Company is almost debt free", "Leverage"),
            ("Stock is trading at {v:.1f}x its book value", "Valuation"),
            ("Company has strong cash flow from operations", "Cash Flow"),
            ("Promoter holding is high at {v:.1f}%", "Governance"),
        ]
        CON_TEMPLATES = [
            ("Stock is trading at {v:.1f} times its book value", "Valuation"),
            ("Company has low interest coverage ratio of {v:.1f}", "Leverage"),
            ("The company has delivered a poor growth of {v:.1f}% over past 5 years", "Growth"),
            ("Tax rate seems low at {v:.1f}%", "Tax"),
            ("Promoter holding has decreased by {v:.1f}% over last quarter", "Governance"),
        ]

        count = 0
        for comp in DimCompany.objects.all():
            n_pros = random.randint(2, 4)
            for t, cat in random.sample(PRO_TEMPLATES, min(n_pros, len(PRO_TEMPLATES))):
                FactProsCons.objects.create(
                    company=comp, is_pro=True, category=cat,
                    text=t.format(v=random.uniform(10, 65)),
                    source='MANUAL', confidence=round(random.uniform(0.7, 1.0), 2)
                )
                count += 1

            n_cons = random.randint(1, 3)
            for t, cat in random.sample(CON_TEMPLATES, min(n_cons, len(CON_TEMPLATES))):
                FactProsCons.objects.create(
                    company=comp, is_pro=False, category=cat,
                    text=t.format(v=random.uniform(1, 30)),
                    source='MANUAL', confidence=round(random.uniform(0.6, 0.95), 2)
                )
                count += 1

        self.stdout.write(f'  [+] {count} pros/cons rows')
