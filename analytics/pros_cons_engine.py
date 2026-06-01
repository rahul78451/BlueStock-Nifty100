"""
Auto Pros & Cons Rule Engine (Section 7.2)
============================================
Generates strengths and concerns per company based on financial rules.

Pros Rules:
  - D/E < 0.1 → "Company is almost debt free."
  - 3Y ROE > 20% → good ROE track record
  - Dividend payout > 30% for 5 years → healthy dividend
  - 10Y sales CAGR > 15% → strong long-term growth
  - OPM improved 3 consecutive years → improving margins
  - OCF > net profit for 3 years → strong cash conversion
  - 3Y profit CAGR > 15% → profit growth accelerated

Cons Rules:
  - 5Y sales CAGR < 10% → below-average growth
  - Borrowings increased > 1.5x in latest year → debt spike
  - OPM declining 3 consecutive years → declining margins
  - D/E > 1.5 → high leverage
  - Net profit - OCF > 0.3 * net profit → earnings quality concern
  - Interest coverage < 2 → debt repayment risk

Usage: python analytics/pros_cons_engine.py
"""
import os
import sys
import django
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from warehouse.models import (
    DimCompany, FactProfitLoss, FactBalanceSheet,
    FactCashFlow, FactAnalysis, FactProsCons
)


