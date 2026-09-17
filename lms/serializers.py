from rest_framework import serializers
from lms.models import Course, Lesson
from lms.validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    video_url = serializers.URLField(
        validators=[validate_youtube_url],
    )

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
    is_subscribed = serializers.SerializerMethodField()

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
            "is_subscribed",
        )
        read_only_fields = (
            "id",
            "owner",
        )

    def get_lesson_count(self, obj):
        """Возвращает количество уроков курса."""

        return obj.lessons.count()

    def get_is_subscribed(self, obj) -> bool:
        request = self.context.get("request")

        if (
                request is None
                or not request.user.is_authenticated
        ):
            return False

        return obj.subscriptions.filter(
            user=request.user,
        ).exists()


class SubscriptionToggleRequestSerializer(
    serializers.Serializer
):
    """Данные для добавления или удаления подписки."""

    course_id = serializers.IntegerField(
        min_value=1,
        help_text="ID курса",
    )


class SubscriptionToggleResponseSerializer(
    serializers.Serializer
):
    """Результат изменения подписки."""

    message = serializers.CharField()
    is_subscribed = serializers.BooleanField()
