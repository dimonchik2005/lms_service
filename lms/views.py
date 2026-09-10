from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from lms.models import Course, Lesson, Subscription
from lms.permissions import (
    MODERATOR_GROUP_NAME,
    IsModerator,
    IsOwner,
)
from lms.serializers import (
    CourseSerializer,
    LessonSerializer,
    SubscriptionToggleRequestSerializer,
    SubscriptionToggleResponseSerializer,
)
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from lms.paginators import LMSPagination
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from lms.tasks import send_course_update_email


def user_is_moderator(user):
    """Проверяет принадлежность пользователя к модераторам."""

    return user.groups.filter(
        name=MODERATOR_GROUP_NAME,
    ).exists()


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курсов с разграничением доступа."""

    serializer_class = CourseSerializer
    pagination_class = LMSPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

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

    def perform_update(self, serializer):
        course_before_update = self.get_object()
        previous_updated_at = (
            course_before_update.updated_at
        )

        course = serializer.save()

        four_hours_passed = (
                previous_updated_at is None
                or timezone.now() - previous_updated_at
                >= timedelta(hours=4)
        )

        if four_hours_passed:
            transaction.on_commit(
                lambda: send_course_update_email.delay(
                    course.pk,
                )
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
    pagination_class = LMSPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

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


class SubscriptionToggleAPIView(APIView):
    """Добавляет или удаляет подписку на курс."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Добавить или удалить подписку",
        description=(
                "Если подписки пользователя на курс нет, "
                "она создаётся. Если подписка уже существует, "
                "она удаляется."
        ),
        request=SubscriptionToggleRequestSerializer,
        responses={
            200: SubscriptionToggleResponseSerializer,
            201: SubscriptionToggleResponseSerializer,
            400: OpenApiResponse(
                description="Не указан или некорректен ID курса.",
            ),
            401: OpenApiResponse(
                description="Пользователь не авторизован.",
            ),
            404: OpenApiResponse(
                description="=Курс не найден."
            ),
        },
    )
    def post(self, request):
        serializer = SubscriptionToggleRequestSerializer(
            data=request.data,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Необходимо передать ID курса.",
                    "is_subscribed": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        course_id = serializer.validated_data[
            "course_id"
        ]

        course = get_object_or_404(
            Course,
            pk=course_id,
        )

        subscription, created = (
            Subscription.objects.get_or_create(
                user=request.user,
                course=course,
            )
        )

        if created:
            return Response(
                {
                    "message": "Подписка добавлена",
                    "is_subscribed": True,
                },
                status=status.HTTP_201_CREATED,
            )

        subscription.delete()

        return Response(
            {
                "message": "Подписка удалена",
                "is_subscribed": False,
            },
            status=status.HTTP_200_OK,
        )
