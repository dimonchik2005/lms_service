from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson
from users.models import Payment, User


class PaymentAPITestCase(APITestCase):
    """Тестирует список, сортировку и фильтрацию платежей."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="test-password",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.course = Course.objects.create(
            title="Тестовый курс",
            description="Описание курса",
        )

        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Тестовый урок",
            description="Описание урока",
            video_url="https://youtube.com/test",
        )

        self.course_payment = Payment.objects.create(
            user=self.user,
            paid_course=self.course,
            amount=Decimal("15000.00"),
            payment_method=Payment.PaymentMethod.TRANSFER,
        )

        self.lesson_payment = Payment.objects.create(
            user=self.user,
            paid_lesson=self.lesson,
            amount=Decimal("2500.00"),
            payment_method=Payment.PaymentMethod.CASH,
        )

        Payment.objects.filter(
            pk=self.course_payment.pk,
        ).update(
            payment_date=timezone.now()
            - timedelta(days=1),
        )

        self.course_payment.refresh_from_db()
        self.lesson_payment.refresh_from_db()

        self.url = "/api/users/payments/"

    def test_payment_list(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 2)

    def test_filter_by_course(self):
        response = self.client.get(
            self.url,
            {"paid_course": self.course.pk},
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.course_payment.pk,
        )

    def test_filter_by_lesson(self):
        response = self.client.get(
            self.url,
            {"paid_lesson": self.lesson.pk},
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.lesson_payment.pk,
        )

    def test_filter_by_payment_method(self):
        response = self.client.get(
            self.url,
            {"payment_method": "cash"},
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["payment_method"],
            "cash",
        )

    def test_ordering_by_payment_date(self):
        ascending_response = self.client.get(
            self.url,
            {"ordering": "payment_date"},
        )

        descending_response = self.client.get(
            self.url,
            {"ordering": "-payment_date"},
        )

        self.assertEqual(
            ascending_response.data[0]["id"],
            self.course_payment.pk,
        )
        self.assertEqual(
            descending_response.data[0]["id"],
            self.lesson_payment.pk,
        )

    def test_user_contains_payment_history(self):
        response = self.client.get(
            f"/api/users/{self.user.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data["payments"]),
            2,
        )

class AuthenticationAndUserAccessTestCase(
    APITestCase,
):
    """Проверяет регистрацию, JWT и профили."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="TestPassword_2026!",
            city="Таганрог",
        )

        self.other_user = User.objects.create_user(
            email="other-profile@example.com",
            password="TestPassword_2026!",
            city="Москва",
        )

    def test_registration(self):
        response = self.client.post(
            "/api/users/register/",
            {
                "email": "registered@example.com",
                "phone": "+79991112233",
                "city": "Таганрог",
                "password": "StrongPassword_2026!",
                "password_repeat": "StrongPassword_2026!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        created_user = User.objects.get(
            email="registered@example.com",
        )

        self.assertTrue(
            created_user.check_password(
                "StrongPassword_2026!",
            )
        )

    def test_duplicate_email_registration(self):
        response = self.client.post(
            "/api/users/register/",
            {
                "email": "profile@example.com",
                "password": "StrongPassword_2026!",
                "password_repeat": "StrongPassword_2026!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_token_obtain_pair(self):
        response = self.client.post(
            "/api/token/",
            {
                "email": "profile@example.com",
                "password": "TestPassword_2026!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_anonymous_user_cannot_get_profiles(self):
        response = self.client.get(
            "/api/users/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            f"/api/users/{self.user.pk}/",
            {"city": "Ростов-на-Дону"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_user_cannot_update_other_profile(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            f"/api/users/{self.other_user.pk}/",
            {"city": "Изменённый город"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_other_profile_has_no_payment_history(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            f"/api/users/{self.other_user.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotIn(
            "payments",
            response.data,
        )
        self.assertNotIn(
            "password",
            response.data,
        )

    def test_user_can_delete_own_profile(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.delete(
            f"/api/users/{self.user.pk}/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
