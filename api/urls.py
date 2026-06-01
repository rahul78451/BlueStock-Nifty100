"""API URL Configuration"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sectors', views.SectorViewSet, basename='sector')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'profit-loss', views.ProfitLossViewSet, basename='profit-loss')
router.register(r'balance-sheets', views.BalanceSheetViewSet, basename='balance-sheet')
router.register(r'cash-flows', views.CashFlowViewSet, basename='cash-flow')
router.register(r'ml-scores', views.MLScoreViewSet, basename='ml-score')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('companies/<str:symbol>/chart-data/', views.company_chart_data, name='company-chart-data'),
]
