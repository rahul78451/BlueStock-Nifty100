"""
ML Scoring — Company Health Score Generator (v2)
==================================================
Scoring Dimensions (from Section 7.1):
  Profitability  25% — OPM%, net_profit_margin_pct, ROE (percentile rank, scaled 0-25)
  Revenue Growth 20% — 3Y compounded sales growth. Penalize <5%. Score 0-20.
  Leverage/Debt  20% — debt_to_equity (lower=better). D/E<0.1 = full 20. D/E>2 = 0.
  Cash Flow      15% — cash_conversion_ratio. >1.2 consistently = full 15.
  Dividend       10% — payout consistency over 5 years. Avg>30% for 5yrs = full 10.
  Growth Trend   10% — linear regression slope on sales+profit (last 5 years).

Labels: 85-100 EXCELLENT, 70-84 GOOD, 50-69 AVERAGE, 35-49 WEAK, 0-34 POOR

Usage: python analytics/ml_scoring.py
"""
import os
import sys
import django
import numpy as np
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from warehouse.models import (
    DimCompany, DimHealthLabel, FactProfitLoss,
    FactBalanceSheet, FactCashFlow, FactAnalysis, FactMLScore
)
from django.db.models import Avg, Max, Min


def percentile_rank(value, all_values):
    """Return percentile rank (0-100) of value within all_values."""
    if value is None or len(all_values) == 0:
        return 50.0
    below = sum(1 for v in all_values if v is not None and v < value)
    return (below / len(all_values)) * 100


def compute_profitability(company, all_opm, all_npm, all_roe):
    """Profitability (25%): OPM + NPM + ROE percentile."""
    pl = FactProfitLoss.objects.filter(company=company).order_by('-year__sort_order').first()
    opm = float(pl.opm_pct or 0) if pl else 0
    npm = float(pl.net_profit_margin_pct or 0) if pl else 0
    roe = float(company.roe_pct or 0)

    score = (
        percentile_rank(opm, all_opm) * 0.4 +
        percentile_rank(npm, all_npm) * 0.3 +
        percentile_rank(roe, all_roe) * 0.3
    )
    return min(25, score * 0.25)


def compute_growth(company):
    """Revenue Growth (20%): 3Y Sales CAGR. Penalize <5%."""
    analysis = FactAnalysis.objects.filter(
        company=company, period_label='3Y'
    ).first()
    if not analysis or analysis.compounded_sales_growth_pct is None:
        return 10.0  # neutral

    growth = float(analysis.compounded_sales_growth_pct)
    if growth >= 25:
        score = 20
    elif growth >= 15:
        score = 16
    elif growth >= 10:
        score = 13
    elif growth >= 5:
        score = 10
    elif growth >= 0:
        score = 5  # penalize <5%
    else:
        score = max(0, 5 + growth)  # negative growth
    return score


def compute_leverage(company):
    """Leverage (20%): D/E ratio. Lower=better. D/E<0.1=full 20. D/E>2=0."""
    bs = FactBalanceSheet.objects.filter(company=company).order_by('-year__sort_order').first()
    if not bs or bs.debt_to_equity is None:
        return 10.0

    de = float(bs.debt_to_equity)
    if de < 0.1:
        return 20.0
    elif de > 2.0:
        return 0.0
    else:
        return 20.0 * (1.0 - (de - 0.1) / 1.9)


def compute_cashflow(company):
    """Cash Flow (15%): cash_conversion_ratio = operating/net_profit. >1.2 = full 15."""
    pls = FactProfitLoss.objects.filter(company=company).order_by('-year__sort_order')[:5]
    cfs = FactCashFlow.objects.filter(company=company).order_by('-year__sort_order')[:5]

    ratios = []
    for p, c in zip(pls, cfs):
        np_val = float(p.net_profit or 0)
        op_val = float(c.operating_activity or 0)
        if np_val > 0:
            ratios.append(op_val / np_val)

    if not ratios:
        return 7.5

    avg_ratio = np.mean(ratios)
    consistently_good = sum(1 for r in ratios if r > 1.2)

    if consistently_good >= 3 and avg_ratio > 1.2:
        return 15.0
    elif avg_ratio > 1.0:
        return 12.0
    elif avg_ratio > 0.7:
        return 8.0
    elif avg_ratio > 0.3:
        return 4.0
    else:
        return 1.0


