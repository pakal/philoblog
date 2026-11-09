# -*- coding: utf-8 -*-
import contextvars

from django.contrib.sites.models import SiteManager
from django.utils.deprecation import MiddlewareMixin


class ReverseProxyFixer(MiddlewareMixin):
    """
    Sets 'REMOTE_ADDR' based on 'HTTP_X_FORWARDED_FOR', if the latter is set.

    Based on http://djangosnippets.org/snippets/1706/
    """

    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR'].split(",")[0].strip()
            request.META['REMOTE_ADDR'] = ip


_current_request = contextvars.ContextVar("current_request", default=None)


class CurrentRequestMiddleware:
    """
    Remembers the request being served, for Site.objects.get_current() calls that don't pass it.

    With an empty SITE_ID setting (both the philosophy and religion sites served by one instance), the current
    django_site row can only be found from the request's Host header, but some code paths still call
    Site.objects.get_current() without the request (eg. cmsplugin-rst page links, via Page.objects.on_site()),
    which would raise ImproperlyConfigured. When SITE_ID is set, it keeps precedence and this has no effect.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)


def _get_current_site(self, request=None):
    return _original_get_current_site(self, request if request is not None else _current_request.get())


_original_get_current_site = SiteManager.get_current
SiteManager.get_current = _get_current_site
