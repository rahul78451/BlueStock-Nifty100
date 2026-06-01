"""
Star Schema Models for BlueStock Nifty 100 Data Warehouse
=========================================================
Dimension tables: DimCompany, DimYear, DimSector, DimHealthLabel
Fact tables: FactProfitLoss, FactBalanceSheet, FactCashFlow, FactAnalysis, FactMLScore, FactProsCons
"""
from django.db import models


# ============================================================
# DIMENSION TABLES
# ============================================================

class DimSector(models.Model):
    """Sector dimension — classifies companies into industry verticals."""
    sector_id = models.AutoField(primary_key=True)
    sector_name = models.CharField(max_length=100, unique=True)
    sector_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, default='')
    color_hex = models.CharField(max_length=7, default='#6366F1')

    class Meta:
        db_table = 'dim_sector'
        ordering = ['sector_name']

    def __str__(self):
        return self.sector_name


class DimCompany(models.Model):
    """Company dimension — master data for each Nifty 100 company."""
    symbol = models.CharField(max_length=30, primary_key=True)
    company_name = models.CharField(max_length=200)
    sector = models.ForeignKey(DimSector, on_delete=models.SET_NULL, null=True, related_name='companies')
    sub_sector = models.CharField(max_length=100, blank=True, default='')
    company_logo = models.URLField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    nse_url = models.URLField(blank=True, default='')
    bse_url = models.URLField(blank=True, default='')
    face_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    book_value = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    roce_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    roe_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    about_company = models.TextField(blank=True, default='')
    market_cap_cr = models.DecimalField(max_digits=14, decimal_places=2, null=True)

    class Meta:
        db_table = 'dim_company'
        ordering = ['company_name']

    def __str__(self):
        return f"{self.symbol} — {self.company_name}"


class DimYear(models.Model):
    """Year/period dimension — standardized time periods for all financial data."""
    year_id = models.AutoField(primary_key=True)
    year_label = models.CharField(max_length=20, unique=True)  # 'Mar 2024', 'TTM'
    fiscal_year = models.IntegerField(null=True)                # 2024
    quarter = models.CharField(max_length=5, blank=True, default='')  # Q1-Q4
    is_ttm = models.BooleanField(default=False)
    is_half_year = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'dim_year'
        ordering = ['sort_order']

    def __str__(self):
        return self.year_label


class DimHealthLabel(models.Model):
    """Health label dimension — maps ML scores to human-readable ratings."""
    label_id = models.AutoField(primary_key=True)
    label_name = models.CharField(max_length=20, unique=True)  # EXCELLENT/GOOD/AVERAGE/WEAK/POOR
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    color_hex = models.CharField(max_length=7, default='#6366F1')

    class Meta:
        db_table = 'dim_health_label'
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.label_name} ({self.min_score}–{self.max_score})"


# ============================================================
# FACT TABLES
# ============================================================

class FactProfitLoss(models.Model):
    """Fact: Annual profit & loss statement per company per year."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='profit_loss')
    year = models.ForeignKey(DimYear, on_delete=models.CASCADE, related_name='profit_loss')
    sales = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    expenses = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    operating_profit = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    opm_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    other_income = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    interest = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    depreciation = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    profit_before_tax = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    tax_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    net_profit = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    eps = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    dividend_payout_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    # Computed columns
    net_profit_margin_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    expense_ratio_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    interest_coverage = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_profit_loss'
        unique_together = ('company', 'year')

    def __str__(self):
        return f"{self.company_id} — {self.year} P&L"


class FactBalanceSheet(models.Model):
    """Fact: Annual balance sheet per company per year."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='balance_sheets')
    year = models.ForeignKey(DimYear, on_delete=models.CASCADE, related_name='balance_sheets')
    equity_capital = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    reserves = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    borrowings = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    other_liabilities = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_liabilities = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    fixed_assets = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    cwip = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    investments = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    other_assets = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_assets = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    # Computed columns
    debt_to_equity = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    equity_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True)

    class Meta:
        db_table = 'fact_balance_sheet'
        unique_together = ('company', 'year')

    def __str__(self):
        return f"{self.company_id} — {self.year} Balance Sheet"


class FactCashFlow(models.Model):
    """Fact: Annual cash flow statement per company per year."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='cash_flows')
    year = models.ForeignKey(DimYear, on_delete=models.CASCADE, related_name='cash_flows')
    operating_activity = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    investing_activity = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    financing_activity = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    net_cash_flow = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    # Computed
    free_cash_flow = models.DecimalField(max_digits=14, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_cash_flow'
        unique_together = ('company', 'year')

    def __str__(self):
        return f"{self.company_id} — {self.year} Cash Flow"


class FactAnalysis(models.Model):
    """Fact: Growth metrics per company per analysis period (10Y/5Y/3Y/TTM)."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='analysis')
    period_label = models.CharField(max_length=10)  # 10Y, 5Y, 3Y, TTM
    compounded_sales_growth_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    compounded_profit_growth_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    stock_price_cagr_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    roe_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True)

    class Meta:
        db_table = 'fact_analysis'
        unique_together = ('company', 'period_label')

    def __str__(self):
        return f"{self.company_id} — {self.period_label}"


class FactMLScore(models.Model):
    """Fact: ML-generated company health scores."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='ml_scores')
    computed_at = models.DateTimeField(auto_now_add=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2)
    profitability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    growth_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    leverage_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    cashflow_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    dividend_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    trend_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    health_label = models.ForeignKey(DimHealthLabel, on_delete=models.SET_NULL, null=True, related_name='scores')

    class Meta:
        db_table = 'fact_ml_scores'
        ordering = ['-computed_at']

    def __str__(self):
        return f"{self.company_id} — {self.overall_score} ({self.health_label})"


class FactProsCons(models.Model):
    """Fact: Pros and cons insights per company."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='pros_cons')
    is_pro = models.BooleanField()
    category = models.CharField(max_length=50, blank=True, default='')
    text = models.TextField()
    source = models.CharField(max_length=10, default='MANUAL', choices=[('MANUAL', 'Manual'), ('ML', 'ML Generated')])
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fact_pros_cons'

    def __str__(self):
        tag = 'PRO' if self.is_pro else 'CON'
        return f"{self.company_id} — {tag}: {self.text[:60]}"


class Document(models.Model):
    """BSE annual report links per company per year."""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(DimCompany, on_delete=models.CASCADE, related_name='documents')
    year = models.ForeignKey(DimYear, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, default='Annual Report')
    url = models.URLField(max_length=500)

    class Meta:
        db_table = 'documents'

    def __str__(self):
        return f"{self.company_id} — {self.year} — {self.document_type}"
