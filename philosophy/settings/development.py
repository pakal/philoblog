from .base import *
import sys

TEMPLATES[0]['OPTIONS'].update({'debug': True})

# Both Django's page cache (UpdateCacheMiddleware/FetchFromCacheMiddleware) and django-cms's
# own page/placeholder cache corrupt cached response headers on a cache hit when
# django-debug-toolbar's CachePanel is also active (Django 6.1.2 + django-cms 5.1.3 +
# django-debug-toolbar 6.3.0): CachePanel's instrumentation of cache.set()/get() mangles the
# stored ResponseHeaders object into its raw internal _store dict. Harmless in prod, which
# never loads the toolbar, but caching pages for up to an hour while developing content is
# undesirable anyway.
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


