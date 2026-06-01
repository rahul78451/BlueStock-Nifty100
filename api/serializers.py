"""
REST API Serializers for BlueStock Nifty 100
=============================================
Provides read-only serialization for all warehouse models.
"""
from rest_framework import serializers
from warehouse.models import (
    DimSector, DimCompany, DimYear, DimHealthLabel,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons
)


class SectorSerializer(serializers.ModelSerializer):
    company_count = serializers.SerializerMethodField()

    class Meta:
        model = DimSector
        fields = '__all__'

    def get_company_count(self, obj):
        return obj.companies.count()


class CompanyListSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True, default='')
    health_score = serializers.SerializerMethodField()
    health_label = serializers.SerializerMethodField()

    class Meta:
        model = DimCompany
        fields = [
            'symbol', 'company_name', 'sector_name', 'market_cap_cr',
            'roce_pct', 'roe_pct', 'book_value', 'health_score', 'health_label'
        ]

    def get_health_score(self, obj):
        score = obj.ml_scores.first()
        return float(score.overall_score) if score else None

    def get_health_label(self, obj):
        score = obj.ml_scores.first()
        return score.health_label.label_name if score and score.health_label else None


class ProfitLossSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)

    class Meta:
        model = FactProfitLoss
        exclude = ['id']


class BalanceSheetSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)

    class Meta:
        model = FactBalanceSheet
        exclude = ['id']


class CashFlowSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True)

    class Meta:
        model = FactCashFlow
        exclude = ['id']


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactAnalysis
        exclude = ['id']


class MLScoreSerializer(serializers.ModelSerializer):
    health_label_name = serializers.CharField(source='health_label.label_name', read_only=True, default='')
    health_color = serializers.CharField(source='health_label.color_hex', read_only=True, default='')

    class Meta:
        model = FactMLScore
        exclude = ['id']


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactProsCons
        exclude = ['id']


class CompanyDetailSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True, default='')
    sector_color = serializers.CharField(source='sector.color_hex', read_only=True, default='')
    profit_loss = ProfitLossSerializer(many=True, read_only=True)
    balance_sheets = BalanceSheetSerializer(many=True, read_only=True)
    cash_flows = CashFlowSerializer(many=True, read_only=True)
    analysis = AnalysisSerializer(many=True, read_only=True)
    ml_scores = MLScoreSerializer(many=True, read_only=True)
    pros_cons = ProsConsSerializer(many=True, read_only=True)

    class Meta:
        model = DimCompany
        fields = '__all__'
