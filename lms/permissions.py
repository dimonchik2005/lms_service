from rest_framework.permissions import BasePermission


MODERATOR_GROUP_NAME = "Модераторы"


class IsModerator(BasePermission):
    """Проверяет принадлежность пользователя к модераторам."""

    message = "Действие доступно только модератору."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(
                name=MODERATOR_GROUP_NAME,
            ).exists()
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return self.has_permission(
            request,
            view,
        )


class IsOwner(BasePermission):
    """Разрешает действие только владельцу объекта."""

    message = "Вы не являетесь владельцем объекта."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return (
            obj.owner_id
            == request.user.id
        )