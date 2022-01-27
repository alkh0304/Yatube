import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test',
            slug='test-slug',
            description='test',
        )
        cls.img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostsViewsTests.img,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Тестовая группа',
            group=PostsViewsTests.group,
            image=PostsViewsTests.uploaded
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': (
                reverse('posts:group_detail',
                        kwargs={'slug': PostsViewsTests.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': PostsViewsTests.user.username})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': PostsViewsTests.post.id})
            ),
            'posts/create_post.html': (
                reverse('posts:post_create')
            ),
        }
        # Проверяем, что при обращении к name вызывается соответствующий
        # HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template,
                                        f'Проверьте, что при обращении к'
                                        f' {reverse_name} вызывается'
                                        f' соответствующий {template}')

    def test_post_edit_url(self):
        """URL-адреса используют шаблон posts/create_post.html."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': PostsViewsTests.post.id})))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def assert_posts_equal(self, expected_post, actual_post):
        self.assertEqual(expected_post.text, actual_post.text)
        self.assertEqual(expected_post.author.username,
                         actual_post.author.username)
        self.assertEqual(expected_post.group, actual_post.group)
        self.assertEqual(expected_post.image, actual_post.image)

    def test_post_detail_page_show_corect_context(self):
        """Контекст страницы поста"""
        response = self.client.get(reverse('posts:post_detail',
                                   kwargs={'post_id':
                                           PostsViewsTests.post.id}))
        first_object = response.context['post']
        self.assert_posts_equal(first_object, self.post)

    def test_index_page_show_corect_context(self):
        """Контекст главной страницы"""
        response = self.client.get(reverse('posts:main'))
        first_object = response.context['page_obj'][0]
        self.assert_posts_equal(first_object, self.post)

    def test_group_detail_page_show_corect_context(self):
        """Контекст страницы группы"""
        response = self.client.get(reverse('posts:group_detail',
                                           kwargs={'slug':
                                                   PostsViewsTests.group.slug}
                                           )
                                   )
        first_object = response.context['page_obj'][0]
        self.assert_posts_equal(first_object, self.post)

    def test_profile_page_show_corect_context(self):
        """Контекст страницы профиля"""
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   PostsViewsTests.user
                                                   .username}
                                           )
                                   )
        first_object = response.context['page_obj'][0]
        self.assert_posts_equal(first_object, self.post)

    def test_post_create_page_show_correct_context(self):
        """Контекст формы создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_corect_context(self):
        """Контекст формы редактирования поста"""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id':
                                                      PostsViewsTests.
                                                      post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_group(self):
        """Проверка создания поста в группе"""
        created_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Тестовая группа',
            group=PostsViewsTests.group,
            image=PostsViewsTests.uploaded
        )
        response = self.client.get(
            reverse('posts:group_detail',
                    kwargs={'slug': created_post.group.slug})
        )
        group_page_response = response.context['page_obj'][0]
        self.assert_posts_equal(group_page_response, created_post)

    def test_new_post_main(self):
        """Проверка создания поста на главной странице"""
        created_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Тестовая группа',
            group=PostsViewsTests.group,
            image=PostsViewsTests.uploaded
        )
        response = self.client.get(
            reverse('posts:main')
        )
        index_page_response = response.context['page_obj'][0]
        self.assert_posts_equal(index_page_response, created_post)

    def test_new_post_profile(self):
        """Проверка создания поста в профиле пользователя"""
        created_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Тестовая группа',
            group=PostsViewsTests.group,
            image=PostsViewsTests.uploaded
        )
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      created_post.author}))
        index_page_response = response.context['page_obj'][0]
        self.assert_posts_equal(index_page_response, created_post)

    def test_new_post_other_group(self):
        """Проверка что пост не дублировался в другой группе"""
        created_group = Group.objects.create(
            title='test22',
            slug='test22',
            description='test22',
        )
        created_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='testing',
            group=created_group,
            image=PostsViewsTests.uploaded
        )
        response = self.client.get(
            reverse('posts:group_detail', kwargs={'slug':
                                                  PostsViewsTests.group.slug})
        )
        count_group_response = response.context['page_obj'][0]
        self.assertNotEqual(count_group_response, created_post)

    def test_follow(self):
        """Проверка подписки и отписки"""
        created_user = User.objects.create_user(username='test')
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username':
                                                   created_user.username}),
                                   follow=True)
        self.assertTrue(Follow.objects.filter(user=PostsViewsTests.user,
                                              author=created_user).exists())

    def test_unfollow(self):
        created_user = User.objects.create_user(username='test')
        Follow.objects.create(author=created_user, user=PostsViewsTests.user)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username':
                                                   created_user.username}),
                                   follow=True)
        self.assertFalse(Follow.objects.filter(user=PostsViewsTests.user,
                                               author=created_user).exists())

    def test_follow_index(self):
        """Проверка ленты с авторами"""
        created_user = User.objects.create_user(username='test')
        Follow.objects.create(author=created_user, user=PostsViewsTests.user)
        created_post = Post.objects.create(
            author=created_user,
            text='testing',
            image=PostsViewsTests.uploaded
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, created_post.text)
        Follow.objects.filter(author=created_user,
                              user=PostsViewsTests.user).delete()
        cache.clear()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, created_post.text)

    def test_cache(self):
        """Проверка работы кэша"""
        cache.clear()
        created_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='testing',
            image=PostsViewsTests.uploaded
        )
        cache.set('1', created_post)
        response = self.client.get(reverse('posts:main'))
        self.assertTrue(created_post.text in response.content.decode('utf-8'))
        post2 = Post.objects.create(
            author=PostsViewsTests.user,
            text='testing2',
            image=PostsViewsTests.uploaded
        )
        cache.set('2', post2)
        response = self.client.get(reverse('posts:main'))
        self.assertFalse(post2.text in response.content.decode('utf-8'))
        cache.clear()
        cache.set('3', post2)
        response = self.client.get(reverse('posts:main'))
        self.assertTrue(post2.text in response.content.decode('utf-8'))


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test',
            slug='test-slug',
            description='Тестовый текст',
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorTests.user)
        # Создаем тестовые посты
        objs = (Post(author=PaginatorTests.user,
                     text='Тестовая группа',
                     group=PaginatorTests.group,)
                for i in range(13))
        Post.objects.bulk_create(objs)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:main'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть 3 поста.
        response = self.client.get(reverse('posts:main') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_group(self):
        response = self.client.get(reverse('posts:group_detail',
                                           kwargs={'slug':
                                                   PaginatorTests.group.slug}))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_two_records_group(self):
        # Проверка: на второй странице должно быть 3 поста.
        response = self.client.get(reverse('posts:group_detail',
                                           kwargs={'slug':
                                                   PaginatorTests.group.slug})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_profile(self):
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username':
                                           PaginatorTests.user.username}))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_two_records_profile(self):
        # Проверка: на второй странице должно быть 3 поста.
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username':
                                           PaginatorTests.user.username})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
