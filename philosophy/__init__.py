
# Misc setups and monkey-patchings, applied as soon as settings get loaded, i.e. BEFORE django.setup()
# Each patch documents which package/Django version needs it, and is version-guarded when possible.

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
else:
    import django

    if django.VERSION < (3, 0):
        # Django 2.2 expects mysqlclient's bytes "_executed", PyMySQL 1.x gives str (crashes the DEBUG
        # SQL logging); backport of the Django 3.0 implementation, which already does this natively.
        from django.db.backends.mysql.operations import DatabaseOperations
        from django.utils.encoding import force_str
        DatabaseOperations.last_executed_query = \
            lambda self, cursor, sql, params: force_str(getattr(cursor, "_executed", None), errors="replace")
