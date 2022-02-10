import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='testauthor')
        cls.author2 = User.objects.create(username='testauthor2')
        cls.group = Group.objects.create(
            title='тестовый титл',
            description='тестовое описание',
            slug='testslug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client2.force_login(self.author2)

    def test_create_post(self):
        """Валидная форма создает запись."""
        post = PostFormTests.post
        group = PostFormTests.group
        post_count = Post.objects.count()
        text = 'Пост 2'
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': text,
            'group': group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.order_by('-pk')[0]
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': post.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=last_post.text,
                author=last_post.author,
                image=last_post.image,
                pk=last_post.pk,
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма меняет запись."""
        post = PostFormTests.post
        group = PostFormTests.group
        post_count = Post.objects.count()
        text = 'Новый текст'
        form_data = {
            'text': text,
            'group': group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=text,
                author=post.author,
                pk=post.pk
            ).exists()
        )

    def test_edit_post_no_author(self):
        """Валидная форма не меняет запись если не автор."""
        post = PostFormTests.post
        group = PostFormTests.group
        post_count = Post.objects.count()
        text = 'Новый автор'
        form_data = {
            'text': text,
            'group': group.pk,
        }
        response = self.authorized_client2.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=text,
                author=post.author,
                pk=post.pk
            ).exists()
        )

    def test_create_guest(self):
        """Создание поста анонимным пользователем."""
        group = PostFormTests.group
        post_count = Post.objects.count()
        text = 'Пост 3'
        form_data = {
            'text': text,
            'group': group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        urls = f'{reverse("users:login")}?next={reverse("posts:post_create")}'
        self.assertRedirects(response, urls)
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_guest(self):
        """Редактирование поста анонимным пользователем."""
        post = PostFormTests.post
        group = PostFormTests.group
        text = 'текст4'
        form_data = {
            'text': text,
            'group': group.pk,
        }
        response = self.client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        next = reverse("posts:post_edit", kwargs={"post_id": post.pk})
        urls = f'{reverse("users:login")}?next={next}'
        self.assertRedirects(response, urls)
        self.assertFalse(
            Post.objects.filter(
                text=text,
                author=post.author,
                pk=post.pk
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='testauthor')
        cls.group = Group.objects.create(
            title='тестовый титл',
            description='тестовое описание',
            slug='testslug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись комментария."""
        post = CommentFormTests.post
        text = 'коммент'
        comment_count = Comment.objects.count()
        form_data = {
            'text': text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': post.pk}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=text,
                author=post.author,
                post=post
            ).exists()
        )
