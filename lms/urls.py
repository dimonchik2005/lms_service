from django.urls import include, path
from rest_framework.routers import DefaultRouter

from lms.views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
    SubscriptionToggleAPIView,
)

app_name = "lms"

router = DefaultRouter()
router.register(
    "courses",
    CourseViewSet,
    basename="course",
)

urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "lessons/",
        LessonListCreateAPIView.as_view(),
        name="lesson_list_create",
    ),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyAPIView.as_view(),
        name="lesson_detail",
    ),
    path(
        "subscriptions/toggle/",
        SubscriptionToggleAPIView.as_view(),
        name="subscription_toggle",
    ),
]
