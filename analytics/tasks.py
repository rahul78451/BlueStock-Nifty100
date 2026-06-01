"""
Celery Tasks — BlueStock Analytics Pipeline (Section 7.3)
==========================================================
Task                   | Schedule         | Action
run_etl_pipeline       | Daily 1:00 AM    | Run ETL scripts 2 and 3
score_all_companies    | Daily 2:00 AM    | Recalculate health scores
generate_pros_cons     | Daily 2:30 AM    | Re-run pros/cons rule engine
detect_anomalies       | Weekly Sunday    | Z-score anomaly detection
detect_trends          | Weekly Sunday    | Linear regression trend analysis
invalidate_cache       | After score tasks| Clear Redis cache
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

from config.celery import app

logger = logging.getLogger(__name__)
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


@app.task(bind=True, name='analytics.tasks.run_etl_pipeline')
def run_etl_pipeline(self):
    """Run ETL scripts 2 (clean & transform) and 3 (load to warehouse)."""
    logger.info("🔄 Starting ETL pipeline...")
    try:
        # Step 2: Clean and transform
        result2 = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, 'etl', '02_clean_and_transform.py')],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=600
        )
        logger.info(f"ETL Step 2: {result2.stdout[-500:] if result2.stdout else 'OK'}")
        if result2.returncode != 0:
            logger.error(f"ETL Step 2 failed: {result2.stderr}")

        # Step 3: Load to warehouse
        result3 = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, 'etl', '03_load_to_warehouse.py')],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=600
        )
        logger.info(f"ETL Step 3: {result3.stdout[-500:] if result3.stdout else 'OK'}")
        if result3.returncode != 0:
            logger.error(f"ETL Step 3 failed: {result3.stderr}")

        return f"ETL pipeline complete. Step2 rc={result2.returncode}, Step3 rc={result3.returncode}"
    except Exception as e:
        logger.error(f"ETL pipeline error: {e}")
        raise self.retry(exc=e, max_retries=2, countdown=300)


@app.task(bind=True, name='analytics.tasks.score_all_companies')
def score_all_companies(self):
    """Recalculate ML health scores for all companies."""
    logger.info("🤖 Starting health score computation...")
    try:
        from analytics.ml_scoring import compute_scores
        compute_scores()

        # Invalidate cache after scoring
        invalidate_cache.delay()

        return "Health scores computed successfully"
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        raise self.retry(exc=e, max_retries=2, countdown=120)


@app.task(bind=True, name='analytics.tasks.generate_pros_cons')
def generate_pros_cons(self):
    """Re-run the pros/cons rule engine for all companies."""
    logger.info("📊 Starting pros/cons generation...")
    try:
        from analytics.pros_cons_engine import generate_pros_cons as run_engine
        run_engine()

        invalidate_cache.delay()

        return "Pros/Cons generated successfully"
    except Exception as e:
        logger.error(f"Pros/Cons error: {e}")
        raise self.retry(exc=e, max_retries=2, countdown=120)


@app.task(bind=True, name='analytics.tasks.detect_anomalies')
def detect_anomalies(self):
    """Z-score anomaly detection across all fact tables."""
    logger.info("🔍 Starting anomaly detection...")
    try:
        import django
        django.setup()

        import numpy as np
        from scipy import stats
        from warehouse.models import FactProfitLoss, FactBalanceSheet

        anomaly_count = 0
        threshold = 2.5

        # P&L anomalies
        for metric in ['sales', 'net_profit', 'operating_profit']:
            companies = FactProfitLoss.objects.values_list(
                'company_id', flat=True
            ).distinct()
            for symbol in companies:
                values = list(FactProfitLoss.objects.filter(
                    company_id=symbol
                ).order_by('year__sort_order').values_list(metric, flat=True))
                values = [float(v) for v in values if v is not None]
                if len(values) < 4:
                    continue
                z = np.abs(stats.zscore(values))
                anomaly_count += sum(1 for z_val in z if z_val > threshold)

        logger.info(f"Detected {anomaly_count} anomalies across P&L tables")
        return f"Anomaly detection complete: {anomaly_count} flags"
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise self.retry(exc=e, max_retries=1, countdown=300)


@app.task(bind=True, name='analytics.tasks.detect_trends')
def detect_trends(self):
    """Linear regression trend analysis for all companies."""
    logger.info("📈 Starting trend analysis...")
    try:
        import django
        django.setup()

        import numpy as np
        from scipy import stats
        from warehouse.models import FactProfitLoss

        trend_counts = {'UP': 0, 'FLAT': 0, 'DOWN': 0}

        companies = FactProfitLoss.objects.values_list(
            'company_id', flat=True
        ).distinct()

        for symbol in companies:
            sales = list(FactProfitLoss.objects.filter(
                company_id=symbol
            ).order_by('-year__sort_order')[:5].values_list('sales', flat=True))
            sales = [float(v) for v in sales if v is not None]
            sales.reverse()

            if len(sales) < 3:
                continue

            x = np.arange(len(sales))
            slope, _, _, _, _ = stats.linregress(x, sales)
            avg = np.mean(sales) if np.mean(sales) != 0 else 1
            norm_slope = slope / avg

            if norm_slope > 0.05:
                trend_counts['UP'] += 1
            elif norm_slope < -0.05:
                trend_counts['DOWN'] += 1
            else:
                trend_counts['FLAT'] += 1

        logger.info(f"Trends: {trend_counts}")
        return f"Trend analysis complete: {trend_counts}"
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise self.retry(exc=e, max_retries=1, countdown=300)


@app.task(name='analytics.tasks.invalidate_cache')
def invalidate_cache():
    """Clear Redis cache for changed company data."""
    try:
        from django.conf import settings
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL)
        keys = r.keys('bluestock:*')
        if keys:
            r.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache keys")
        else:
            logger.info("No cache keys to clear")
        return f"Cache cleared: {len(keys)} keys"
    except Exception as e:
        logger.warning(f"Cache invalidation skipped (Redis may not be running): {e}")
        return "Cache invalidation skipped"
