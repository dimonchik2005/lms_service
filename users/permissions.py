from rest_framework.permissions import BasePermission


class IsCurrentUser(BasePermission):
    """Разрешает изменение и удаление только своего профиля."""

    message = "Можно изменять только собственный профиль."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.pk == request.user.pk