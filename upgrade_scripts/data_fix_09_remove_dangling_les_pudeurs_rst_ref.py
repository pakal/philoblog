"""
One-off data fix, to run when/before upgrading cmsplugin-rst to 0.3: that release stops silently
swallowing ":cmspage:" roles pointing at a missing/unpublished page, and instead renders a visible
"System Message: ERROR ... Targeted reverse ID of published page doesn't exist" in the page.

The "la-foret-des-libertes" RstPlugin body still references ":cmspage:`les-pudeurs`", a page that
was removed earlier in the upgrade ladder (it no longer exists at all). Drops the dead
cross-reference, keeping the surrounding prose, which is how it effectively rendered before
(the old cmsplugin-rst silently emitted nothing for this broken role). Idempotent.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_09_remove_dangling_les_pudeurs_rst_ref.py').read())"
"""
from cmsplugin_rst.models import RstPluginModel

OLD = "sans égard pour la sensibilité de leurs congénères (cf. :cmspage:`les-pudeurs`)."
NEW = "sans égard pour la sensibilité de leurs congénères."

count = 0
for plugin in RstPluginModel.objects.filter(body__contains=OLD):
    plugin.body = plugin.body.replace(OLD, NEW)
    plugin.save(update_fields=["body"])
    count += 1
print("%s RstPlugin bodies de-referenced from the removed 'les-pudeurs' page" % count)
