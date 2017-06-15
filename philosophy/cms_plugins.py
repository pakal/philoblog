from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from django.utils.translation import ugettext_lazy as _

from cms.models import Page
from cms.templatetags.cms_tags import get_placeholder_content, _get_placeholder
from django.shortcuts import render
from django.template import RequestContext
from menus.menu_pool import menu_pool
from menus.templatetags.menu_tags import cut_levels



def get_preview_galleries(request):

    menu_renderer = menu_pool.get_renderer(request)

    nodes = menu_renderer.get_nodes()

    #for node in nodes:
        #print("=========>", node, node.children)


    sections = cut_levels(nodes,
                          from_level=0, to_level=100,
                          extra_inactive=1000, extra_active=1000)

    galleries = []

    for section in sections:
        print("------>", section.title)

        images = []

        for article in section.children:
            page = Page.objects.published().get(pk=article.id)
            #print(page)

            context = RequestContext(request, {"request": request})
            name = "illustration"
            inherit = False
            nodelist = None

            placeholder = _get_placeholder(page, page, context, name)  # placeholder or None
            #content = get_placeholder_content(context, request, page, name, inherit, nodelist)
            if not placeholder:
                continue

            plugins = placeholder.get_plugins()

            if not plugins:
                continue

            image = plugins[0]
            inst, klass = image.get_plugin_instance()

            if not hasattr(inst, "image"):
                continue  # weird, not an image plugin

            #print(">>>>>>>", type(inst.image), inst.image.file)
            images.append((page, inst.image.file))

        if images:
            galleries.append((section.title, images))

    #print(galleries)
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
        #print(">>CONTEXT IS", context)
        return context


plugin_pool.register_plugin(PagesOverviewPlugin)
