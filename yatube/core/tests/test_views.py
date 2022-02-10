from django.test import TestCase


class CustomViewsTests(TestCase):

    def test_404_page_use_custom(self):
        """Страница 404 использует кастомный шаблон."""
        response = self.client.get('core/404.html')
        self.assertTemplateUsed(response, 'core/404.html')
