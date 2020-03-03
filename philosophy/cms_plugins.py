from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from cms.models import Page
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
            try:
                page = Page.objects.published().get(pk=article.id)
            except Page.DoesNotExist:
                continue  # Page is not yet published

            placeholders = page.get_placeholders().filter(slot="illustration")
            for placeholder in placeholders:

                for plugin in placeholder.get_plugins():  # Returns CMSPlugin instances
                    real_plugin = plugin.get_bound_plugin()  # Real subtype of CMSPlugin

                    if not hasattr(real_plugin, "image"):
                        continue  # Not an image plugin? Skip!

                    section_images.append((page, real_plugin.image.file))

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
