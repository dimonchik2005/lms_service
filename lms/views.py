from rest_framework import generics, viewsets

from lms.models import Course, Lesson
from lms.serializers import (
    CourseSerializer,
    LessonSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курсов."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonListCreateAPIView(
    generics.ListCreateAPIView,
):
    """Получение списка и создание уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView,
):
    """Просмотр, изменение и удаление одного урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
