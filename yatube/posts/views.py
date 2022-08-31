from http.client import HTTPResponse
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_page_context


@cache_page(20, key_prefix='index_page')
def index(request: HttpRequest) -> HTTPResponse:
    """Главная страница:  Получение последних постов."""
    post_list: QuerySet[Post] = Post.objects.select_related(
        'group').select_related('author').all()
    page_obj: Any = get_page_context(post_list, request)
    context: Dict[str, QuerySet[Post]] = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HTTPResponse:
    """Получение списка последних постов группы."""
    group: Group = get_object_or_404(Group, slug=slug)
    group_post_list: QuerySet[Post] = group.posts.all()
    page_obj: Any = get_page_context(group_post_list, request)
    context: Dict[str, Any] = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HTTPResponse:
    """Получение списка  постов одного автора(пользователя)."""
    author: str = get_object_or_404(User, username=username)
    author_posts: QuerySet[Post] = Post.objects.all().filter(
        author=author)
    posts_count: int = author_posts.count()
    page_obj: Any = get_page_context(author_posts, request)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user.id,
            author=author.id
        ).exists()
    else:
        following = False
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
    comments: Comment = Comment.objects.filter(post__id=post_id)
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
    page_obj: Any = get_page_context(followed_posts, request)
    context: Dict[str, QuerySet[Post]] = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@ login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author: str = get_object_or_404(User, username=username)
    following = request.user.follower.filter(author=author).exists()
    if request.user != author and not following:
        follow = Follow(user=request.user, author=author)
        follow.save()
    return redirect('posts:profile', username=author)


@ login_required
def profile_unfollow(request, username):
    author: str = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author
    ).delete()
    return redirect('posts:profile', username=author.username)
