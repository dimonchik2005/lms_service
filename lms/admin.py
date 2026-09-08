from django.contrib import admin

from lms.models import Course, Lesson, Subscription


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Управление курсами."""

    list_display = (
        "id",
        "title",
    )
    search_fields = (
        "title",
        "description",
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Управление уроками."""

    list_display = (
        "id",
        "title",
        "course",
        "video_url",
    )
    list_filter = ("course",)
    search_fields = (
        "title",
        "description",
    )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Отображение подписок в административной панели."""

    list_display = (
        "id",
        "user",
        "course",
    )

    search_fields = (
        "user__email",
        "course__title",
    )