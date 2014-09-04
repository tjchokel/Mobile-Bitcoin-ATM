from django.shortcuts import render
from blog.models import BlogPost, Category
from django.shortcuts import render_to_response, get_object_or_404

from annoying.decorators import render_to


@render_to('blog_index.html')
def blog_index(request):
    categories = Category.objects.all()
    return {
        'posts': BlogPost.objects.all().order_by('-posted_at')[:5],
        'categories': categories,
    }


@render_to('view_post.html')
def view_post(request, slug):
    categories = Category.objects.all()
    return {
        'post': get_object_or_404(BlogPost, slug=slug),
        'categories': categories,
        'posts': BlogPost.objects.all().order_by('-posted_at')[:5],
    }


@render_to('view_category.html')
def view_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    categories = Category.objects.all()
    return {
        'category': category,
        'posts': BlogPost.objects.filter(category=category).order_by('-posted_at')[:5],
        'categories': categories,
    }