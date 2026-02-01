from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count

# --- Кастомный QuerySet для постов ---
class PostQuerySet(models.QuerySet):
    def popular(self):
        """Сортирует посты по количеству лайков (популярности)"""
        return self.annotate(likes_count=Count('likes', distinct=True)).order_by('-likes_count')

    def fetch_with_comments_count(self):
        """Добавляет к постам количество комментариев и возвращает QuerySet"""
        popular_ids = list(self.values_list('id', flat=True))
        comments_counts = (
            Post.objects
            .filter(id__in=popular_ids)
            .annotate(comments_count=Count('comments'))
            .values_list('id', 'comments_count')
        )
        counts_dict = dict(comments_counts)
        # Присваиваем временное поле comments_count каждому посту
        for post in self:
            post.comments_count = counts_dict.get(post.id, 0)
        return self

class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка', blank=True, null=True)
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True}
    )
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги'
    )

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

# --- Кастомный QuerySet для тегов ---
class TagQuerySet(models.QuerySet):
    def popular(self):
        """Сортирует теги по количеству постов"""
        return self.annotate(posts_count=Count('posts')).order_by('-posts_count')

class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args=[self.title])

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому написан'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
