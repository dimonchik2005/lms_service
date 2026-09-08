from rest_framework import status
from rest_framework.test import APITestCase
from lms.models import Course, Lesson
from django.contrib.auth.models import Group
from users.models import User


class CourseSerializerTestCase(APITestCase):
    """Проверяет вывод курса и связанных уроков."""

    def setUp(self):
        """Создаёт тестовые данные перед каждым тестом."""

        self.user = User.objects.create_user(
            email="course-owner@example.com",
            password="TestPassword_2026!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.course = Course.objects.create(
            owner=self.user,
            title="Python-разработка",
            description="Тестовый курс",
        )

        Lesson.objects.create(
            owner=self.user,
            course=self.course,
            title="Первый урок",
            description="Описание первого урока",
            video_url="https://youtube.com/lesson-1",
        )

        Lesson.objects.create(
            owner=self.user,
            course=self.course,
            title="Второй урок",
            description="Описание второго урока",
            video_url="https://youtube.com/lesson-2",
        )

    def test_course_contains_lesson_count(self):
        """Проверяет количество уроков курса."""

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
        """Проверяет вложенный список уроков."""

        response = self.client.get(
            f"/api/courses/{self.course.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
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


class LMSPermissionsTestCase(APITestCase):
    """Проверяет владельцев и модераторов."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword_2026!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword_2026!",
        )

        self.moderator = User.objects.create_user(
            email="moderator-test@example.com",
            password="TestPassword_2026!",
        )

        moderator_group = Group.objects.create(
            name="Модераторы",
        )
        self.moderator.groups.add(
            moderator_group,
        )

        self.owner_course = Course.objects.create(
            owner=self.owner,
            title="Курс владельца",
            description="Описание",
        )

        self.other_course = Course.objects.create(
            owner=self.other_user,
            title="Чужой курс",
            description="Описание",
        )

        self.owner_lesson = Lesson.objects.create(
            owner=self.owner,
            course=self.owner_course,
            title="Урок владельца",
            description="Описание",
            video_url="https://youtube.com/owner",
        )

    def test_anonymous_user_has_no_access(self):
        response = self.client.get(
            "/api/courses/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_sees_only_own_courses(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            "/api/courses/",
        )

        course_ids = [
            course["id"]
            for course in response.data
        ]

        self.assertIn(
            self.owner_course.pk,
            course_ids,
        )
        self.assertNotIn(
            self.other_course.pk,
            course_ids,
        )

    def test_course_owner_is_filled_automatically(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            "/api/courses/",
            {
                "title": "Новый курс",
                "description": "Новое описание",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        course = Course.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            course.owner,
            self.owner,
        )

    def test_user_cannot_open_other_course(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            f"/api/courses/{self.other_course.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_moderator_can_update_any_course(self):
        self.client.force_authenticate(
            user=self.moderator,
        )

        response = self.client.patch(
            f"/api/courses/{self.owner_course.pk}/",
            {"title": "Изменено модератором"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_moderator_cannot_create_course(self):
        self.client.force_authenticate(
            user=self.moderator,
        )

        response = self.client.post(
            "/api/courses/",
            {
                "title": "Запрещённый курс",
                "description": "Описание",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_moderator_cannot_delete_course(self):
        self.client.force_authenticate(
            user=self.moderator,
        )

        response = self.client.delete(
            f"/api/courses/{self.owner_course.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_lesson_owner_is_filled_automatically(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            "/api/lessons/",
            {
                "course": self.owner_course.pk,
                "title": "Новый урок",
                "description": "Описание",
                "video_url": "https://youtube.com/new",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        lesson = Lesson.objects.get(
            pk=response.data["id"],
        )

        self.assertEqual(
            lesson.owner,
            self.owner,
        )
