"""
One-off data fix, phase C of the django-cms 3.11 -> 5.0 upgrade, to run after phase B and the full `migrate`:
creates the djangocms-versioning Version rows, without which no page content nor snippet is visible.

Using the "upgrade_cms4_titles" table recorded by phase A, for each page+language:
  - published page: the content coming from the cms3 public copy becomes the PUBLISHED version; the one coming
    from the draft copy becomes a DRAFT version (the pending, unpublished changes) if it differed, else it is
    deleted with its placeholders and plugins
  - never published page: the content coming from the draft copy becomes a DRAFT version, the one coming from
    the (unpublished, possibly outdated) public copy is deleted
Version dates are set to the content's last change date. Snippets (a single copy in cms3) become PUBLISHED.
Finally the "upgrade_cms4_titles" table is dropped.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_03c_cms4_create_versions.py').read())"
"""
from collections import Counter

from cms.models import PageContent
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from djangocms_snippet.models import Snippet
from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.models import Version

cur = connection.cursor()
user = get_user_model().objects.filter(is_superuser=True).order_by("pk").first()


def delete_content(content):
    for placeholder in content.placeholders.all():
        placeholder.clear()
        placeholder.delete()
    content.delete()


with transaction.atomic():
    assert not Version.objects.exists()
    cur.execute("SELECT title_id, origin, is_live, same_as_public FROM upgrade_cms4_titles ORDER BY origin DESC, title_id")  # published versions get #1
    stats = Counter()
    for title_id, origin, is_live, same_as_public in cur.fetchall():
        content = PageContent.admin_manager.get(pk=title_id)
        if origin == "public":
            state = PUBLISHED if is_live else None
        else:
            state = None if (is_live and same_as_public) else DRAFT
        if state is None:
            delete_content(content)
            stats["%s content deleted" % origin] += 1
            continue
        version = Version.objects.create(content=content, state=state, created_by=user)
        Version.objects.filter(pk=version.pk).update(created=content.changed_date, modified=content.changed_date)
        stats["%s content -> %s version" % (origin, state)] += 1

    for snippet in Snippet.admin_manager.all():
        Version.objects.create(content=snippet, state=PUBLISHED, created_by=user)
        stats["snippet -> published version"] += 1

    assert not PageContent.admin_manager.exclude(pk__in=Version.objects.filter(
        content_type__model="pagecontent").values("object_id")).exists()

for key, count in sorted(stats.items()):
    print("%-40s %s" % (key, count))

cur.execute("DROP TABLE upgrade_cms4_titles")
