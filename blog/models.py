from django.db import models
from django.db.models import permalink


class BlogPost(models.Model):
    title = models.CharField(max_length=100, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=100, unique=True, blank=False, null=False)
    body = models.TextField(blank=False, null=False)
    posted_at = models.DateField(db_index=True, auto_now_add=True)
    category = models.ForeignKey('blog.Category', blank=True, null=True)

    def __unicode__(self):
        return '%s' % self.title

    @permalink
    def get_absolute_url(self):
        return ('view_blog_post', None, {'slug': self.slug})


class Category(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, db_index=True)

    def __unicode__(self):
        return '%s' % self.title

    @permalink
    def get_absolute_url(self):
        return ('view_blog_category', None, { 'slug': self.slug })