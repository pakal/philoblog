from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from cms.models import PageContent, Placeholder
from django.utils.translation import get_language
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels


def get_preview_galleries(request):

    menu_renderer = menu_pool.get_renderer(request)

    nodes = menu_renderer.get_nodes()

    # In case we want to trim displayed articles in this preview
    sections = cut_levels(nodes,
                          from_level=0, to_level=100,
                          extra_inactive=1000, extra_active=1000)

    galleries = []

    for section in sections:

        section_images = []

        for article in section.children:
            # The default manager only returns published content (djangocms-versioning)
            page_content = PageContent.objects.filter(page_id=article.id, language=get_language()).first()
            if not page_content:
                continue  # Page is not yet published
            page = page_content.page

            placeholders = Placeholder.objects.get_for_obj(page_content).filter(slot="illustration")
            for placeholder in placeholders:

                for plugin in placeholder.get_plugins():  # Returns CMSPlugin instances
                    real_plugin = plugin.get_bound_plugin()  # Real subtype of CMSPlugin

                    picture = getattr(real_plugin, "picture", None)  # djangocms-picture plugin
                    if not picture:
                        continue  # Not an image plugin? Skip!

                    section_images.append((page, picture.file))

        if section_images:
            galleries.append((section.title, section_images))

    return galleries


class PagesOverviewPlugin(CMSPluginBase):
    model = CMSPlugin
    render_template = "overview.html"

    def render(self, context, instance, placeholder):
        context = super(PagesOverviewPlugin, self).render(context, instance, placeholder)
        request = context["request"]
        context.update({
            "galleries": get_preview_galleries(request)
        })
        return context


plugin_pool.register_plugin(PagesOverviewPlugin)
