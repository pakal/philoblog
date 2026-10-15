"""
One-off data fix, phase A of the django-cms 3.11 -> 5.0 upgrade, to run on the cms 3.11 schema
(i.e. BEFORE installing django-cms 5), after check_03_compare_draft_public_pages.py was reviewed.

django-cms 3 stores every page twice (a draft and a public Page row, sharing one TreeNode, each
with its own Titles/placeholders/plugins); django-cms 4+ has a single Page per tree node, with
draft/published states handled by djangocms-versioning on PageContent (the former Title).
cms.0031 drops the publisher_is_draft / published columns, so this phase records, while they
still exist, everything phases B and C need, in a temporary table "upgrade_cms4_titles":
  - title_id (= future PageContent id), page_id, draft_page_id (the Page row which survives)
  - origin: "draft" or "public" copy
  - is_live: whether the public copy of this page+language is currently published
  - same_as_public: for draft titles, whether draft content == public content (page settings,
    title fields, and every placeholder's plugin tree with plugin data)

It also deletes "ghost" plugins (cms_cmsplugin rows of a subclassed plugin type without their
subclass row, which render nothing), which would otherwise make some identical pairs differ.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_03a_cms4_record_page_pairs.py').read())"
"""
from django.db import connection, transaction

exec(open("upgrade_scripts/check_03_compare_draft_public_pages.py", encoding="utf8").read().split("by_node = defaultdict")[0])

with transaction.atomic():
    ghosts = []
    for plugin_type, table in TABLES.items():
        cur.execute("SELECT p.id FROM cms_cmsplugin p LEFT JOIN %s s ON s.cmsplugin_ptr_id = p.id"
                    " WHERE p.plugin_type = %%s AND s.cmsplugin_ptr_id IS NULL" % table, [plugin_type])
        ghosts += [r[0] for r in cur.fetchall()]
    for ghost_id in ghosts:
        cur.execute("SELECT COUNT(*) FROM cms_cmsplugin WHERE parent_id = %s", [ghost_id])
        assert cur.fetchone()[0] == 0, "ghost plugin %s has children" % ghost_id
    if ghosts:
        cur.execute("DELETE FROM cms_cmsplugin WHERE id IN (%s)" % ",".join(map(str, ghosts)))
    print("deleted ghost plugins:", ghosts)

cur.execute("DROP TABLE IF EXISTS upgrade_cms4_titles")
cur.execute("""CREATE TABLE upgrade_cms4_titles (
    title_id INT PRIMARY KEY, page_id INT NOT NULL, draft_page_id INT NOT NULL, language VARCHAR(15) NOT NULL,
    origin VARCHAR(10) NOT NULL, is_live BOOL NOT NULL, same_as_public BOOL NULL)""")

with transaction.atomic():
    pages = fetch_dicts("SELECT id, node_id, publisher_is_draft, publisher_public_id FROM cms_page")
    draft_by_node = {p["node_id"]: p["id"] for p in pages if p["publisher_is_draft"]}
    public_by_node = {p["node_id"]: p["id"] for p in pages if not p["publisher_is_draft"]}
    assert len(draft_by_node) + len(public_by_node) == len(pages), "nodes with several drafts or publics"
    assert set(public_by_node) <= set(draft_by_node), "public page without draft"

    stats = defaultdict(int)
    for node_id, draft_id in draft_by_node.items():
        public_id = public_by_node.get(node_id)
        draft_titles = {t["language"]: t for t in fetch_dicts("SELECT * FROM cms_title WHERE page_id = %s", [draft_id])}
        public_titles = {t["language"]: t for t in fetch_dicts("SELECT * FROM cms_title WHERE page_id = %s", [public_id])} if public_id else {}
        draft_content = page_content(draft_id)
        public_content = page_content(public_id) if public_id else None
        for language, title in draft_titles.items():
            public_title = public_titles.get(language)
            is_live = bool(public_title and public_title["published"])
            same = None
            if public_title:
                filter_lang = lambda c: {  # noqa: E731
                    "page": c["page"],
                    "titles": [t for t in c["titles"] if t["language"] == language],
                    "placeholders": {slot: [p for p in plugins if p[0] == language] for slot, plugins in c["placeholders"].items()},
                }
                same = filter_lang(draft_content) == filter_lang(public_content)
            cur.execute("INSERT INTO upgrade_cms4_titles VALUES (%s, %s, %s, %s, 'draft', %s, %s)",
                        [title["id"], draft_id, draft_id, language, is_live, same])
            stats["draft live=%s same=%s" % (is_live, same)] += 1
            if public_title:
                cur.execute("INSERT INTO upgrade_cms4_titles VALUES (%s, %s, %s, %s, 'public', %s, NULL)",
                            [public_title["id"], public_id, draft_id, language, is_live])
                stats["public live=%s" % is_live] += 1
        assert set(public_titles) <= set(draft_titles), "public title without draft title on node %s" % node_id

for key, count in sorted(stats.items()):
    print("%-30s %s" % (key, count))
