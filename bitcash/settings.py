"""
Django settings for bitcash project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
# Another good one: https://github.com/etianen/django-herokuapp#validating-your-heroku-setup

SECRET_KEY = os.getenv('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!

if os.getenv('DEBUG') == 'True':
    DEBUG = True
else:
    DEBUG = False
if os.getenv('TEMPLATE_DEBUG') == 'True':
    TEMPLATE_DEBUG = True
else:
    TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

# TODO: confirm this works!
ADMINS = (
    ('Michael Flaxman', 'michael@coinsafe.com'),
    ('Tom Chokel', 'tom@coinsafe.com'),
)

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'crispy_forms',
    'business',
    'app',
    'bitcoins',
    'shoppers'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request'
)

AUTH_USER_MODEL = 'business.AppUser'

ROOT_URLCONF = 'bitcash.urls'

WSGI_APPLICATION = 'bitcash.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

# Parse database configuration from $DATABASE_URL
import dj_database_url
# http://stackoverflow.com/a/11100175
DJ_DEFAULT_URL = os.getenv('DJ_DEFAULT_URL', 'postgres://localhost')
DATABASES = {'default': dj_database_url.config(default=DJ_DEFAULT_URL)}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Yay crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap', 'bootstrap3')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
# # Static asset configuration
STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'static'),
)
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
TEMPLATE_DIRS = (os.path.join(PROJECT_PATH, 'templates'),)
