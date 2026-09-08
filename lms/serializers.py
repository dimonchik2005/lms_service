from rest_framework import serializers

from lms.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        model = Lesson
        fields = (
            "id",
            "owner",
            "course",
            "title",
            "description",
            "preview",
            "video_url",
        )
        read_only_fields = (
            "id",
            "owner",
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
            "owner",
            "title",
            "preview",
            "description",
            "lesson_count",
            "lessons",
        )
        read_only_fields = (
            "id",
            "owner",
        )

    def get_lesson_count(self, obj):
        """Возвращает количество уроков курса."""

        return obj.lessons.count()