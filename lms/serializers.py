from rest_framework import serializers

from lms.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        model = Lesson
        fields = (
            "id",
            "course",
            "title",
            "description",
            "preview",
            "video_url",
        )


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса."""

    lesson_count = serializers.SerializerMethodField()

    lessons = LessonSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "lesson_count",
            "lessons",
        )

    def get_lesson_count(self, obj):
        """Возвращает количество уроков курса."""

        return obj.lessons.count()