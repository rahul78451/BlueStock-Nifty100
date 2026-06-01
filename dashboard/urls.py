"""Dashboard URL Configuration"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('company/<str:symbol>/', views.company_detail, name='company-detail'),
    path('sectors/', views.sector_overview, name='sector-overview'),
]
