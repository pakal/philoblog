# Upstream djangocms-page-sitemap 1.4.0 dropped the "public_extension" field from
# PageSitemapProperties (obsolete since django-cms 4+ merged draft/public pages) but
# never shipped the migration removing it - see MIGRATION_MODULES override in settings.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('djangocms_page_sitemap', '0005_auto_20180324_1050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pagesitemapproperties',
            name='public_extension',
        ),
    ]
