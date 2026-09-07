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
