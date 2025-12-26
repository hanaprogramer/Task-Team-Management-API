import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_name.settings')

app = Celery('project_name')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'deactivate-inactive-users-daily': {
        'task': 'apps.users.tasks.deactivate_inactive_users',
        'schedule': crontab(hour=0, minute=0),  # هر روز ساعت ۰۰:۰۰
    },
}