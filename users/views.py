from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import filters, generics, status
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Payment, User
from users.permissions import IsCurrentUser
from users.serializers import (
    PaymentSerializer,
    PublicUserSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    StripePaymentCreateSerializer,
)
from users.services import (
    StripeServiceError,
    create_checkout_session,
    create_stripe_price,
    create_stripe_product,
    retrieve_checkout_session,
)
from django.shortcuts import get_object_or_404


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


class StripePaymentCreateAPIView(APIView):
    """Создаёт оплату курса через Stripe."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание оплаты курса через Stripe",
        description=(
                "Создаёт продукт, цену и платёжную сессию "
                "Stripe. Возвращает данные платежа и ссылку."
        ),
        request=StripePaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(
                description="Некорректные данные.",
            ),
            401: OpenApiResponse(
                description="Пользователь не авторизован.",
            ),
            502: OpenApiResponse(
                description="Ошибка обращения к Stripe.",
            ),
        },
    )
    def post(self, request):
        serializer = StripePaymentCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        course = serializer.validated_data[
            "paid_course"
        ]
        amount = serializer.validated_data["amount"]

        payment = Payment.objects.create(
            user=request.user,
            paid_course=course,
            paid_lesson=None,
            amount=amount,
            payment_method=(
                Payment.PaymentMethod.STRIPE
            ),
            status=Payment.Status.PENDING,
        )

        try:
            stripe_product = create_stripe_product(
                course,
            )
            payment.stripe_product_id = (
                stripe_product.id
            )
            payment.save(
                update_fields=["stripe_product_id"],
            )

            stripe_price = create_stripe_price(
                product_id=stripe_product.id,
                amount=amount,
            )
            payment.stripe_price_id = stripe_price.id
            payment.save(
                update_fields=["stripe_price_id"],
            )

            stripe_session = create_checkout_session(
                price_id=stripe_price.id,
                payment_id=payment.pk,
            )
            payment.stripe_session_id = (
                stripe_session.id
            )
            payment.payment_link = stripe_session.url
            payment.save(
                update_fields=[
                    "stripe_session_id",
                    "payment_link",
                ],
            )

        except StripeServiceError as error:
            payment.status = Payment.Status.FAILED
            payment.save(
                update_fields=["status"],
            )

            return Response(
                {
                    "error": str(error),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_serializer = PaymentSerializer(
            payment,
            context={
                "request": request,
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class StripePaymentStatusAPIView(APIView):
    """Проверяет и обновляет статус Stripe-платежа."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверить статус Stripe-платежа",
        description=(
                "Проверяет платёжную сессию Stripe и "
                "синхронизирует статус локального платежа."
        ),
        responses={
            200: PaymentSerializer,
            401: OpenApiResponse(
                description="Пользователь не авторизован.",
            ),
            404: OpenApiResponse(
                description="Платёж не найден.",
            ),
            502: OpenApiResponse(
                description="Ошибка обращения к Stripe.",
            ),
        },
    )
    def get(self, request, pk):
        payments = Payment.objects.all()

        if not request.user.is_superuser:
            payments = payments.filter(
                user=request.user,
            )

        payment = get_object_or_404(
            payments,
            pk=pk,
        )

        if not payment.stripe_session_id:
            return Response(
                {
                    "error": (
                        "У платежа отсутствует "
                        "Stripe Session ID."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stripe_session = (
                retrieve_checkout_session(
                    payment.stripe_session_id,
                )
            )
        except StripeServiceError as error:
            return Response(
                {
                    "error": str(error),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if stripe_session.payment_status == "paid":
            payment.status = Payment.Status.PAID
        elif stripe_session.status == "expired":
            payment.status = Payment.Status.CANCELED
        else:
            payment.status = Payment.Status.PENDING

        payment.save(
            update_fields=["status"],
        )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )
