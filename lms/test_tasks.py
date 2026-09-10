from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from lms.models import Course, Subscription
from lms.tasks import send_course_update_email


class CourseUpdateTaskTestCase(TestCase):
    """Тестирует уведомление подписчиков курса."""

    def setUp(self):
        user_model = get_user_model()

        self.owner = user_model.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.subscriber = user_model.objects.create_user(
            email="subscriber@example.com",
            password="TestPassword123!",
        )

        self.course = Course.objects.create(
            title="Тестовый курс",
            description="Описание курса",
            owner=self.owner,
        )

        Subscription.objects.create(
            user=self.subscriber,
            course=self.course,
        )

    @patch("lms.tasks.send_mass_mail")
    def test_email_is_sent_to_subscriber(
        self,
        mocked_send_mass_mail,
    ):
        mocked_send_mass_mail.return_value = 1

        result = send_course_update_email.run(
            self.course.pk,
        )

        self.assertEqual(result, 1)
        mocked_send_mass_mail.assert_called_once()

        email_messages = (
            mocked_send_mass_mail.call_args.args[0]
        )

        self.assertEqual(
            email_messages[0][3],
            ["subscriber@example.com"],
        )