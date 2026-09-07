from rest_framework import serializers

from users.models import User

from rest_framework import serializers

from lms.serializers import (
    CourseSerializer,
    LessonSerializer,
)
from users.models import Payment, User


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
