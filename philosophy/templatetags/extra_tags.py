import re

from cms.models import PageContent, Placeholder
from django import template
from django.utils.translation import get_language

register = template.Library()

#  Custom tag for diagnostics
@register.simple_tag()
def debug_object_dump(var):
    return type(var), vars(var)


_ICON_CLASS_RE = re.compile(r'<span class="([^"]+)"')
_TITLE_RE = re.compile(r"<h4[^>]*>(.*?)</h4>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


@register.simple_tag()
def category_badge(page):
    """Extracts the category icon class and label out of the article's "intro" snippet plugin
    (the per-category icon/title/lead-text snippet, eg. "psychology" or "justice_and_ethics_intro"),
    so it can be shown as a small badge instead of the full intro box."""
    if not page:
        return None
    page_content = PageContent.objects.filter(page=page, language=get_language()).first()
    if not page_content:
        return None
    placeholders = Placeholder.objects.get_for_obj(page_content).filter(slot="intro")
    for placeholder in placeholders:
        for plugin in placeholder.get_plugins(language=get_language()):
            snippet_grouper = getattr(plugin.get_bound_plugin(), "snippet_grouper", None)
            snippet = snippet_grouper.snippet() if snippet_grouper else None
            if not snippet:
                continue
            icon_match = _ICON_CLASS_RE.search(snippet.html)
            title_match = _TITLE_RE.search(snippet.html)
            if not icon_match or not title_match:
                continue
            icon_classes = " ".join(
                cls for cls in icon_match.group(1).split() if not cls.startswith("bordered-icon")
            )
            title = _TAG_RE.sub("", title_match.group(1)).strip()
            return {"icon_class": icon_classes, "title": title}
    return None
