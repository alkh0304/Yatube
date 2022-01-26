from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_tech(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_author(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)
