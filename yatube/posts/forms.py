from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'text': 'Текст поста',
                  'group': 'Группа', 'image': 'Изображение'}
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Прикрепите изображение',
        }
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        labels = {'text': 'Комментарий'}
        help_texts = {
            'text': 'Текст нового комментария',
        }
        fields = ['text']
