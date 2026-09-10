from rest_framework import status
from rest_framework.test import APITestCase
from lms.models import Course, Lesson, Subscription
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
            for course in response.data["results"]
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


class LessonValidatorTestCase(APITestCase):
    """Проверяет допустимые ссылки урока."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="validator@example.com",
            password="TestPassword_2026!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.course = Course.objects.create(
            owner=self.user,
            title="Курс для проверки ссылок",
            description="Описание",
        )

    def test_youtube_link_is_allowed(self):
        response = self.client.post(
            "/api/lessons/",
            {
                "course": self.course.pk,
                "title": "Урок YouTube",
                "description": "Описание",
                "video_url": (
                    "https://www.youtube.com/watch?v=test"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_external_link_is_rejected(self):
        response = self.client.post(
            "/api/lessons/",
            {
                "course": self.course.pk,
                "title": "Урок со сторонней ссылкой",
                "description": "Описание",
                "video_url": "https://example.com/video",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "youtube.com",
            str(response.data["video_url"][0]),
        )


class SubscriptionAPITestCase(APITestCase):
    """Проверяет добавление и удаление подписки."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="subscriber@example.com",
            password="TestPassword_2026!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.course = Course.objects.create(
            owner=self.user,
            title="Курс для подписки",
            description="Описание",
        )

        self.url = "/api/subscriptions/toggle/"

    def test_subscription_creation(self):
        response = self.client.post(
            self.url,
            {"course_id": self.course.pk},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

        self.assertTrue(
            response.data["is_subscribed"],
        )

    def test_subscription_deletion(self):
        Subscription.objects.create(
            user=self.user,
            course=self.course,
        )

        response = self.client.post(
            self.url,
            {"course_id": self.course.pk},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            Subscription.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

        self.assertFalse(
            response.data["is_subscribed"],
        )

    def test_course_id_is_required(self):
        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["message"],
            "Необходимо передать ID курса.",
        )

    def test_course_id_must_be_integer(self):
        response = self.client.post(
            self.url,
            {"course_id": "не число"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_nonexistent_course(self):
        response = self.client.post(
            self.url,
            {"course_id": 999999},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_course_serializer_shows_subscription(self):
        Subscription.objects.create(
            user=self.user,
            course=self.course,
        )

        response = self.client.get(
            f"/api/courses/{self.course.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["is_subscribed"],
        )


class LMSPaginationTestCase(APITestCase):
    """Проверяет пагинацию курсов и уроков."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="pagination@example.com",
            password="TestPassword_2026!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.courses = []

        for number in range(25):
            course = Course.objects.create(
                owner=self.user,
                title=f"Курс {number}",
                description="Описание",
            )
            self.courses.append(course)

        for number in range(6):
            Lesson.objects.create(
                owner=self.user,
                course=self.courses[0],
                title=f"Урок {number}",
                description="Описание",
                video_url=(
                    f"https://youtube.com/watch?v={number}"
                ),
            )

    def test_course_page_size(self):
        response = self.client.get(
            "/api/courses/",
            {"page_size": 2},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

    def test_course_max_page_size(self):
        response = self.client.get(
            "/api/courses/",
            {"page_size": 100},
        )

        self.assertEqual(
            len(response.data["results"]),
            20,
        )

    def test_lesson_pagination(self):
        response = self.client.get(
            "/api/lessons/",
            {"page_size": 3},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

        self.assertEqual(
            len(response.data["results"]),
            3,
        )