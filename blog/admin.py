from django.contrib import admin
from blog.models import BlogPost, Category

from bitcash.custom import ReadOnlyModelAdmin


class BlogPostAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'posted_at', 'slug', 'title', 'category']
    prepopulated_fields = {'slug': ('title',)}


class CategoryAdmin(ReadOnlyModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Category, CategoryAdmin)
