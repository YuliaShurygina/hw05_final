from http import HTTPStatus
import shutil
import tempfile
from http.client import HTTPResponse
from typing import Any, Dict, List, Tuple

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

POSTS_ON_SECOND_PAGE: int = 5
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_follower = Client()
        cls.user_follower.force_login(cls.user)
        cls.some_user = User.objects.create_user(
            username='unfollowed_user')
        cls.unfollowed_user = Client()
        cls.unfollowed_user.force_login(cls.some_user)

        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовый текст #1',
            group=cls.group,
        )

    def setUp(self) -> None:
        cache.clear()
        posts: List[Post] = [Post(
            author=PostPagesTests.author,
            text=f'Тестовый пост {i}',
            group=PostPagesTests.group,
        ) for i in range(0,
                         settings.POSTS_PER_PAGE
                         + POSTS_ON_SECOND_PAGE - 1)]
        Post.objects.order_by('-pub_date', '-id').bulk_create(posts)

    @classmethod
    def tearDownClass(cls) -> None:
        return super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_use_correct_template(self) -> None:
        """Тесты, проверяющие, что во view-функциях
           используются правильные html-шаблоны."""

        templates_pages_names: Dict[Any, str] = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'author'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    self.post1.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    self.post1.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response: HTTPResponse = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pagination_of_pages(self) -> None:
        """Тестирование паджинатора."""
        paginator_page_reverse: Tuple[Any, ...] = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': 'author'}),
        )
        page_count_posts: Tuple[Tuple[int, int], ...] = (
            (1, settings.POSTS_PER_PAGE),
            (2, POSTS_ON_SECOND_PAGE),
        )
        for url in paginator_page_reverse:
            for page_number, post_count in page_count_posts:
                with self.subTest(url=url):
                    response: Any = self.author_client.get(
                        url, {"page": page_number})
                    self.assertEqual(len(response.context['page_obj']),
                                     post_count)

    def test_page_index_show_correct_context(self) -> None:
        """В шаблон index.html при создании
            поста передан правильный контекст."""

        response: Any = self.author_client.get(reverse('posts:index'))
        post_context: List[Any] = response.context['page_obj'].object_list
        post_list: List[QuerySet[Post]] = list(
            Post.objects.all()[:settings.POSTS_PER_PAGE])
        self.assertEqual(post_list, post_context)

    def test_group_list_show_correct_context(self) -> None:
        """В шаблон group_list.html при создании
            поста передан правильный контекст."""
        response: Any = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        group_context: Any = response.context['group']
        post_by_group_context: List[QuerySet[Any]] = list(
            group_context.posts.all())
        post_by_group: List[QuerySet[Group]] = list(
            self.group.posts.select_related('group'))
        self.assertEqual(post_by_group, post_by_group_context)

    def test_post_create_page_show_correct_context(self) -> None:
        """В шаблон create_post.html при создании
            поста передан правильный контекст."""
        response: Any = self.author_client.get(
            reverse('posts:post_create'))
        form_fields: Dict[str, Any] = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field: Any = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self) -> None:
        """В шаблон post_detail.html передан правильный контекст."""
        response: Any = (self.author_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post1.id})))
        self.assertEqual(response.context.get('post'), self.post1)
        self.assertEqual(response.context.get('post').id, self.post1.id)

    def test_post_edit_page_show_correct_context(self) -> None:
        """В шаблон create_post.html(edit)
            при создании поста передан правильный контекст."""
        response: Any = (self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post1.id})))
        some_object: Any = response.context['post']
        post_text: Any = some_object.text
        post_group: Any = some_object.group.title
        self.assertEqual(post_text, 'Тестовый текст #1')
        self.assertEqual(post_group, 'Тестовая группа')

    def test_profile_show_correct_context(self) -> None:
        """В шаблон profile.html при создании
            поста передан правильный контекст."""
        response: Any = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author'}))
        group_context: Any = response.context['author']
        post_by_author_context: List[QuerySet[Any]] = list(
            group_context.posts.all())
        post_by_author: List[QuerySet[Group]] = list(
            self.group.posts.select_related('author'))
        self.assertEqual(post_by_author, post_by_author_context)

    def test_post_is_not_in_another_group(self) -> None:
        """Проверка, что этот пост не попал в группу,
            для которой не был предназначен."""
        response: Any = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}))
        group_context: Any = response.context['group']
        post_by_group2_context: QuerySet[Any] = group_context.posts.all()
        self.assertEqual(len(post_by_group2_context), 0)

    def test_post_is_index_profile_group_list_pages(self) -> None:
        """Проверка, что если при создании поста указать группу,
           то этот пост появляется на главной странице,
            на странице профайла, на странице группы."""
        cache.clear()
        pages: Tuple[Any, ...] = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                'username': 'author'}),
        )
        new_post: Post = Post.objects.create(
            author=self.author,
            text='новая запись',
            group=self.group,
        )
        for url in pages:
            with self.subTest(url=url):
                response: Any = self.author_client.get(
                    url)
                posts_by_context: Any = response.context['page_obj']
                self.assertIn(new_post, posts_by_context)

    def test_picture_is_in_pages_context(self) -> None:
        """При выводе поста с картинкой изображение передаётся в словаре context
            на главную страницу, на страницу профайла, на страницу группы,
            на отдельную страницу поста."""
        urls: Tuple[Any, ...] = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': 'author'}),
            reverse('posts:post_edit', kwargs={'post_id': self.post1.id}),
        )
        small_gif: Any = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded: Any = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        Post.objects.create(
            author=self.author,
            text='new text',
            group=self.group,
            image=uploaded,
        )
        for url in urls:
            with self.subTest(url=url):
                response: Any = self.author_client.get(url)
            self.assertContains(response, '<img ')

    def test_after_sending_comment_is_on_post_detail_page(self) -> None:
        """Проверка, что после успешной отправки
           комментарий появляется на странице поста."""
        comments_count: int = Comment.objects.count()
        form_data: Dict[str, Any] = {
            'text': 'Новый комментарий',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post1.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post1.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_index_cache(self) -> None:
        """Проверка кеширования главной страницы."""
        cache.clear()
        posts_count = Post.objects.count()
        new_post: Post = Post.objects.create(
            author=self.author,
            text='проверка кэша',
            group=self.group,
        )
        response: HTTPResponse = self.author_client.get(reverse(
            'posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='проверка кэша',
                group=self.group.id
            ).exists()
        )
        new_post.delete()
        cached_response: HTTPResponse = self.author_client.get(reverse(
            'posts:index'))
        self.assertEqual(response.content, cached_response.content)
        cache.clear()
        response_cleared: HTTPResponse = self.author_client.get(
            reverse('posts:index'))
        self.assertNotEqual(response_cleared.content, cached_response.content)

    def test_post_appears_on_follow_index_page_for_followers(self):
        """Новая запись пользователя появляется в ленте тех,
            кто на него подписан."""
        cache.clear()
        Follow.objects.create(
            author=self.author,
            user=self.user,
        )
        following_post: Post = Post.objects.create(
            author=self.author,
            text='проверка подписки',
            group=self.group,
        )
        response: Any = self.user_follower.get(
            '/follow/')
        context: Any = response.context['page_obj'][0]
        self.assertEqual(context, following_post)

    def test_post_not_appears_on_follow_index_page_for_unfollowers(self):
        """Новая запись пользователя не появляется в ленте тех,
             кто не подписан."""

        Follow.objects.create(
            author=self.author,
            user=self.user,
        )
        following_post: Post = Post.objects.create(
            author=self.author,
            text='проверка подписки',
            group=self.group,
        )
        response: Any = self.unfollowed_user.get(
            '/follow/')
        self.assertNotContains(response, following_post)

    def test_authorised_user_can_follow(self):
        """Авторизованный пользователь может подписываться
            на других пользователей."""
        self.user_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.all().count(), 1)
        response: HTTPResponse = self.unfollowed_user.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Follow.objects.filter(
                author=self.author,
                user=self.some_user
            ).exists()
        )

    def test_authorised_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться от подписок."""
        self.user_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
        response: HTTPResponse = self.user_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(
            Follow.objects.filter(
                author=self.author,
                user=self.user
            ).exists()
        )
