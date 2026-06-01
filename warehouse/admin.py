"""Admin registration for all warehouse models."""
from django.contrib import admin
from .models import (
    DimSector, DimCompany, DimYear, DimHealthLabel,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons, Document
)


@admin.register(DimSector)
class DimSectorAdmin(admin.ModelAdmin):
    list_display = ('sector_code', 'sector_name', 'color_hex')
    search_fields = ('sector_name',)


@admin.register(DimCompany)
class DimCompanyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'sector', 'market_cap_cr', 'roce_pct', 'roe_pct')
    list_filter = ('sector',)
    search_fields = ('symbol', 'company_name')


@admin.register(DimYear)
class DimYearAdmin(admin.ModelAdmin):
    list_display = ('year_label', 'fiscal_year', 'is_ttm', 'sort_order')
    list_filter = ('is_ttm',)


@admin.register(DimHealthLabel)
class DimHealthLabelAdmin(admin.ModelAdmin):
    list_display = ('label_name', 'min_score', 'max_score', 'color_hex')


@admin.register(FactProfitLoss)
class FactProfitLossAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'sales', 'net_profit', 'opm_pct', 'eps')
    list_filter = ('year', 'company__sector')
    search_fields = ('company__symbol', 'company__company_name')


@admin.register(FactBalanceSheet)
class FactBalanceSheetAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'total_assets', 'total_liabilities', 'debt_to_equity')
    list_filter = ('year',)
    search_fields = ('company__symbol',)


@admin.register(FactCashFlow)
class FactCashFlowAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'operating_activity', 'net_cash_flow', 'free_cash_flow')
    list_filter = ('year',)
    search_fields = ('company__symbol',)


@admin.register(FactAnalysis)
class FactAnalysisAdmin(admin.ModelAdmin):
    list_display = ('company', 'period_label', 'compounded_sales_growth_pct', 'roe_pct')
    list_filter = ('period_label',)
    search_fields = ('company__symbol',)


@admin.register(FactMLScore)
class FactMLScoreAdmin(admin.ModelAdmin):
    list_display = ('company', 'overall_score', 'health_label', 'computed_at')
    list_filter = ('health_label',)
    search_fields = ('company__symbol',)


@admin.register(FactProsCons)
class FactProsConsAdmin(admin.ModelAdmin):
    list_display = ('company', 'is_pro', 'category', 'source', 'text')
    list_filter = ('is_pro', 'source')
    search_fields = ('company__symbol', 'text')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'document_type')
    list_filter = ('year',)
    search_fields = ('company__symbol',)
