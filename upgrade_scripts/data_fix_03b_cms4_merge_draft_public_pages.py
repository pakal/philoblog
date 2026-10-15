"""
One-off data fix, phase B of the django-cms 3.11 -> 5.0 upgrade, to run with django-cms 5 installed, after
    manage.py migrate cms 0035_auto_20230822_2208_squashed_0036_auto_20240311_1028
    manage.py migrate djangocms_versioning 0009_cms_pagecontent_remove_unique_constraint
(the latter drops the cms3 unique key on (language, page) of PageContent, the former Title), and BEFORE the
full `migrate` (cms.0037_merge_page_treenode asserts that each tree node has a single Page).

Beware: tables created by these migrations get the database's default collation, which must match the one
of the legacy tables (utf8mb3_general_ci here), else some joins fail with "Illegal mix of collations".

Using the "upgrade_cms4_titles" table recorded by phase A, each public Page row is merged into its draft Page
row (whose id is the one referenced by link/picture plugins, menus, etc.):
  - the public PageContents (former Titles, still owning their placeholders and plugins) are repointed to the
    draft Page, so that each page+language temporarily has 2 PageContents; phase C turns them into
    djangocms-versioning versions (published / draft) and removes the redundant ones
  - any other foreign key to a public Page is repointed to the draft Page, except for per-page rows which only
    duplicate the draft ones (PageUrl, permissions, page extensions), which are deleted
  - the public Page rows are deleted

Also drops the tables of the retired, unused (0 rows) djangocms-page-tags / django-taggit / taggit-autosuggest.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_03b_cms4_merge_draft_public_pages.py').read())"
"""
from django.apps import apps
from django.db import connection, transaction

cur = connection.cursor()

# rows duplicating, for the public copy, those of the draft page
DELETED_PER_PAGE_TABLES = ["cms_pageurl", "cms_pagepermission", "djangocms_page_sitemap_pagesitemapproperties"]

cur.execute("SELECT DISTINCT page_id, draft_page_id FROM upgrade_cms4_titles WHERE origin = 'public'")
public_to_draft = dict(cur.fetchall())
cur.execute("SELECT id FROM cms_page WHERE id NOT IN (SELECT draft_page_id FROM upgrade_cms4_titles)")
public_ids = sorted(r[0] for r in cur.fetchall())
# a public page without any title would not be listed by phase A
assert public_ids == sorted(public_to_draft), (public_ids, sorted(public_to_draft))
ids_sql = ",".join(map(str, public_ids))

page_model = apps.get_model("cms", "Page")
fk_columns = sorted({
    (model._meta.db_table, field.column)
    for model in apps.get_models(include_auto_created=True)
    for field in model._meta.concrete_fields
    if field.is_relation and field.related_model is page_model
})
cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = DATABASE()")
db_columns = set(cur.fetchall())

with transaction.atomic():
    cur.execute("UPDATE cms_pagecontent c JOIN upgrade_cms4_titles t ON t.title_id = c.id SET c.page_id = t.draft_page_id"
                " WHERE t.origin = 'public'")
    print("public PageContents moved to their draft page:", cur.rowcount)

    for table in DELETED_PER_PAGE_TABLES:
        column = "extended_object_id" if table.startswith("djangocms_page_sitemap") else "page_id"
        cur.execute("DELETE FROM %s WHERE %s IN (%s)" % (table, column, ids_sql))
        print("deleted public rows of %s: %s" % (table, cur.rowcount))

    for table, column in fk_columns:
        if table in DELETED_PER_PAGE_TABLES or table == "cms_page":
            continue
        if (table, column) not in db_columns:
            print("skipped %s.%s (not in the database yet)" % (table, column))
            continue
        moved = 0
        for public_id, draft_id in public_to_draft.items():
            cur.execute("UPDATE %s SET %s = %%s WHERE %s = %%s" % (table, column, column), [draft_id, public_id])
            moved += cur.rowcount
        print("%s.%s: %s references to public pages repointed" % (table, column, moved))

    cur.execute("DELETE FROM cms_page WHERE id IN (%s)" % ids_sql)
    print("deleted public pages:", cur.rowcount)

    cur.execute("SELECT node_id, COUNT(*) FROM cms_page GROUP BY node_id HAVING COUNT(*) > 1")
    assert not cur.fetchall(), "several pages left for some tree nodes"

# DDL auto-commits on MariaDB, so done after the data transaction
for table in ["djangocms_page_tags_pagetags_tags", "djangocms_page_tags_titletags_tags", "djangocms_page_tags_pagetags",
              "djangocms_page_tags_titletags", "taggit_taggeditem", "taggit_tag"]:
    cur.execute("DROP TABLE IF EXISTS %s" % table)
cur.execute("DELETE FROM django_migrations WHERE app IN ('djangocms_page_tags', 'taggit', 'taggit_autosuggest')")
cur.execute("DELETE p FROM auth_permission p JOIN django_content_type ct ON ct.id = p.content_type_id"
            " WHERE ct.app_label IN ('djangocms_page_tags', 'taggit', 'taggit_autosuggest')")
cur.execute("DELETE FROM django_content_type WHERE app_label IN ('djangocms_page_tags', 'taggit', 'taggit_autosuggest')")
print("dropped djangocms-page-tags and django-taggit tables")
