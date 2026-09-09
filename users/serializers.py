from rest_framework import serializers

from users.models import User
from decimal import Decimal
from rest_framework import serializers

from lms.serializers import (
    CourseSerializer,
    LessonSerializer,
)
from users.models import Payment, User
from lms.models import Course
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import IntegrityError, transaction


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор платежа с вложенными данными."""

    user_email = serializers.CharField(
        source="user.email",
        read_only=True,
    )

    paid_course = CourseSerializer(
        read_only=True,
    )

    paid_lesson = LessonSerializer(
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "user_email",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "status",
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "payment_link",
        )
        read_only_fields = (
            "user",
            "payment_date",
            "status",
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "payment_link",
        )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    payments = PaymentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "city",
            "avatar",
            "payments",
        )
        read_only_fields = (
            "id",
            "email",
            "payments",
        )


class PublicUserSerializer(serializers.ModelSerializer):
    """Общедоступные данные пользователя."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "city",
            "avatar",
        )
        read_only_fields = fields


class UserRegistrationSerializer(
    serializers.ModelSerializer,
):
    """Регистрирует пользователя и безопасно сохраняет пароль."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_repeat = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "city",
            "avatar",
            "password",
            "password_repeat",
        )
        read_only_fields = ("id",)

    def validate_email(self, value):
        """Проверяет отсутствие пользователя с такой почтой."""

        normalized_email = value.strip().lower()

        if User.objects.filter(
                email__iexact=normalized_email,
        ).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return normalized_email

    def validate(self, attrs):
        """Проверяет совпадение паролей."""

        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError(
                {
                    "password_repeat": (
                        "Введённые пароли не совпадают."
                    ),
                }
            )

        return attrs

    def create(self, validated_data):
        """Создаёт пользователя с хешированным паролем."""

        validated_data.pop("password_repeat")

        try:
            with transaction.atomic():
                return User.objects.create_user(
                    **validated_data,
                )
        except (IntegrityError, ValueError) as error:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Не удалось создать пользователя."
                    ),
                }
            ) from error


class StripePaymentCreateSerializer(
    serializers.Serializer
):
    """Данные для создания оплаты курса."""

    paid_course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        help_text="ID оплачиваемого курса",
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Сумма оплаты в рублях",
    )
