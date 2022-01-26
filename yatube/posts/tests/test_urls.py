from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostsModelTest.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон (Гость)."""
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostsModelTest.group.slug}/',
            'posts/profile.html': f'/profile/{PostsModelTest.user.username}/',
            'posts/post_detail.html': f'/posts/{PostsModelTest.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон (Авторизованный)."""
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostsModelTest.group.slug}/',
            'posts/profile.html': f'/profile/{PostsModelTest.user.username}/',
            'posts/post_detail.html': f'/posts/{PostsModelTest.post.id}/',
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirect_post_edit(self):
        """Переадресация с редактирования поста"""
        response = (self.guest_client.
                    get(f'/posts/{PostsModelTest.post.id}/edit/')
                    )
        self.assertEqual(response.status_code, 302)

    def test_connect_post_edit(self):
        """Доступность редактирования только автору"""
        response = (self.authorized_client.
                    get(f'/posts/{PostsModelTest.post.id}/edit/')
                    )
        self.assertEqual(response.status_code, 200)
