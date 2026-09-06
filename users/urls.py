from django.urls import path

from users.views import UserRetrieveUpdateAPIView


app_name = "users"

urlpatterns = [
    path(
        "<int:pk>/",
        UserRetrieveUpdateAPIView.as_view(),
        name="user_detail_update",
    ),
]