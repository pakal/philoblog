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


admin.autodiscover()


ROBOTS_TXT = """
User-agent: *

Sitemap: https://regard-humaniste.com/fr/sitemap.xml
"""


# WORKAROUND for cron jobs generating broken i18n urls - https://code.djangoproject.com/ticket/26271
urlpatterns = [
    url('^None/(?P<path>.*)$', RedirectView.as_view(url='/%(path)s', permanent=False)),
]


# This is only needed when using runserver.
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url('^__debug__/', include(debug_toolbar.urls)),
        ] + staticfiles_urlpatterns() # NOQA


urlpatterns += i18n_patterns(

    url(r'^robots.txt$', lambda r: HttpResponse(ROBOTS_TXT)),

    url(r'^admin/', include(admin.site.urls)),  # NOQA

    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': {'cmspages': ExtendedSitemap}}),

    url(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
    url(r'^glossary/', include('terms.urls')),

    url(r'^newsletter/', include('newsletter.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    url(r'^', include('cms.urls')),
)



