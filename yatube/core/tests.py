from django.test import Client, TestCase


class ViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_error_page(self):
        """Проверка: страница 404 отдаёт кастомный шаблон."""
        response = self.client.get('/some-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
