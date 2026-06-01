"""Dashboard Views — Server-side rendered pages."""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from warehouse.models import (
    DimCompany, DimSector, FactMLScore, FactProfitLoss,
    FactBalanceSheet, FactAnalysis, FactProsCons
)
from django.db.models import Avg, Count


def index(request):
    """Main dashboard — overview of all Nifty 100 companies."""
    return render(request, 'dashboard/index.html')


def company_detail(request, symbol):
    """Company detail page with full financial dashboard."""
    company = get_object_or_404(DimCompany, symbol=symbol)
    return render(request, 'dashboard/company_detail.html', {'company': company})


def sector_overview(request):
    """Sector performance overview page."""
    return render(request, 'dashboard/sector_overview.html')


def watchlist(request):
    """Watchlist page — shows user's pinned companies (stored client-side)."""
    return render(request, 'dashboard/watchlist.html')
