"""
One-off data fix (MariaDB >= 10.10 only): convert the database and all its tables from the legacy utf8mb3 (and a few
latin1) charsets to utf8mb4 with the Unicode 14 collation utf8mb4_uca1400_ai_ci (accent and case insensitive), so
that 4-byte characters (emoji, some CJK/math symbols) can be stored, and so that tables created later by migrations
get the same collation as existing ones (else some joins fail with "Illegal mix of collations").

The latin1 columns (django-request, django-reversion and unused leftovers) only contain ASCII, apart from a few
user agents already mangled when they were inserted, so they convert as is.

Idempotent. Back up the database first: DDL statements are not transactional on MariaDB.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_05_convert_db_to_utf8mb4.py').read())"
"""
from django.db import connection

CHARSET, COLLATION = "utf8mb4", "utf8mb4_uca1400_ai_ci"

cur = connection.cursor()
cur.execute("SELECT DATABASE()")
db_name = cur.fetchone()[0]
cur.execute("ALTER DATABASE `%s` CHARACTER SET %s COLLATE %s" % (db_name, CHARSET, COLLATION))

# tables whose default collation or any text column's collation differs
cur.execute("""SELECT DISTINCT t.table_name FROM information_schema.tables t
               LEFT JOIN information_schema.columns c ON c.table_schema = t.table_schema AND c.table_name = t.table_name
               WHERE t.table_schema = %s AND t.table_type = 'BASE TABLE'
               AND (t.table_collation <> %s OR (c.collation_name IS NOT NULL AND c.collation_name <> %s))""",
            [db_name, COLLATION, COLLATION])
tables = sorted(row[0] for row in cur.fetchall())

cur.execute("SET FOREIGN_KEY_CHECKS = 0")  # columns linked by foreign keys are converted one table at a time
try:
    for table in tables:
        cur.execute("ALTER TABLE `%s` CONVERT TO CHARACTER SET %s COLLATE %s" % (table, CHARSET, COLLATION))
        print("converted", table)
finally:
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
print("%s tables converted to %s / %s" % (len(tables), CHARSET, COLLATION))
