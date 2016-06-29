
from .base import *
import logging.config

STATIC_URL = '/static/resources/'
MEDIA_URL = '/static/media/'

#TODO : add  'django.middleware.security.SecurityMiddleware' middleware,
# add SSL everywhere, and add X-Content-Type-Options: nosniff to NGINX static server
#add SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') for nginx

# Cache the templates in memory for speed-up
loaders = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

TEMPLATES[0]['OPTIONS'].update({"loaders": loaders})
TEMPLATES[0].update({"APP_DIRS": False})
