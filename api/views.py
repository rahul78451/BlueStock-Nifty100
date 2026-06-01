"""
REST API Views for BlueStock Nifty 100
=======================================
Read-only ViewSets for channel partner API access.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q, Max
from warehouse.models import (
    DimSector, DimCompany, DimYear,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons
)
from .serializers import (
    SectorSerializer, CompanyListSerializer, CompanyDetailSerializer,
    ProfitLossSerializer, BalanceSheetSerializer, CashFlowSerializer,
    AnalysisSerializer, MLScoreSerializer, ProsConsSerializer
)


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for sectors — lists all sectors with company counts."""
    queryset = DimSector.objects.all()
    serializer_class = SectorSerializer
    search_fields = ['sector_name', 'sector_code']


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for companies — list/detail with full financial data."""
    queryset = DimCompany.objects.select_related('sector').prefetch_related(
        'ml_scores', 'ml_scores__health_label'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sector__sector_code', 'ml_scores__health_label__label_name']
    search_fields = ['symbol', 'company_name']
    ordering_fields = ['market_cap_cr', 'roce_pct', 'roe_pct', 'company_name']
    ordering = ['-market_cap_cr']
    lookup_field = 'symbol'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanyListSerializer

    @action(detail=True, methods=['get'])
    def financials(self, request, symbol=None):
        """Get full financial details for a specific company."""
        company = self.get_object()
        return Response(CompanyDetailSerializer(company).data)


class ProfitLossViewSet(viewsets.ReadOnlyModelViewSet):
    """P&L data for all companies."""
    queryset = FactProfitLoss.objects.select_related('company', 'year').all()
    serializer_class = ProfitLossSerializer
    filterset_fields = ['company__symbol', 'year__fiscal_year']
    ordering = ['company__symbol', 'year__sort_order']


class BalanceSheetViewSet(viewsets.ReadOnlyModelViewSet):
    """Balance sheet data for all companies."""
    queryset = FactBalanceSheet.objects.select_related('company', 'year').all()
    serializer_class = BalanceSheetSerializer
    filterset_fields = ['company__symbol', 'year__fiscal_year']
    ordering = ['company__symbol', 'year__sort_order']


class CashFlowViewSet(viewsets.ReadOnlyModelViewSet):
    """Cash flow data for all companies."""
    queryset = FactCashFlow.objects.select_related('company', 'year').all()
    serializer_class = CashFlowSerializer
    filterset_fields = ['company__symbol', 'year__fiscal_year']
    ordering = ['company__symbol', 'year__sort_order']


class MLScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ML health scores for all companies."""
    queryset = FactMLScore.objects.select_related('company', 'health_label').all()
    serializer_class = MLScoreSerializer
    filterset_fields = ['company__symbol', 'health_label__label_name']
    ordering = ['-overall_score']


@api_view(['GET'])
def dashboard_stats(request):
    """Aggregate stats for the main dashboard."""
    total_companies = DimCompany.objects.count()
    total_sectors = DimSector.objects.count()
    avg_score = FactMLScore.objects.aggregate(avg=Avg('overall_score'))['avg']
    label_dist = FactMLScore.objects.values(
        'health_label__label_name', 'health_label__color_hex'
    ).annotate(count=Count('id')).order_by('-count')

    # Top 10 by ML score
    top_companies = FactMLScore.objects.select_related(
        'company', 'company__sector', 'health_label'
    ).order_by('-overall_score')[:10]

    # Sector performance
    sector_perf = DimSector.objects.annotate(
        avg_score=Avg('companies__ml_scores__overall_score'),
        company_count=Count('companies', distinct=True)
    ).values('sector_name', 'sector_code', 'color_hex', 'avg_score', 'company_count').order_by('-avg_score')

    return Response({
        'total_companies': total_companies,
        'total_sectors': total_sectors,
        'avg_health_score': round(float(avg_score), 2) if avg_score else 0,
        'health_distribution': list(label_dist),
        'top_companies': [
            {
                'symbol': s.company.symbol,
                'company_name': s.company.company_name,
                'sector': s.company.sector.sector_name if s.company.sector else '',
                'score': float(s.overall_score),
                'label': s.health_label.label_name if s.health_label else '',
                'color': s.health_label.color_hex if s.health_label else '',
            }
            for s in top_companies
        ],
        'sector_performance': list(sector_perf),
    })


@api_view(['GET'])
def company_chart_data(request, symbol):
    """Return chart-ready time series data for a company."""
    pl = FactProfitLoss.objects.filter(
        company__symbol=symbol
    ).select_related('year').order_by('year__sort_order')

    bs = FactBalanceSheet.objects.filter(
        company__symbol=symbol
    ).select_related('year').order_by('year__sort_order')

    cf = FactCashFlow.objects.filter(
        company__symbol=symbol
    ).select_related('year').order_by('year__sort_order')

    return Response({
        'labels': [p.year.year_label for p in pl],
        'revenue': [float(p.sales or 0) for p in pl],
        'net_profit': [float(p.net_profit or 0) for p in pl],
        'operating_profit': [float(p.operating_profit or 0) for p in pl],
        'opm_pct': [float(p.opm_pct or 0) for p in pl],
        'npm_pct': [float(p.net_profit_margin_pct or 0) for p in pl],
        'eps': [float(p.eps or 0) for p in pl],
        'total_assets': [float(b.total_assets or 0) for b in bs],
        'debt_to_equity': [float(b.debt_to_equity or 0) for b in bs],
        'borrowings': [float(b.borrowings or 0) for b in bs],
        'operating_cf': [float(c.operating_activity or 0) for c in cf],
        'free_cf': [float(c.free_cash_flow or 0) for c in cf],
        'net_cf': [float(c.net_cash_flow or 0) for c in cf],
    })
