from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        # Создаем неавторизованного клиента
        self.guest_client = Client()
        # Создаем авторизованного клиента-автора
        self.author_client = Client()
        self.author_client.force_login(self.author)
        # Создаем авторизованного клиента не автора
        self.guest_author = Client()
        self.guest_author.force_login(self.user)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_post_id(self):
        """Страница по адресу posts/{self.post_id}/edit/ перенаправит
        авторизованного пользователя(не автора)
        пользователя на страницу поста."""
        response = self.guest_author.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/'))

    def test_url_exists_at_desired_location(self):
        """Проверка доступности страниц."""
        url_names = ['/', '/group/test-slug/', f'/profile/{self.post.author}/',
                     f'/posts/{self.post.id}/']
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        guest_templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        cache.clear()
        for address, template in guest_templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        response = self.guest_author.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisted_url(self):
        """Проверка запроса к несуществующей странице."""
        url_names = ['/somepage/', '/group/test/', '/profile/',
                     '/posts/']
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_only_authorised_user_can_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