def generate_pros_cons():
    """Generate pros and cons for all companies using financial rules."""
    print("📊 Generating Pros & Cons (Rule Engine)...\n")

    # Clear existing ML-generated entries
    deleted, _ = FactProsCons.objects.filter(source='ML').delete()
    print(f"  Cleared {deleted} previous ML-generated entries")

    companies = DimCompany.objects.all()
    total_pros = 0
    total_cons = 0

    for company in companies:
        pros = []
        cons = []

        # Get financial data
        pls = list(FactProfitLoss.objects.filter(
            company=company
        ).order_by('-year__sort_order')[:5])

        bs_latest = FactBalanceSheet.objects.filter(
            company=company
        ).order_by('-year__sort_order').first()

        bs_prev = FactBalanceSheet.objects.filter(
            company=company
        ).order_by('-year__sort_order')[1:2].first() if FactBalanceSheet.objects.filter(company=company).count() > 1 else None

        cfs = list(FactCashFlow.objects.filter(
            company=company
        ).order_by('-year__sort_order')[:5])

        analysis_3y = FactAnalysis.objects.filter(
            company=company, period_label='3Y'
        ).first()

        analysis_5y = FactAnalysis.objects.filter(
            company=company, period_label='5Y'
        ).first()

        analysis_10y = FactAnalysis.objects.filter(
            company=company, period_label='10Y'
        ).first()

        # ── PRO RULES ──

        # 1. D/E < 0.1 → debt free
        if bs_latest and bs_latest.debt_to_equity is not None:
            de = float(bs_latest.debt_to_equity)
            if de < 0.1:
                pros.append(("Leverage", "Company is almost debt free."))

        # 2. 3Y ROE > 20%
        if analysis_3y and analysis_3y.roe_pct is not None:
            roe_3y = float(analysis_3y.roe_pct)
            if roe_3y > 20:
                pros.append(("Profitability",
                    f"Company has a good return on equity (ROE) track record: 3 Years ROE {roe_3y:.1f}%"))

        # 3. Dividend payout > 30% for 5 years
        if len(pls) >= 5:
            payouts = [float(p.dividend_payout_pct or 0) for p in pls[:5]]
            avg_payout = np.mean(payouts)
            years_above_30 = sum(1 for p in payouts if p > 30)
            if years_above_30 >= 5 and avg_payout > 30:
                pros.append(("Dividend",
                    f"Company has been maintaining a healthy dividend payout of {avg_payout:.1f}%"))

        # 4. 10Y sales CAGR > 15%
        if analysis_10y and analysis_10y.compounded_sales_growth_pct is not None:
            cagr_10y = float(analysis_10y.compounded_sales_growth_pct)
            if cagr_10y > 15:
                pros.append(("Growth",
                    f"Strong long-term revenue growth of {cagr_10y:.1f}% CAGR over 10 years"))

        # 5. OPM improved 3 consecutive years
        if len(pls) >= 4:
            opms = [float(p.opm_pct or 0) for p in pls[:4]]
            opms.reverse()  # chronological
            if len(opms) >= 4 and all(opms[i+1] > opms[i] for i in range(3)):
                pros.append(("Profitability",
                    "Improving operating margins consistently for 3 years"))

        # 6. OCF > net profit for 3 consecutive years
        if len(pls) >= 3 and len(cfs) >= 3:
            ocf_exceeds = 0
            for p, c in zip(pls[:3], cfs[:3]):
                np_val = float(p.net_profit or 0)
                ocf_val = float(c.operating_activity or 0)
                if np_val > 0 and ocf_val > np_val:
                    ocf_exceeds += 1
            if ocf_exceeds >= 3:
                pros.append(("Cash Flow",
                    "Strong cash conversion — OCF exceeds reported profits"))

        # 7. 3Y profit CAGR > 15%
        if analysis_3y and analysis_3y.compounded_profit_growth_pct is not None:
            profit_cagr = float(analysis_3y.compounded_profit_growth_pct)
            if profit_cagr > 15:
                pros.append(("Growth",
                    f"Profit growth accelerated significantly at {profit_cagr:.1f}% CAGR"))

        # ── CON RULES ──

        # 1. 5Y sales CAGR < 10%
        if analysis_5y and analysis_5y.compounded_sales_growth_pct is not None:
            cagr_5y = float(analysis_5y.compounded_sales_growth_pct)
            if cagr_5y < 10:
                cons.append(("Growth",
                    "Below-average sales growth over past five years"))

        # 2. Borrowings increased > 1.5x
        if bs_latest and bs_prev:
            curr_borr = float(bs_latest.borrowings or 0)
            prev_borr = float(bs_prev.borrowings or 1)
            if prev_borr > 0 and curr_borr > prev_borr * 1.5:
                cons.append(("Leverage",
                    "Borrowings have increased significantly in the recent year"))

        # 3. OPM declining 3 consecutive years
        if len(pls) >= 4:
            opms = [float(p.opm_pct or 0) for p in pls[:4]]
            opms.reverse()
            if len(opms) >= 4 and all(opms[i+1] < opms[i] for i in range(3)):
                cons.append(("Profitability",
                    "Operating margins have been declining for three consecutive years"))

        # 4. D/E > 1.5
        if bs_latest and bs_latest.debt_to_equity is not None:
            de = float(bs_latest.debt_to_equity)
            if de > 1.5:
                cons.append(("Leverage",
                    "Stock carries high debt — leverage levels require monitoring"))

        # 5. Earnings quality concern
        if len(pls) >= 1 and len(cfs) >= 1:
            np_val = float(pls[0].net_profit or 0)
            ocf_val = float(cfs[0].operating_activity or 0)
            if np_val > 0 and (np_val - ocf_val) > 0.3 * np_val:
                cons.append(("Cash Flow",
                    "Earnings quality concern — reported profits exceed actual cash generation"))

        # 6. Interest coverage < 2
        if pls and pls[0].interest_coverage is not None:
            ic = float(pls[0].interest_coverage)
            if ic < 2:
                cons.append(("Leverage",
                    "Low interest coverage ratio — debt repayment risk"))

        # Save to database
        for category, text in pros:
            FactProsCons.objects.create(
                company=company, is_pro=True,
                category=category, text=text,
                source='ML', confidence=Decimal('0.85')
            )
            total_pros += 1

        for category, text in cons:
            FactProsCons.objects.create(
                company=company, is_pro=False,
                category=category, text=text,
                source='ML', confidence=Decimal('0.80')
            )
            total_cons += 1

    print(f"\n✅ Generated {total_pros} pros and {total_cons} cons for {companies.count()} companies")


if __name__ == '__main__':
    from decimal import Decimal
    generate_pros_cons()
