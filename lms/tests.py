from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson


class CourseSerializerTestCase(APITestCase):
    """Тестирует вывод курса и связанных уроков."""

    def setUp(self):
        self.course = Course.objects.create(
            title="Python-разработка",
            description="Тестовый курс",
        )

        Lesson.objects.create(
            course=self.course,
            title="Первый урок",
            description="Описание первого урока",
            video_url="https://youtube.com/lesson-1",
        )

        Lesson.objects.create(
            course=self.course,
            title="Второй урок",
            description="Описание второго урока",
            video_url="https://youtube.com/lesson-2",
        )

    def test_course_contains_lesson_count(self):
        response = self.client.get(
            f"/api/courses/{self.course.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["lesson_count"],
            2,
        )

    def test_course_contains_nested_lessons(self):
        response = self.client.get(
            f"/api/courses/{self.course.pk}/",
        )

        self.assertEqual(
            len(response.data["lessons"]),
            2,
        )
        lesson_titles = [
            lesson["title"]
            for lesson in response.data["lessons"]
        ]

        self.assertCountEqual(
            lesson_titles,
            [
                "Первый урок",
                "Второй урок",
            ],
        )