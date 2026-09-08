from django.db import models
from django.conf import settings


class Course(models.Model):
    """Учебный курс."""

    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    preview = models.ImageField(
        upload_to="courses/previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class Lesson(models.Model):
    """Урок, входящий в учебный курс."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    preview = models.ImageField(
        upload_to="lessons/previews/",
        blank=True,
        null=True,
        verbose_name="Превью",
    )
    video_url = models.URLField(
        verbose_name="Ссылка на видео",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        null=True,
        blank=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = (
            "course",
            "title",
        )

    def __str__(self) -> str:
        return self.title


class Subscription(models.Model):
    """Подписка пользователя на обновления курса."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Пользователь",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Курс",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "user",
                    "course",
                ),
                name="unique_user_course_subscription",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"{self.course.title}"
        )