from celery import shared_task
from django.conf import settings
from django.core.mail import send_mass_mail

from lms.models import Course


@shared_task
def send_course_update_email(
    course_id: int,
) -> int:
    """Отправляет уведомления подпис подписчикам курса."""

    course = Course.objects.get(pk=course_id)

    recipient_emails = list(
        course.subscriptions.filter(
            user__is_active=True,
        )
        .exclude(
            user__email="",
        )
        .values_list(
            "user__email",
            flat=True,
        )
        .distinct()
    )

    if not recipient_emails:
        return 0

    subject = (
        f"Обновление курса «{course.title}»"
    )
    message = (
        f"Курс «{course.title}» был обновлён.\n\n"
        "Откройте LMS, чтобы посмотреть изменения."
    )

    email_messages = tuple(
        (
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        for email in recipient_emails
    )

    return send_mass_mail(
        email_messages,
        fail_silently=False,
    )