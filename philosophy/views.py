from cms.models import Page
from cms.templatetags.cms_tags import get_placeholder_content, _get_placeholder
from django.shortcuts import render
from django.template import RequestContext
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels


def overview(request):  # FIXME DELETE THIS
    context={}

    return render(request, template_name="overview.html", context=context)


