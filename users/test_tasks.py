from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from users.tasks import deactivate_inactive_users


class DeactivateInactiveUsersTaskTestCase(TestCase):
    """Тестирует блокировку неактивных пользователей."""

    def setUp(self):
        user_model = get_user_model()

        self.inactive_user = (
            user_model.objects.create_user(
                email="inactive@example.com",
                password="TestPassword123!",
            )
        )
        self.inactive_user.last_login = (
            timezone.now() - timedelta(days=31)
        )
        self.inactive_user.save(
            update_fields=["last_login"],
        )

        self.active_user = (
            user_model.objects.create_user(
                email="active@example.com",
                password="TestPassword123!",
            )
        )
        self.active_user.last_login = (
            timezone.now() - timedelta(days=5)
        )
        self.active_user.save(
            update_fields=["last_login"],
        )

    def test_old_user_is_deactivated(self):
        updated_count = (
            deactivate_inactive_users.run()
        )

        self.inactive_user.refresh_from_db()
        self.active_user.refresh_from_db()

        self.assertEqual(updated_count, 1)
        self.assertFalse(
            self.inactive_user.is_active,
        )
        self.assertTrue(
            self.active_user.is_active,
        )