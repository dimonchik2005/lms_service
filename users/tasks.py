from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone


@shared_task
def deactivate_inactive_users() -> int:
    """Блокирует пользователей, не входивших больше месяца."""

    user_model = get_user_model()

    inactivity_limit = (
        timezone.now() - timedelta(days=30)
    )

    updated_count = (
        user_model.objects.filter(
            is_active=True,
            is_superuser=False,
            last_login__lt=inactivity_limit,
        ).update(
            is_active=False,
        )
    )

    return updated_count