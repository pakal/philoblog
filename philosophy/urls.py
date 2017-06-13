# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.conf.urls import *  # NOQA
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

from djangocms_page_sitemap.sitemap import ExtendedSitemap

from .views import overview

admin.autodiscover()


ROBOTS_TXT = """
User-agent: *

Sitemap: http://regard-humaniste.com/fr/sitemap.xml
"""

urlpatterns = i18n_patterns('',

    url(r'^robots.txt$', lambda r: HttpResponse(ROBOTS_TXT)),

    url(r'^admin/', include(admin.site.urls)),  # NOQA

    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': {'cmspages': ExtendedSitemap}}),

    url(r'^select2/', include('django_select2.urls')),

    url(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
    url(r'^glossary/', include('terms.urls')),

    url(r'^newsletter/', include('newsletter.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    url(r'^overview/', overview),

    url(r'^', include('cms.urls')),
)

# WORKAROUND for cron jobs generating broken i18n urls - https://code.djangoproject.com/ticket/26271
urlpatterns += patterns('',
    url('^None/(?P<path>.*)$', RedirectView.as_view(url='/%(path)s', permanent=False)),
)

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        ) + staticfiles_urlpatterns() + urlpatterns  # NOQA
