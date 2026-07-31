"""
Celery configuration for My Hope Story project.
Handles async tasks, scheduled jobs, and background processing.
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhopestory.settings')

# Create Celery app
app = Celery('myhopestory')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all apps
app.autodiscover_tasks()

# ===========================
# Celery Beat Schedule (Periodic Tasks)
# ===========================

app.conf.beat_schedule = {
    # Send pending email notifications every 5 minutes
    'send-pending-notifications': {
        'task': 'notifications.tasks.send_pending_notifications',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Generate daily analytics reports at 2 AM
    'generate-daily-analytics': {
        'task': 'analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Clean up old notifications monthly
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),  # 1st of month at 3 AM
    },
    # Update recommendation cache
    'update-recommendations': {
        'task': 'search.tasks.update_recommendation_cache',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    # Process moderation queue
    'process-moderation-queue': {
        'task': 'moderation.tasks.process_flagged_content',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    # Generate weekly investor reports
    'generate-weekly-reports': {
        'task': 'analytics.tasks.generate_weekly_investor_report',
        'schedule': crontab(day_of_week=1, hour=6, minute=0),  # Monday at 6 AM
    },
}

# Configure Celery settings
app.conf.update(
    # Task configuration
    CELERY_TASK_TIME_LIMIT=30 * 60,  # 30 minutes hard limit
    CELERY_TASK_SOFT_TIME_LIMIT=25 * 60,  # 25 minutes soft limit
    CELERY_TASK_TRACK_STARTED=True,
    CELERY_TASK_TIME_EXPIRES=3600,  # 1 hour
    CELERY_TASK_REJECT_ON_WORKER_LOST=True,
    
    # Worker configuration
    CELERY_WORKER_PREFETCH_MULTIPLIER=4,
    CELERY_WORKER_MAX_TASKS_PER_CHILD=1000,
    
    # Result backend
    CELERY_RESULT_EXPIRES=3600,  # 1 hour
    
    # Timezone
    CELERY_TIMEZONE=settings.TIME_ZONE,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
