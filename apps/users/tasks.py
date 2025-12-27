from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import User

@shared_task
def deactivate_inactive_users(days_inactive=30):
    cutoff_date = timezone.now() - timedelta(days=days_inactive)
    User.objects.filter(
        is_active=True,
        last_login__lt=cutoff_date
    ).update(is_active=False)

