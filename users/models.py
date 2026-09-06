from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from users.managers import UserManager


class User(
    AbstractBaseUser,
    PermissionsMixin,
):
    """Пользователь LMS-платформы."""

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Фамилия",
    )
    phone = models.CharField(
        max_length=35,
        blank=True,
        verbose_name="Телефон",
    )
    city = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Город",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Сотрудник",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата регистрации",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        """Возвращает полное имя пользователя."""

        return (
            f"{self.first_name} {self.last_name}"
        ).strip()

    def get_short_name(self) -> str:
        """Возвращает короткое имя пользователя."""

        return self.first_name or self.email