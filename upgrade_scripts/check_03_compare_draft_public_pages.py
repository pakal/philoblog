"""
Read-only check (django-cms 3.11 -> 5.0 upgrade), to run BEFORE data_fix_03: for every cms3 page,
compare its draft and public copies (page/title fields, and every placeholder's plugin tree with
plugin subclass data), to know whether merging them into one cms4 page loses anything.

Run via: manage.py shell -c "exec(open('upgrade_scripts/check_03_compare_draft_public_pages.py').read())"
"""
import re
from collections import defaultdict

from django.db import connection

cur = connection.cursor()


def fetch_dicts(sql, params=()):
    cur.execute(sql, params)
    columns = [col[0] for col in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


PAGE_FIELDS = ["template", "in_navigation", "reverse_id", "soft_root", "navigation_extenders", "login_required",
               "limit_visibility_in_menu", "is_home", "application_urls", "application_namespace", "xframe_options",
               "is_page_type", "publication_date", "publication_end_date"]
TITLE_FIELDS = ["language", "title", "page_title", "menu_title", "meta_description", "slug", "path",
                "has_url_overwrite", "redirect", "published"]


def plugin_subclass_tables():
    from cms.plugin_pool import plugin_pool
    tables = {}
    for plugin in plugin_pool.get_all_plugins():
        model = plugin.model
        if model._meta.db_table != "cms_cmsplugin":
            tables[plugin.__name__] = model._meta.db_table
    return tables


TABLES = plugin_subclass_tables()


def plugin_tree(placeholder_id):
    plugins = fetch_dicts("SELECT id, parent_id, position, language, plugin_type FROM cms_cmsplugin"
                          " WHERE placeholder_id = %s ORDER BY language, parent_id, position", [placeholder_id])
    ids = {p["id"]: i for i, p in enumerate(sorted(plugins, key=lambda p: (p["language"], p["position"], p["id"])))}
    result = []
    for p in plugins:
        data = {}
        table = TABLES.get(p["plugin_type"])
        if table:
            rows = fetch_dicts("SELECT * FROM %s WHERE cmsplugin_ptr_id = %%s" % table, [p["id"]])
            data = rows[0] if rows else {"GHOST": True}
            data.pop("cmsplugin_ptr_id", None)
            for key, value in list(data.items()):
                if isinstance(value, str):  # text bodies reference child plugins by id
                    data[key] = re.sub(r'\bid="\d+"', 'id="X"', value)
        result.append((p["language"], ids.get(p["parent_id"]), p["position"], p["plugin_type"], sorted(data.items())))
    return sorted(result, key=repr)


def page_content(page_id):
    page = fetch_dicts("SELECT * FROM cms_page WHERE id = %s", [page_id])[0]
    titles = fetch_dicts("SELECT * FROM cms_title WHERE page_id = %s ORDER BY language", [page_id])
    placeholders = fetch_dicts("SELECT ph.id, ph.slot FROM cms_placeholder ph JOIN cms_page_placeholders pp"
                               " ON pp.placeholder_id = ph.id WHERE pp.page_id = %s ORDER BY ph.slot", [page_id])
    return {
        "page": {f: page[f] for f in PAGE_FIELDS},
        "titles": [{f: t[f] for f in TITLE_FIELDS} for t in titles],
        "placeholders": {ph["slot"]: plugin_tree(ph["id"]) for ph in placeholders},
    }


by_node = defaultdict(dict)
for row in fetch_dicts("SELECT id, node_id, publisher_is_draft FROM cms_page"):
    by_node[row["node_id"]]["draft" if row["publisher_is_draft"] else "public"] = row["id"]

identical, different = 0, 0
for node_id, pages in sorted(by_node.items()):
    if set(pages) != {"draft", "public"}:
        print("node %s: unpaired %s" % (node_id, pages))
        continue
    draft, public = page_content(pages["draft"]), page_content(pages["public"])
    title = draft["titles"][0]["path"] if draft["titles"] else "?"
    if draft == public:
        identical += 1
        continue
    different += 1
    print("node %s (draft %s / public %s) '%s' DIFFERS:" % (node_id, pages["draft"], pages["public"], title))
    for key in ("page", "titles"):
        if draft[key] != public[key]:
            print("   %s: draft=%s\n   %s  public=%s" % (key, draft[key], " " * len(key), public[key]))
    for slot in sorted(set(draft["placeholders"]) | set(public["placeholders"])):
        d, p = draft["placeholders"].get(slot), public["placeholders"].get(slot)
        if d != p:
            only_d = [x for x in (d or []) if x not in (p or [])]
            only_p = [x for x in (p or []) if x not in (d or [])]
            print("   slot %r: %d plugins only in draft, %d only in public" % (slot, len(only_d), len(only_p)))
            for x in only_d:
                print("      draft :", repr(x)[:300])
            for x in only_p:
                print("      public:", repr(x)[:300])

print("identical pairs:", identical, "- differing pairs:", different)
