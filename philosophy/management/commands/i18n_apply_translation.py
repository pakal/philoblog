import json
from collections import defaultdict

from cms.api import create_page_content
from cms.models import CMSPlugin, Page, PageContent, PageUrl
from cms.utils.plugins import copy_plugins_to_placeholder, downcast_plugins
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from djangocms_text.utils import replace_plugin_tags
from djangocms_versioning.models import Version

from ._i18n_common import SNIPPET_GROUPER_FR_TO_EN, TRANSLATABLE_PLUGIN_FIELDS


class Command(BaseCommand):
    help = (
        "Creates (or replaces) the given page's content in a target language from a JSON "
        "translation file produced from i18n_dump_page, then publishes it. "
        "See Notes.txt for the full workflow."
    )

    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)
        parser.add_argument("--json", required=True, help="Path to the translated JSON file")
        parser.add_argument("--source-lang", default="fr")
        parser.add_argument("--target-lang", default="en")
        parser.add_argument("--user", default=None, help="Username to attribute the content to (defaults to first superuser)")

    def handle(self, *args, **options):
        page_id = options["page_id"]
        source_lang = options["source_lang"]
        target_lang = options["target_lang"]

        try:
            page = Page.objects.get(pk=page_id)
        except Page.DoesNotExist:
            raise CommandError(f"No page with id {page_id}")

        try:
            source_content = PageContent.objects.get(page=page, language=source_lang)
        except PageContent.DoesNotExist:
            raise CommandError(f"Page {page_id} has no published '{source_lang}' content")

        with open(options["json"], encoding="utf-8") as fobj:
            translation = json.load(fobj)

        fields = translation["fields"]
        plugin_texts = {int(k): v for k, v in translation.get("plugins", {}).items()}

        User = get_user_model()
        if options["user"]:
            user = User.objects.get(username=options["user"])
        else:
            user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if not user:
            raise CommandError("No user found to attribute the translation to")

        # Idempotent: wipe any previous attempt for this page/language first.
        PageContent.admin_manager.filter(page=page, language=target_lang).delete()
        PageUrl.objects.filter(page=page, language=target_lang).delete()
        page._clear_internal_cache()

        target_content = create_page_content(
            language=target_lang,
            title=fields["title"],
            page=page,
            menu_title=fields.get("menu_title") or None,
            slug=fields["slug"],
            meta_description=fields.get("meta_description") or None,
            template=source_content.template,
            in_navigation=source_content.in_navigation,
            soft_root=source_content.soft_root,
            created_by=user,
        )

        source_placeholders = list(source_content.get_placeholders())
        target_placeholders = {ph.slot: ph for ph in target_content.get_placeholders()}

        source_plugins = downcast_plugins(
            CMSPlugin.objects.filter(
                placeholder_id__in=[ph.pk for ph in source_placeholders],
                language=source_lang,
            ).order_by("position")
        )
        plugins_by_placeholder = defaultdict(list)
        for plugin in source_plugins:
            plugins_by_placeholder[plugin.placeholder_id].append(plugin)

        # Pass 1: copy every plugin's structure as-is (French text, for now) across all
        # placeholders first, so we get a complete old-plugin-id -> new-plugin-id map. Rich
        # text bodies can reference *other* plugins inline via <cms-plugin id="..."> tags (eg.
        # an inline image/link insert), and those ids must point to the new copies -- we can
        # only remap them once every plugin on the page has been copied.
        id_map = {}
        pairs = []  # (source_plugin, new_plugin)
        for placeholder in source_placeholders:
            target = target_placeholders.get(placeholder.slot)
            if target is None:
                self.stderr.write(self.style.WARNING(f"No target placeholder for slot '{placeholder.slot}'"))
                continue

            source_list = plugins_by_placeholder[placeholder.pk]
            copied_plugins = copy_plugins_to_placeholder(
                source_list,
                target,
                language=target_lang,
                plugins_are_downcast=True,
            )
            for source_plugin, new_plugin in zip(source_list, copied_plugins):
                id_map[source_plugin.pk] = new_plugin.pk
                pairs.append((source_plugin, new_plugin))

        # Pass 2: apply translated text (with <cms-plugin id="..."> references remapped to the
        # new ids) and repoint category-badge snippet plugins to their English equivalent.
        missing_translations = []
        for source_plugin, new_plugin in pairs:
            if source_plugin.plugin_type == "SnippetPlugin":
                new_grouper_id = SNIPPET_GROUPER_FR_TO_EN.get(new_plugin.snippet_grouper_id)
                if new_grouper_id:
                    new_plugin.snippet_grouper_id = new_grouper_id
                    new_plugin.save()
                continue

            field = TRANSLATABLE_PLUGIN_FIELDS.get(source_plugin.plugin_type)
            if not field:
                continue

            if source_plugin.pk in plugin_texts:
                text = plugin_texts[source_plugin.pk]
            elif (getattr(source_plugin, field, "") or "").strip():
                missing_translations.append(source_plugin.pk)
                text = getattr(new_plugin, field)
            else:
                continue

            text = replace_plugin_tags(text, id_map)
            setattr(new_plugin, field, text)
            new_plugin.save()

        if missing_translations:
            self.stderr.write(
                self.style.WARNING(
                    f"No translation provided for source plugin ids {missing_translations}; "
                    "their French text was copied as-is."
                )
            )

        ct = ContentType.objects.get_for_model(PageContent)
        version = Version.objects.get(content_type=ct, object_id=target_content.pk)
        version.publish(user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Published page {page_id} ('{fields['title']}') in '{target_lang}' "
                f"(PageContent id {target_content.pk})"
            )
        )
