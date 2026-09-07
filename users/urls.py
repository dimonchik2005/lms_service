from django.urls import path

from users.views import (UserRetrieveUpdateAPIView, PaymentListAPIView)

app_name = "users"

urlpatterns = [
    path(
        "payments/",
        PaymentListAPIView.as_view(),
        name="payment_list",
    ),
    path(
        "<int:pk>/",
        UserRetrieveUpdateAPIView.as_view(),
        name="user_detail_update",
    ),
]
