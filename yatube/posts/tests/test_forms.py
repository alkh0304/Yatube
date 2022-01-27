import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем необходимую для тестов базу
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Boris')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.image,
            content_type='image/gif',
        )
        self.group = Group.objects.create(
            title='test',
            slug='test',
            description='test',
        )

    def test_create_post(self):
        """Валидная форма создает запись в Posts."""
        # Подсчитаем количество записей в Posts
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'Boris'}))
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, 200)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, верно ли заполнены поля
        self.assertTrue(
            Post.objects.filter(
                author=self.user.id,
                text='test',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        created_post = Post.objects.create(
            author=self.user,
            text='test',
        )
        # Подсчитаем количество записей в Posts
        posts_count = Post.objects.count()
        # Формируем измененный пост
        form_data2 = {
            'text': 'test2',
        }
        # Меняем пост
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': created_post.id}),
            data=form_data2,
            follow=True
        )
        created_post.refresh_from_db()
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       created_post.id}))
        # Убеждаемся, что пост изменился
        self.assertEqual(created_post.text, 'test2')
        # Убеждаемся, что число постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)

    def test_comment_post(self):
        created_post = Post.objects.create(
            author=self.user,
            text='test',
        )
        comments_count = Comment.objects.count()
        form_data2 = {
            'text': 'test2',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': created_post.id}),
            data=form_data2,
            follow=True
        )
        # Убеждаемся, что комментарий был создан
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                author=self.user.id,
                text='test2',
            ).exists()
        )

    def test_unathorized_can_not_comment_post(self):
        created_post = Post.objects.create(
            author=self.user,
            text='test',
        )
        comments_count = Comment.objects.count()
        form_data2 = {
            'text': 'test2',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': created_post.id}),
            data=form_data2,
            follow=True
        )
        # Убеждаемся, что комментарий не был создан
        self.assertEqual(Comment.objects.count(), comments_count)
