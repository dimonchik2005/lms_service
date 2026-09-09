from django.urls import path

from users.views import (
    PaymentListAPIView,
    UserListAPIView,
    UserRegistrationAPIView,
    UserRetrieveUpdateDestroyAPIView,
    StripePaymentCreateAPIView,
    StripePaymentStatusAPIView,
)

app_name = "users"

urlpatterns = [
    path(
        "",
        UserListAPIView.as_view(),
        name="user_list",
    ),
    path(
        "register/",
        UserRegistrationAPIView.as_view(),
        name="register",
    ),
    path(
        "payments/",
        PaymentListAPIView.as_view(),
        name="payment_list",
    ),
    path(
        "<int:pk>/",
        UserRetrieveUpdateDestroyAPIView.as_view(),
        name="user_detail",
    ),
    path(
        "payments/checkout/",
        StripePaymentCreateAPIView.as_view(),
        name="stripe_payment_create",
    ),
    path(
        "payments/<int:pk>/status/",
        StripePaymentStatusAPIView.as_view(),
        name="stripe_payment_status",
    ),
]
