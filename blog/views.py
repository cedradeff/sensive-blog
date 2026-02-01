from django.shortcuts import render
from django.db.models import Count
from blog.models import Comment, Post, Tag


def get_related_posts_count(tag):
    return getattr(tag, 'posts_count', tag.posts.count())


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': getattr(tag, 'posts_count', tag.posts.count()),
    }


def serialize_post(post):
    tags = post.tags.all()

    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags],
        'first_tag_title': tags[0].title if tags else None,
    }


def index(request):
    posts = (
        Post.objects
        .select_related('author')
        .prefetch_related('tags')
        .annotate(likes_count=Count('likes'))
    )

    most_popular_posts = posts.order_by('-likes_count')[:5]
    most_fresh_posts = posts.order_by('-published_at')[:5]

    all_post_ids = (
        list(most_popular_posts.values_list('id', flat=True)) +
        list(most_fresh_posts.values_list('id', flat=True))
    )

    comments_counts = (
        Post.objects
        .filter(id__in=all_post_ids)
        .annotate(comments_count=Count('comments'))
        .values_list('id', 'comments_count')
    )
    comments_by_id = dict(comments_counts)

    for post in most_popular_posts:
        post.comments_count = comments_by_id.get(post.id, 0)

    for post in most_fresh_posts:
        post.comments_count = comments_by_id.get(post.id, 0)

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = (
        Post.objects
        .select_related('author')
        .prefetch_related('tags')
        .get(slug=slug)
    )

    comments = Comment.objects.filter(post=post)

    serialized_comments = [{
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    } for comment in comments]

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = Tag.objects.popular()[:5]

    related_posts = (
        tag.posts
        .select_related('author')
        .prefetch_related('tags')
        [:20]
    )

    for post in related_posts:
        post.comments_count = post.comments.count()

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})
