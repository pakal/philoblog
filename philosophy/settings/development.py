from .base import *
import sys

TEMPLATES[0]['OPTIONS'].update({'debug': True})

# Turn off debug while imported by Celery with a workaround
# See http://stackoverflow.com/a/4806384
if "celery" in sys.argv[0]:
    DEBUG = False

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


