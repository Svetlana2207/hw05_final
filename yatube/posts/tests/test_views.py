import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from yatube.settings import PAGE_QUANTITY

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostPagesTest(TestCase):
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

        pages_num = range(0, 28)
        post_quantity = len(pages_num)
        if post_quantity > PAGE_QUANTITY * 2:
            cls.page2_quantity = PAGE_QUANTITY
        else:
            cls.page2_quantity = post_quantity - PAGE_QUANTITY
        for i in pages_num:
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовая группа {i}',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_paginator(self):
        """Количество постов на главной странице."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAGE_QUANTITY)
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.page2_quantity)

    def test_paginator_group_list(self):
        """Количество постов на странице группы."""
        group = PostPagesTest.group
        response = self.client.get(reverse(
            'posts:group_posts', kwargs={'slug': f'{group.slug}'}))
        self.assertEqual(len(response.context['page_obj']), PAGE_QUANTITY)
        response = self.client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': f'{group.slug}'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.page2_quantity)

    def test_paginator_profile(self):
        """Количество постов на странице профиля."""
        post = PostPagesTest.post
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{post.author}'}))
        self.assertEqual(len(response.context['page_obj']), PAGE_QUANTITY)
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{post.author}'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.page2_quantity)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': 'testslug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'testuser'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class ContextPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='тестовый титл',
            description='тестовое описание',
            slug='testslug',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.image_address = 'posts/small.gif'
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def compare_objects(self, first_object):
        post = ContextPagesTest.post
        post_text = first_object.text
        post_group = first_object.group
        post_author = first_object.author
        post_image = first_object.image
        post_count = first_object.author.posts.count()
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_count, self.post.author.posts.count())

    def test_index_show_correct_content(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.compare_objects(first_object)

    def test_group_list_page_show_correct_content(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = ContextPagesTest.group
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': f'{group.slug}'}))
        first_object = response.context['page_obj'][0]
        self.compare_objects(first_object)

    def test_profile_page_show_correct_content(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'testuser'}))
        first_object = response.context['page_obj'][0]
        self.compare_objects(first_object)

    def test_post_detail__page_show_correct_content(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post = ContextPagesTest.post
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': f'{post.pk}'}))
        first_object = response.context['post']
        self.compare_objects(first_object)

    def test_create__page_show_correct_content(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        """Кэширование страницы index производится."""
        post = Post.objects.all()[0]
        response = self.client.get(reverse('posts:index'))
        Post.objects.all()[0].delete()
        self.assertContains(response, post.text)


class PostCreateViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group
        )

    def setUp(self):
        self.user = PostCreateViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_index_post(self):
        group = PostCreateViewsTest.group
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.group.pk
        self.assertEqual(task_text_0, group.pk)

    def test_group_post(self):
        group = PostCreateViewsTest.group
        rvrs = reverse('posts:group_posts', kwargs={'slug': f'{group.slug}'})
        response = self.authorized_client.get(rvrs)
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.group.pk
        self.assertEqual(task_text_0, group.pk)

    def test_profile_post(self):
        group = PostCreateViewsTest.group
        post = PostCreateViewsTest.post
        rvrs = reverse('posts:profile', kwargs={'username': f'{post.author}'})
        response = self.authorized_client.get(rvrs)
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.group.pk
        self.assertEqual(task_text_0, group.pk)


class FollowUnfollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group
        )

    def setUp(self):
        self.user = FollowUnfollowViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_add_comment_be_commented_an_authorized_client(self):
        """Комментирует посты только авторизованный пользователь."""
        post = FollowUnfollowViewsTest.post
        count_comments = post.comments.count()
        text = 'коммент'
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data={'text': text},
            follow=True
        )
        self.assertEqual(count_comments, post.comments.count())
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data={'text': text},
            follow=True)
        self.assertEqual(count_comments + 1, post.comments.count())

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь подписывается на других."""
        author = FollowUnfollowViewsTest.author
        following_count = self.user.following.count()
        self.assertEqual(following_count, 0)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': author}))
        self.assertEqual(
            self.author.following.count(), following_count + 1)
        self.assertTrue(self.user.follower.filter(
            author_id=author.id).exists())

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь отписывается."""
        following_count = self.user.following.count() + 1
        self.assertNotEqual(following_count, 0)
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(
            self.author.following.count(), following_count - 1)
        self.assertFalse(self.user.follower.filter(
            author_id=self.author.id).exists())

    def test_new_post_iust_in_followers(self):
        """Новая запись появляется только в ленте фолловеров."""
        author = FollowUnfollowViewsTest.author
        text1 = 'пост для фолловеров'
        text2 = 'пост левого автора'
        Post.objects.create(author=author, text=text1,)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(0, response.context['page_obj'].paginator.count)
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': author}))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(1, response.context['page_obj'].paginator.count)

        post2 = Post.objects.create(author=author, text=text2,)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(2, response.context['page_obj'].paginator.count)

        response = self.authorized_follower.get(reverse('posts:follow_index'))
        last_post = response.context.get('page_obj')[0]
        self.assertEqual(post2.id, last_post.id)
