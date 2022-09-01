from http.client import HTTPResponse
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_page_obj


@cache_page(20, key_prefix='index_page')
def index(request: HttpRequest) -> HTTPResponse:
    """Главная страница:  Получение последних постов."""
    post_list: QuerySet[Post] = Post.objects.select_related('group', 'author')
    page_obj: Any = get_page_obj(post_list, request)
    context: Dict[str, QuerySet[Post]] = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HTTPResponse:
    """Получение списка последних постов группы."""
    group: Group = get_object_or_404(Group, slug=slug)
    group_post_list: QuerySet[Post] = group.posts.select_related(
        'group', 'author')
    page_obj: Any = get_page_obj(group_post_list, request)
    context: Dict[str, Any] = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HTTPResponse:
    """Получение списка  постов одного автора(пользователя)."""
    author: str = get_object_or_404(User, username=username)
    author_posts: QuerySet[Post] = author.posts.select_related(
        'group', 'author')
    posts_count: int = author_posts.count()
    page_obj: Any = get_page_obj(author_posts, request)
    following = request.user.is_authenticated and Follow.objects.filter(
        author=author, user=request.user).exists()
    context: Dict[str, Any] = {
        'author': author,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HTTPResponse:
    """Получение отдельной страницы поста."""
    post: Post = get_object_or_404(Post, pk=post_id)
    n_posts: int = post.author.posts.count()
    form: CommentForm = CommentForm()
    comments: QuerySet[Comment] = Comment.objects.filter(post__id=post_id)
    context: Dict[str, Any] = {
        'post': post,
        'n_posts': n_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HTTPResponse:
    """Публикация нового поста."""
    form: PostForm = PostForm(
        request.POST or None,
        files=request.FILES or None,)
    if request.method == 'POST':
        if form.is_valid():
            post: PostForm = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HTTPResponse:
    """Страница редактирования постов."""
    post: Post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        is_edit: bool = True
        form: PostForm = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.id)
        context: Dict[str, Any] = {
            'is_edit': is_edit,
            'form': form,
            'post': post,
        }
        return render(request, 'posts/create_post.html', context)
    else:
        return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request: HttpRequest, post_id: int) -> HTTPResponse:
    post: Post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница постов авторов, на которых подписан текущий пользователь."""
    followed_posts = Post.objects.filter(author__following__user=request.user)
    page_obj: Any = get_page_obj(followed_posts, request)
    context: Dict[str, QuerySet[Post]] = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@ login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author: str = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user, author=author)

    return redirect('posts:profile', username=author)


@ login_required
def profile_unfollow(request, username):
    author: User = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author
    ).delete()
    return redirect('posts:profile', username=author.username)
