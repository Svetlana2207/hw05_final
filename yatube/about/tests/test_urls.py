from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):

    def test_author_guest(self):
        """Страница доступна любому пользователю."""
        reverce_status_names = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for reverse_name, status in reverce_status_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, status)
