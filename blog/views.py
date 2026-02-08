from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Prefetch
from blog.models import Post, Tag, Comment


def serialize_tag(tag):
    posts_count = getattr(tag, 'posts_count', tag.posts.count())
    return {
        'title': tag.title,
        'posts_with_tag': posts_count,
    }


def serialize_post(post):
    tags = getattr(post, 'prefetched_tags', post.tags.all())
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': getattr(post, 'comments_count', 0),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags],
        'first_tag_title': tags[0].title if tags else None,
    }


def index(request):
    most_popular_posts = (
        Post.objects.popular()
        .prefetch_related(
            'author',
            Prefetch('tags', to_attr='prefetched_tags')
        )
        .fetch_with_comments_count()
    )[:5]


    most_fresh_posts = (
        Post.objects.order_by('-published_at')
        .prefetch_related(
            'author',
            Prefetch('tags', to_attr='prefetched_tags')
        )
        .fetch_with_comments_count()
    )[:5]

    most_popular_tags = (
        Tag.objects.popular()
        .prefetch_related(Prefetch('posts', to_attr='prefetched_posts'))[:5]
    )

    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects
        .select_related('author')
        .prefetch_related(Prefetch('tags', to_attr='prefetched_tags'))
        .annotate(likes_count=Count('likes')),
        slug=slug
    )

    serialized_comments = [
        {
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username
        } for comment in post.comments.all()
    ]

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': getattr(post, 'likes_count', 0),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in getattr(post, 'prefetched_tags', post.tags.all())],
    }

    most_popular_tags = (
        Tag.objects.popular()
        .prefetch_related(Prefetch('posts', to_attr='prefetched_posts'))[:5]
    )

    most_popular_posts = (
        Post.objects.popular()
        .prefetch_related(
            'author',
            Prefetch('tags', to_attr='prefetched_tags')
        )
        .fetch_with_comments_count()
    )[:5]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = get_object_or_404(Tag, title=tag_title)

    most_popular_tags = (
        Tag.objects.popular()
        .prefetch_related(Prefetch('posts', to_attr='prefetched_posts'))[:5]
    )

    related_posts = (
        Post.objects
        .filter(tags=tag)
        .select_related('author')
        .prefetch_related(Prefetch('tags', to_attr='prefetched_tags'))
        .fetch_with_comments_count()
        [:20]
    )

    most_popular_posts = (
        Post.objects.popular()
        .prefetch_related(
            'author',
            Prefetch('tags', to_attr='prefetched_tags')
        )
        .fetch_with_comments_count()
    )[:5]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})
