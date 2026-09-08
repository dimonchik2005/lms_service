from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework import filters, generics
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
)

from users.models import Payment, User
from users.permissions import IsCurrentUser
from users.serializers import (
    PaymentSerializer,
    PublicUserSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class UserRegistrationAPIView(
    generics.CreateAPIView,
):
    """Регистрирует пользователя без JWT."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)


class UserListAPIView(generics.ListAPIView):
    """Выводит общедоступные профили."""

    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated,)


class UserRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView,
):
    """Просматривает профиль и управляет своим профилем."""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.kwargs.get("pk") == self.request.user.pk:
            return UserSerializer

        return PublicUserSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = (
                IsAuthenticated,
            )
        else:
            permission_classes = (
                IsAuthenticated,
                IsCurrentUser,
            )

        return [
            permission()
            for permission in permission_classes
        ]


class PaymentListAPIView(generics.ListAPIView):
    """Выводит платежи текущего пользователя."""

    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

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

    def get_queryset(self):
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
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(
            user=self.request.user,
        )