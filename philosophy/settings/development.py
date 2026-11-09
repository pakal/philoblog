from .base import *
import sys

TEMPLATES[0]['OPTIONS'].update({'debug': True})

# Caching pages for up to an hour is undesirable while developing content, so disable both
# Django's page cache (UpdateCacheMiddleware/FetchFromCacheMiddleware) and django-cms's own
# page/placeholder cache. (The corrupted response headers once seen on cache hits came from a
# django-compat-patcher fixer, now excluded in base.py, not from the debug toolbar.)
MIDDLEWARE = [m for m in MIDDLEWARE if "cache.UpdateCacheMiddleware" not in m
              and "cache.FetchFromCacheMiddleware" not in m]
CMS_PAGE_CACHE = False
CMS_PLACEHOLDER_CACHE = False

# Turn off debug while imported by Celery with a workaround
# See http://stackoverflow.com/a/4806384
if "celery" in sys.argv[0]:
    DEBUG = False

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

# Django Debug Toolbar
INSTALLED_APPS += (
    'debug_toolbar.apps.DebugToolbarConfig',
)

# Display emails in console by default, in DEBUG mode
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Show thumbnail generation errors
THUMBNAIL_DEBUG = True


# Django-filer debugging setup
FILER_DEBUG = True
FILER_ENABLE_LOGGING = True


