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

ALLOWED_HOSTS = ['www.closecoin.com', 'closecoin.herokuapp.com', ]

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
    'raven.contrib.django.raven_compat',
    'south',
    'crispy_forms',
    'users',
    'merchants',
    'bitcoins',
    'shoppers',
    'services',
    'emails',
    'phones',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'bitcash.middleware.AjaxMessaging',
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

DEBUG_TOOLBAR_PATCH_SETTINGS = False

AUTH_USER_MODEL = 'users.AuthUser'


PRODUCTION_DOMAIN = 'www.closecoin.com'
STAGING_DOMAIN = 'bitcashstaging.herokuapp.com'
SITE_DOMAIN = os.getenv('SITE_DOMAIN', PRODUCTION_DOMAIN)

# SSL and BASE_URL settings for Production, Staging and Local:
if SITE_DOMAIN in (PRODUCTION_DOMAIN, STAGING_DOMAIN):
    BASE_URL = 'https://%s' % SITE_DOMAIN
    # SSL stuff:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    MIDDLEWARE_CLASSES += ('bitcash.middleware.SSLMiddleware',)
else:
    BASE_URL = 'http://%s' % SITE_DOMAIN

if SITE_DOMAIN == PRODUCTION_DOMAIN:
    EMAIL_DEV_PREFIX = False
else:
    EMAIL_DEV_PREFIX = True
    # Enable debug toolbar on local and staging
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES
    INSTALLED_APPS += ('debug_toolbar', )

SESSION_EXPIRE_AT_BROWSER_CLOSE = True


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

BCI_SECRET_KEY = os.getenv('BCI_SECRET_KEY')
BLOCKCYPHER_API_KEY = os.getenv('BLOCKCYPHER_API_KEY')

SERVER_EMAIL = 'support@coinsafe.com'

POSTMARK_SMTP_SERVER = 'smtp.postmarkapp.com'
POSTMARK_SENDER = 'CoinSafe Support <support@coinsafe.com>'
POSTMARK_TEST_MODE = os.getenv('POSTMARK_TEST_MODE', False)
POSTMARK_API_KEY = os.getenv('POSTMARK_API_KEY')
assert POSTMARK_API_KEY, 'Must have a Postmark API Key'

EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'

PLIVO_AUTH_TOKEN = os.getenv('PLIVO_AUTH_TOKEN')
PLIVO_AUTH_ID = os.getenv('PLIVO_AUTH_ID')
assert PLIVO_AUTH_ID, 'Must have plivo API access'

# Keep this at the end
if DEBUG:
    print '-' * 75
    print 'SITE_DOMAIN is set to %s' % SITE_DOMAIN
    print "If you're testing webhooks, be sure this is correct"
    print '-' * 75
