"""
One-off data fix, to run right BEFORE deploying the code which restores USE_TZ = True: with USE_TZ = False, datetimes
were stored as naive Europe/Paris local times, whereas with USE_TZ = True Django stores (and reads) them as naive UTC
times on MySQL/MariaDB. So every DateTimeField column of the installed models is shifted from Europe/Paris to UTC.

The conversion is done in Python (zoneinfo), so it doesn't need the MariaDB time zone tables; for ambiguous local
times (the repeated hour when DST ends), the first occurrence is assumed.

Not idempotent by nature: a marker table is created at the end, and the script refuses to run again if it exists.
Back up the database first; all updates are done in a single transaction.

Ops note: with USE_TZ = True, date truncations in SQL (e.g. admin date_hierarchy, dates()/datetimes() querysets) use
CONVERT_TZ(), which needs the MariaDB time zone tables, else they fail with "Database returned an invalid datetime
value. Are time zone definitions for your database installed?" (the original reason for USE_TZ = False on O2SWITCH).
Load them with: mariadb-tzinfo-to-sql /usr/share/zoneinfo | mariadb -u root mysql

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_07_convert_datetimes_to_utc.py').read())"
"""
import datetime
import zoneinfo

from django.apps import apps
from django.db import connection, models, transaction

MARKER_TABLE = "upgrade_marker_datetimes_to_utc"
PARIS = zoneinfo.ZoneInfo("Europe/Paris")

existing_tables = set(connection.introspection.table_names())
assert MARKER_TABLE not in existing_tables, "Datetimes were already converted to UTC, aborting"

# {table: (pk column, [datetime columns])}
tables = {}
for model in apps.get_models(include_auto_created=True):
    meta = model._meta
    if meta.proxy or not meta.managed or meta.db_table not in existing_tables:
        continue
    columns = [field.column for field in meta.local_concrete_fields if isinstance(field, models.DateTimeField)]
    if columns:
        pk_column, known_columns = tables.setdefault(meta.db_table, (meta.pk.column, []))
        known_columns.extend(column for column in columns if column not in known_columns)


def to_utc(value):
    return value.replace(tzinfo=PARIS).astimezone(datetime.UTC).replace(tzinfo=None)


qn = connection.ops.quote_name
cur = connection.cursor()
# created first, since DDL statements implicitly commit the current transaction on MariaDB
cur.execute("CREATE TABLE %s (converted_at DATETIME NOT NULL)" % qn(MARKER_TABLE))
try:
    with transaction.atomic():
        for table, (pk_column, columns) in sorted(tables.items()):
            cur.execute("SELECT %s, %s FROM %s" % (qn(pk_column), ", ".join(qn(c) for c in columns), qn(table)))
            rows = cur.fetchall()
            set_clause = ", ".join("%s = %%s" % qn(c) for c in columns)
            cur.executemany(
                "UPDATE %s SET %s WHERE %s = %%s" % (qn(table), set_clause, qn(pk_column)),
                [[to_utc(value) if value is not None else None for value in row[1:]] + [row[0]] for row in rows],
            )
            print("converted %s rows of %s (%s)" % (len(rows), table, ", ".join(columns)))
        cur.execute("INSERT INTO %s VALUES (UTC_TIMESTAMP())" % qn(MARKER_TABLE))
except BaseException:
    cur.execute("DROP TABLE %s" % qn(MARKER_TABLE))
    raise
print("%s tables converted from Europe/Paris to UTC" % len(tables))
