from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from lms.models import Course, Lesson
from lms.permissions import (
    MODERATOR_GROUP_NAME,
    IsModerator,
    IsOwner,
)
from lms.serializers import (
    CourseSerializer,
    LessonSerializer,
)


def user_is_moderator(user):
    """Проверяет принадлежность пользователя к модераторам."""

    return user.groups.filter(
        name=MODERATOR_GROUP_NAME,
    ).exists()


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курсов с разграничением доступа."""

    serializer_class = CourseSerializer

    def get_queryset(self):
        queryset = (
            Course.objects
            .prefetch_related("lessons")
            .all()
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        if self.action == "create":
            permission_classes = (
                IsAuthenticated,
                ~IsModerator,
            )

        elif self.action == "destroy":
            permission_classes = (
                IsAuthenticated,
                ~IsModerator,
                IsOwner,
            )

        elif self.action in (
            "retrieve",
            "update",
            "partial_update",
        ):
            permission_classes = (
                IsAuthenticated,
                IsModerator | IsOwner,
            )

        else:
            permission_classes = (
                IsAuthenticated,
            )

        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
        )


class LessonListCreateAPIView(
    generics.ListCreateAPIView,
):
    """Список и создание уроков."""

    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.select_related(
            "course",
            "owner",
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = (
                IsAuthenticated,
                ~IsModerator,
            )
        else:
            permission_classes = (
                IsAuthenticated,
            )

        return [
            permission()
            for permission in permission_classes
        ]

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]

        if course.owner_id != self.request.user.id:
            raise PermissionDenied(
                "Нельзя добавить урок в чужой курс."
            )

        serializer.save(
            owner=self.request.user,
        )


class LessonRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView,
):
    """Просмотр, изменение и удаление урока."""

    serializer_class = LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.select_related(
            "course",
            "owner",
        )

        if user_is_moderator(self.request.user):
            return queryset

        return queryset.filter(
            owner=self.request.user,
        )

    def get_permissions(self):
        if self.request.method == "DELETE":
            permission_classes = (
                IsAuthenticated,
                ~IsModerator,
                IsOwner,
            )
        else:
            permission_classes = (
                IsAuthenticated,
                IsModerator | IsOwner,
            )

        return [
            permission()
            for permission in permission_classes
        ]