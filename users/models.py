from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
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


class Payment(models.Model):
    """Платёж пользователя за курс или отдельный урок."""

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Наличные"
        TRANSFER = "transfer", "Перевод на счёт"
        STRIPE = "stripe", "Stripe"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачено"
        FAILED = "failed", "Ошибка оплаты"
        CANCELED = "canceled", "Оплата отменена"


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Пользователь",
    )

    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата оплаты",
    )

    paid_course = models.ForeignKey(
        "lms.Course",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный курс",
    )

    paid_lesson = models.ForeignKey(
        "lms.Lesson",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный урок",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты",
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name="Способ оплаты",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус платежа",
    )

    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID продукта Stripe",
    )

    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID цены Stripe",
    )

    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID сессии Stripe",
    )

    payment_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ссылка на оплату",
    )

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ("-payment_date",)
        constraints = [
            models.CheckConstraint(
                condition=(
                        models.Q(
                            paid_course__isnull=False,
                            paid_lesson__isnull=True,
                        )
                        | models.Q(
                    paid_course__isnull=True,
                    paid_lesson__isnull=False,
                )
                ),
                name="payment_has_exactly_one_item",
            ),
        ]

    def clean(self):
        """Проверяет, что оплачен курс или урок, но не оба."""

        super().clean()

        if bool(self.paid_course) == bool(self.paid_lesson):
            raise ValidationError(
                "Необходимо выбрать либо курс, либо урок."
            )

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"{self.amount} руб."
        )
