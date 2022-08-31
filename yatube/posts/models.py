from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

User: Type[AbstractBaseUser] = get_user_model()


class Post(models.Model):
    """Модель для хранения поста."""

    text = models.TextField(
        'Текст поста',
        help_text='Текст нового поста'
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self) -> str:
        """Метод для отображения информации
         об объекте класса для пользователей."""
        return self.text[:15]

    class Meta:
        """Контейнер класса(модели) с некоторыми данными."""
        ordering = ('-pub_date',)
        default_related_name = 'posts'


class Group(models.Model):
    """Модель сообществ."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        """Метод для отображения информации
         об объекте класса для пользователей."""
        return self.title


class Comment(models.Model):
    """Модель комментарии."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Метод для отображения информации
         об объекте класса для пользователей."""
        return self.text[:15]

    class Meta:
        """Контейнер класса(модели) с некоторыми данными."""
        ordering = ('-created',)
        default_related_name = 'comments'


class Follow(models.Model):
    """Модель подписки."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='following',)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='follower',)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow"
            )
        ]
