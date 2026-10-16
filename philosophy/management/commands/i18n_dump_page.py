import json
from collections import defaultdict

from cms.models import CMSPlugin, Page, PageContent
from cms.utils.plugins import downcast_plugins
from django.core.management.base import BaseCommand, CommandError

from ._i18n_common import TRANSLATABLE_PLUGIN_FIELDS


class Command(BaseCommand):
    help = (
        "Dumps the French content of a CMS page (title/slug/meta + translatable plugin text) "
        "as JSON, as a starting point for translating it into another language with "
        "i18n_apply_translation. See Notes.txt for the full workflow."
    )

    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)
        parser.add_argument("--source-lang", default="fr")
        parser.add_argument("--out", default=None, help="Write JSON to this file (UTF-8) instead of stdout")

    def handle(self, *args, **options):
        page_id = options["page_id"]
        source_lang = options["source_lang"]

        try:
            page = Page.objects.get(pk=page_id)
        except Page.DoesNotExist:
            raise CommandError(f"No page with id {page_id}")

        try:
            source_content = PageContent.objects.get(page=page, language=source_lang)
        except PageContent.DoesNotExist:
            raise CommandError(f"Page {page_id} has no published '{source_lang}' content")

        placeholders = list(source_content.get_placeholders())
        plugins = downcast_plugins(
            CMSPlugin.objects.filter(
                placeholder_id__in=[ph.pk for ph in placeholders],
                language=source_lang,
            ).order_by("position")
        )
        slot_by_placeholder_id = {ph.pk: ph.slot for ph in placeholders}

        plugin_dumps = []
        for plugin in plugins:
            field = TRANSLATABLE_PLUGIN_FIELDS.get(plugin.plugin_type)
            if not field:
                continue
            text = getattr(plugin, field, "") or ""
            plugin_dumps.append(
                {
                    "id": plugin.pk,
                    "placeholder_slot": slot_by_placeholder_id.get(plugin.placeholder_id),
                    "plugin_type": plugin.plugin_type,
                    "field": field,
                    "text": text,
                }
            )

        dump = {
            "page_id": page.pk,
            "source_lang": source_lang,
            "fields": {
                "title": source_content.title,
                "menu_title": source_content.menu_title,
                "slug": page.get_slug(source_lang, fallback=False) or "",
                "meta_description": source_content.meta_description,
            },
            "plugins": plugin_dumps,
        }
        text = json.dumps(dump, ensure_ascii=False, indent=2)
        if options["out"]:
            with open(options["out"], "w", encoding="utf-8") as fobj:
                fobj.write(text)
            self.stderr.write(self.style.SUCCESS(f"Wrote {options['out']}"))
        else:
            self.stdout.write(text)
