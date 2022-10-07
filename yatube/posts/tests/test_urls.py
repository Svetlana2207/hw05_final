from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='testuser')
        cls.author = User.objects.create(username='testauthor')

        cls.group = Group.objects.create(
            title='тестовый титл',
            description='тестовое описание',
            slug='testslug',
        )

        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_homepage(self):
        """Доступность страниц любому пользователю."""
        templates_pages_names = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': f'{self.group.slug}'}): HTTPStatus.OK,
            reverse('posts:profile', kwargs={'username': f'{self.user}'}):
                HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}):
                HTTPStatus.OK,
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, template)

    def test_post_author(self):
        """Доступность редактирования страниц post_id автору"""
        response = self.author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_user(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_guest(self):
        """Страница create/ перенаправляет неавторизованного пользователя."""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_no_page_guest(self):
        """Недоступность несуществующей страницы любому пользователю."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
