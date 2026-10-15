"""
One-off data fix (django-cms upgrade ladder): replace every djangocms-inherit
"InheritPagePlaceholderPlugin" by an equivalent "SnippetPlugin", IN PLACE.

djangocms-inherit is abandoned (last PyPI release 0.2.2 can't even render on django-cms 3.6 -
"'SnippetPtr' object has no attribute 'render_plugin'", the isotoma git fork that worked is gone
from GitHub) and has no django-cms 4+ release.

On this site, every inherit plugin sits alone in an article's "intro" placeholder, and inherits
the "intro" placeholder of its section page, which itself only holds a single SnippetPlugin
(identical on the draft and public copies of the section). So each inherit plugin is swapped
for a SnippetPlugin pointing to that same Snippet: the cms_cmsplugin row (placeholder, position,
tree path) is kept, only its subclass row and plugin_type change. Snippets being shared objects,
editing a section intro snippet still updates all its articles.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_01_inherit_to_snippet.py').read())"
"""
from django.db import connection, transaction

cur = connection.cursor()

with transaction.atomic():
    cur.execute("""
        SELECT i.cmsplugin_ptr_id, i.from_page_id FROM djangocms_inherit_inheritpageplaceholder i
        JOIN cms_cmsplugin pl ON pl.id = i.cmsplugin_ptr_id
        WHERE pl.plugin_type = 'InheritPagePlaceholderPlugin'
    """)
    inherit_rows = cur.fetchall()
    print("inherit plugins:", len(inherit_rows))

    for plugin_id, from_page_id in inherit_rows:
        # Snippets in the "intro" slot of the source page (both draft and public copies, sharing the node)
        cur.execute("""
            SELECT DISTINCT s.snippet_id FROM cms_page p
            JOIN cms_page_placeholders pp ON pp.page_id = p.id
            JOIN cms_placeholder ph ON ph.id = pp.placeholder_id AND ph.slot = 'intro'
            JOIN cms_cmsplugin pl ON pl.placeholder_id = ph.id
            JOIN djangocms_snippet_snippetptr s ON s.cmsplugin_ptr_id = pl.id
            WHERE p.node_id = (SELECT node_id FROM cms_page WHERE id = %s)
        """, [from_page_id])
        snippet_ids = [r[0] for r in cur.fetchall()]
        assert len(snippet_ids) == 1, (plugin_id, from_page_id, snippet_ids)

        cur.execute("INSERT INTO djangocms_snippet_snippetptr (cmsplugin_ptr_id, snippet_id) VALUES (%s, %s)",
                    [plugin_id, snippet_ids[0]])
        cur.execute("DELETE FROM djangocms_inherit_inheritpageplaceholder WHERE cmsplugin_ptr_id = %s", [plugin_id])
        cur.execute("UPDATE cms_cmsplugin SET plugin_type = 'SnippetPlugin' WHERE id = %s", [plugin_id])
        print("  plugin %s: inherit from page %s -> snippet %s" % (plugin_id, from_page_id, snippet_ids[0]))

cur.execute("SELECT COUNT(*) FROM cms_cmsplugin WHERE plugin_type = 'InheritPagePlaceholderPlugin'")
print("remaining InheritPagePlaceholderPlugin:", cur.fetchone()[0])
