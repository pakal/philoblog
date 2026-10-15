"""
One-off data fix (django-cms upgrade ladder), to run on django-cms 5.0 BEFORE upgrading to django-cms 5.1, whose
migration cms.0042 deletes the StaticPlaceholder model (and its table).

Converts every static placeholder into the djangocms-alias "static alias" which the {% static_alias %} template
tag looks up (same static_code, no site, "Static Alias" category, one AliasContent per language whose placeholder
slot is the static_code), as a PUBLISHED version holding the plugins of the public copy, which are moved, not copied.

All static placeholders are global (site NULL) and none has unpublished changes ("dirty" flag unset): this is
asserted, by comparing the plugin trees of the draft and public copies, before deleting the draft copies.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_04_static_placeholders_to_static_aliases.py').read())"
"""
from cms.models import Placeholder
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from djangocms_alias.constants import DEFAULT_STATIC_ALIAS_CATEGORY_NAME
from djangocms_alias.models import Alias, AliasContent, Category
from djangocms_versioning.models import Version

# plugin_tree() and fetch_dicts() helpers
exec(open("upgrade_scripts/check_03_compare_draft_public_pages.py", encoding="utf8").read().split("def page_content")[0])

user = get_user_model().objects.filter(is_superuser=True).order_by("pk").first()

with transaction.atomic():
    category = Category.objects.filter(translations__name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME).first()
    if not category:
        category = Category.objects.create(name=DEFAULT_STATIC_ALIAS_CATEGORY_NAME)

    for static in fetch_dicts("SELECT * FROM cms_staticplaceholder ORDER BY id"):
        code = static["code"]
        assert static["site_id"] is None, "per-site static placeholders need {% static_alias ... site %}"
        draft_tree, public_tree = plugin_tree(static["draft_id"]), plugin_tree(static["public_id"])
        assert not static["dirty"] and draft_tree == public_tree, "%s has unpublished changes" % code
        assert not Alias.objects.filter(static_code=code).exists(), code

        alias = Alias.objects.create(category=category, static_code=code, creation_method=Alias.CREATION_BY_TEMPLATE)
        cur.execute("SELECT DISTINCT language FROM cms_cmsplugin WHERE placeholder_id = %s", [static["public_id"]])
        languages = [row[0] for row in cur.fetchall()] or [settings.LANGUAGE_CODE]
        for language in languages:
            content = AliasContent.objects.with_user(user).create(alias=alias, name=code, language=language)
            cur.execute("UPDATE cms_cmsplugin SET placeholder_id = %s WHERE placeholder_id = %s AND language = %s",
                        [content.placeholder.pk, static["public_id"], language])
            moved = cur.rowcount
            Version.objects.get_for_content(content).publish(user)
            print("static placeholder %r (%s): %s plugins moved to a published static alias" % (code, language, moved))

        cur.execute("SELECT COUNT(*) FROM cms_cmsplugin WHERE placeholder_id = %s", [static["public_id"]])
        assert cur.fetchone()[0] == 0
        cur.execute("DELETE FROM cms_staticplaceholder WHERE id = %s", [static["id"]])
        for placeholder in Placeholder.objects.filter(pk__in=[static["draft_id"], static["public_id"]]):
            placeholder.clear()  # the draft copy is identical, see above
            placeholder.delete()
