"""
One-off data fix, to run BEFORE deploying the code which removes django-request (hit-logging analytics, too heavy):
drops its "request_request" table and its django_migrations rows, while the app is still installed.

The table is emptied first, since the reverse migrations alter columns and fail on existing rows (e.g. "Data truncated
for column 'ip'"); its data is not kept anyway. Idempotent.

After deploying, run "manage.py remove_stale_contenttypes --include-stale-apps" (interactively, to review the objects
it cascade-deletes) to remove the leftover content type and permissions; this also cleans up the leftovers of other
apps removed during the upgrade ladder (cmsplugin_filer_*, djangocms_text_ckeditor...).

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_06_drop_django_request.py').read())"
"""
from django.core.management import call_command
from django.db import connection

if "request_request" in connection.introspection.table_names():
    connection.cursor().execute("TRUNCATE TABLE request_request")
call_command("migrate", "request", "zero")
