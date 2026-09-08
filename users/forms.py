from django.contrib.auth.forms import (
    UserChangeForm,
    UserCreationForm,
)

from users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Создание пользователя в административной панели."""

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
        )


class CustomUserChangeForm(UserChangeForm):
    """Редактирование пользователя в админке."""

    class Meta:
        model = User
        fields = "__all__"