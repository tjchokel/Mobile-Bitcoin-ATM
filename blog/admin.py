from django.contrib import admin
from blog.models import BlogPost, Category


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'posted_at', 'slug', 'title', 'category']
    prepopulated_fields = {'slug': ('title',)}


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Category, CategoryAdmin)
