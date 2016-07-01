
import sys, os
from .base import *

import environ
env = environ.Env()

env_file = os.environ.get("DJANGO_LOCAL_ENV_FILE", os.path.join(ROOT_DIR, "local.env"))
if True: # os.path.exists(env_file):
    environ.Env.read_env(env_file)

DEBUG = env.bool("DEBUG", default=False)  # might be overridden below by smart imports

ENVIRONMENT = env.str("ENVIRONMENT")  # must exist

if ENVIRONMENT == "development":
    from .development import *
else:
    from .production import *  # also for preview etc.

STATIC_ROOT = env.str('STATIC_ROOT')
STATIC_ROOT = os.path.join(ROOT_DIR, STATIC_ROOT) if not os.path.isabs(STATIC_ROOT) else STATIC_ROOT
COMPRESS_ROOT = STATIC_ROOT  # for now, must be writable so

MEDIA_ROOT = env.str('MEDIA_ROOT')
MEDIA_ROOT = os.path.join(ROOT_DIR, MEDIA_ROOT) if not os.path.isabs(MEDIA_ROOT) else MEDIA_ROOT


# for alert emails
ADMINS = env.json("ADMINS", default=None)
MANAGERS = ADMINS

# SECURITY WARNING: keep the secret key used in production secret!
# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env.str('SECRET_KEY')

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
SITE_URL = env.str("SITE_URL")

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
_default_db = env.db()
_default_db["HOST"] = _default_db["HOST"] or ""  # workaround until new release of django-environ
DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'default': _default_db
}

# TODO - enforce this to TRUE for prod, later, when SSL gets mandatory
CSRF_COOKIE_HTTPONLY = False  # we need AJAX...
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

## Django-analytics settings
GOOGLE_ANALYTICS_PROPERTY_ID = env.str("GOOGLE_ANALYTICS_PROPERTY_ID", default=None)  # eg. 'UA-14845987-3'
GOOGLE_ANALYTICS_DOMAIN = env.str("GOOGLE_ANALYTICS_DOMAIN", default=None)  # eg. 'mydomain.com' or 'auto'

_enable_smtp = env.bool("ENABLE_SMTP", default=None)
if _enable_smtp:
    SERVER_EMAIL = env.str("SERVER_EMAIL", default=None)  # "from" of ERROR emails only
    DEFAULT_FROM_EMAIL = SERVER_EMAIL  # default "from" for non-ERROR emails
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # restored to default value
    EMAIL_HOST = env.str("EMAIL_HOST")
    EMAIL_PORT = env.int("EMAIL_PORT")
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
    EMAIL_USE_SSL = env.bool("EMAIL_USE_TLS")


if ENVIRONMENT != "development":
    from webfaction_common_prod_settings import *  # may override SMTP, cache etc.
