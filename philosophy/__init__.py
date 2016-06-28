
# Misc setups and monkey-patchings

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
