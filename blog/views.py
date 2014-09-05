from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from annoying.decorators import render_to

from blog.models import BlogPost, Category


@render_to('blog/blog_index.html')
def blog_index(request):
    categories = Category.objects.all()
    return {
        'posts': BlogPost.objects.all().order_by('-posted_at')[:5],
        'categories': categories,
    }


@render_to('blog/view_post.html')
def view_post(request, slug):
    categories = Category.objects.all()
    return {
        'post': get_object_or_404(BlogPost, slug=slug),
        'categories': categories,
        'posts': BlogPost.objects.all().order_by('-posted_at')[:5],
    }


@render_to('blog/view_category.html')
def view_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    categories = Category.objects.all()
    return {
        'category': category,
        'posts': BlogPost.objects.filter(category=category).order_by('-posted_at')[:5],
        'categories': categories,
    }


def cold_storage_guide(request):
    " Migrate old static page to new blog stuff "
    return HttpResponseRedirect(reverse('view_blog_post', kwargs={'slug': 'cold-storage-guide'}))
