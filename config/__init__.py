# config package
# Load Celery app so that @shared_task decorators work (if celery is installed)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed — skip (Django will still work without background tasks)
    pass
