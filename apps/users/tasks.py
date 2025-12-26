from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import User

@shared_task
def deactivate_inactive_users(days_inactive=30):
    """
    غیرفعال کردن کاربرانی که به مدت مشخص لاگین نکرده‌اند
    """
    cutoff_date = timezone.now() - timedelta(days=days_inactive)
    users_to_deactivate = User.objects.filter(is_active=True, last_login__lt=cutoff_date)
    
    for user in users_to_deactivate:
        user.is_active = False
        user.save()
