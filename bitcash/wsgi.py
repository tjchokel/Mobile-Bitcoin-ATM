# https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/

from raven.contrib.django.raven_compat.middleware.wsgi import Sentry
# http://raven.readthedocs.org/en/latest/config/django.html#wsgi-middleware

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bitcash.settings")

from dj_static import Cling

from django.core.wsgi import get_wsgi_application
application = Sentry(Cling(get_wsgi_application()))
