from django.db import models
from django.core.urlresolvers import reverse


class BlogPost(models.Model):
    title = models.CharField(max_length=100, unique=True, blank=False, null=False, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, blank=False, null=False, db_index=True)
    body = models.TextField(blank=False, null=False)
    posted_at = models.DateField(db_index=True, auto_now_add=True)
    category = models.ForeignKey('blog.Category', blank=True, null=True)

    def __unicode__(self):
        return '%s' % self.title

    def get_absolute_url(self):
        return reverse('view_blog_post', None, { self.slug })


class Category(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, db_index=True)

    def __unicode__(self):
        return '%s' % self.title

    def get_absolute_url(self):
        return reverse('view_blog_category', None, { self.slug })
        # return reverse('view_blog_category', None, { 'slug': self.slug })