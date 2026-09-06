from rest_framework import serializers

from lms.models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    """Преобразует курсы между моделью и JSON."""

    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    """Преобразует уроки между моделью и JSON."""

    class Meta:
        model = Lesson
        fields = "__all__"