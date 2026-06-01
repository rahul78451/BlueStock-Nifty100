"""
Celery Application Configuration
==================================
Celery app for BlueStock background analytics tasks.
Broker: Redis (via REDIS_URL environment variable)
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('bluestock')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['analytics'])

# ─── Section 7.3: Celery Scheduled Tasks ───
app.conf.beat_schedule = {
    # Run ETL pipeline daily at 1:00 AM IST
    'run-etl-pipeline': {
        'task': 'analytics.tasks.run_etl_pipeline',
        'schedule': crontab(hour=1, minute=0),
    },
    # Recalculate health scores daily at 2:00 AM IST
    'score-all-companies': {
        'task': 'analytics.tasks.score_all_companies',
        'schedule': crontab(hour=2, minute=0),
    },
    # Re-run pros/cons rule engine daily at 2:30 AM IST
    'generate-pros-cons': {
        'task': 'analytics.tasks.generate_pros_cons',
        'schedule': crontab(hour=2, minute=30),
    },
    # Z-score anomaly detection weekly on Sunday at 3:00 AM
    'detect-anomalies': {
        'task': 'analytics.tasks.detect_anomalies',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),
    },
    # Trend analysis weekly on Sunday at 3:30 AM
    'detect-trends': {
        'task': 'analytics.tasks.detect_trends',
        'schedule': crontab(hour=3, minute=30, day_of_week='sunday'),
    },
}

app.conf.timezone = 'Asia/Kolkata'
