from rest_framework import generics

from users.models import User, Payment
from users.serializers import UserSerializer, PaymentSerializer

from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework import filters, generics



class UserRetrieveUpdateAPIView(
    generics.RetrieveUpdateAPIView,
):
    """Просмотр и редактирование профиля пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

class PaymentListAPIView(generics.ListAPIView):
    """Выводит список платежей с фильтрацией."""

    queryset = (
        Payment.objects
        .select_related(
            "user",
            "paid_course",
            "paid_lesson",
        )
        .prefetch_related(
            "paid_course__lessons",
        )
        .all()
    )

    serializer_class = PaymentSerializer

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    filterset_fields = (
        "paid_course",
        "paid_lesson",
        "payment_method",
    )

    ordering_fields = (
        "payment_date",
    )

    ordering = (
        "-payment_date",
    )