def compute_dividend(company):
    """Dividend (10%): Avg payout >30% for 5 consecutive years = full 10."""
    pls = FactProfitLoss.objects.filter(company=company).order_by('-year__sort_order')[:5]
    payouts = [float(p.dividend_payout_pct) for p in pls if p.dividend_payout_pct is not None]

    if not payouts:
        return 0.0

    avg_payout = np.mean(payouts)
    years_above_30 = sum(1 for p in payouts if p > 30)

    if years_above_30 >= 5 and avg_payout > 30:
        return 10.0
    elif years_above_30 >= 3:
        return 7.0
    elif avg_payout > 20:
        return 5.0
    elif avg_payout > 0:
        return 2.0
    else:
        return 0.0


def compute_trend(company):
    """Trend (10%): Linear regression slope on sales & profit (last 5 years)."""
    pls = list(FactProfitLoss.objects.filter(
        company=company
    ).order_by('-year__sort_order')[:5].values_list('sales', 'net_profit'))

    if len(pls) < 3:
        return 5.0

    pls.reverse()  # chronological order
    sales = [float(s or 0) for s, _ in pls]
    profits = [float(p or 0) for _, p in pls]
    x = np.arange(len(sales))

    sales_slope = np.polyfit(x, sales, 1)[0] if len(sales) >= 3 else 0
    profit_slope = np.polyfit(x, profits, 1)[0] if len(profits) >= 3 else 0

    avg_sales = np.mean(sales) if np.mean(sales) != 0 else 1
    norm_sales_slope = sales_slope / avg_sales
    avg_profit = np.mean(profits) if np.mean(profits) != 0 else 1
    norm_profit_slope = profit_slope / avg_profit

    combined = (norm_sales_slope + norm_profit_slope) / 2

    if combined > 0.1:  # accelerating
        return 10.0
    elif combined > 0.03:
        return 7.0
    elif combined > -0.03:
        return 5.0
    elif combined > -0.1:
        return 2.0
    else:
        return 0.0


def compute_scores():
    """Compute health scores for all companies."""
    print("🤖 Computing ML Health Scores (v2)...\n")

    companies = DimCompany.objects.all()
    labels = {l.label_name: l for l in DimHealthLabel.objects.all()}

    # Precompute global distributions for percentile ranking
    all_opm = list(FactProfitLoss.objects.order_by('-year__sort_order')
                   .values_list('opm_pct', flat=True)
                   .distinct()[:200])
    all_npm = list(FactProfitLoss.objects.order_by('-year__sort_order')
                   .values_list('net_profit_margin_pct', flat=True)
                   .distinct()[:200])
    all_roe = [float(c.roe_pct) for c in companies if c.roe_pct is not None]

    all_opm = [float(v) for v in all_opm if v is not None]
    all_npm = [float(v) for v in all_npm if v is not None]

    scores_computed = 0

    for company in companies:
        profitability = compute_profitability(company, all_opm, all_npm, all_roe)
        growth = compute_growth(company)
        leverage = compute_leverage(company)
        cashflow = compute_cashflow(company)
        dividend = compute_dividend(company)
        trend = compute_trend(company)

        overall = profitability + growth + leverage + cashflow + dividend + trend
        overall = round(min(100, max(0, overall)), 2)

        # Get health label
        if overall >= 85:
            label = labels.get('EXCELLENT')
        elif overall >= 70:
            label = labels.get('GOOD')
        elif overall >= 50:
            label = labels.get('AVERAGE')
        elif overall >= 35:
            label = labels.get('WEAK')
        else:
            label = labels.get('POOR')

        FactMLScore.objects.update_or_create(
            company=company,
            defaults={
                'overall_score': Decimal(str(overall)),
                'profitability_score': Decimal(str(round(profitability, 2))),
                'growth_score': Decimal(str(round(growth, 2))),
                'leverage_score': Decimal(str(round(leverage, 2))),
                'cashflow_score': Decimal(str(round(cashflow, 2))),
                'dividend_score': Decimal(str(round(dividend, 2))),
                'trend_score': Decimal(str(round(trend, 2))),
                'health_label': label,
            }
        )
        scores_computed += 1

    print(f"✅ Computed scores for {scores_computed} companies\n")

    # Summary
    for label_name in ['EXCELLENT', 'GOOD', 'AVERAGE', 'WEAK', 'POOR']:
        count = FactMLScore.objects.filter(health_label__label_name=label_name).count()
        print(f"  {label_name}: {count} companies")


if __name__ == '__main__':
    compute_scores()
