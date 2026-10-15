"""
One-off data fix, to run when deploying the code which removes the Twitter feed sidebar: the "*_notwitter.html"
templates are merged into their base templates, so the page contents (of all versions: draft, published, archived)
still using them are re-pointed to the base templates. Idempotent.

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_08_merge_notwitter_templates.py').read())"
"""
from cms.models import PageContent

for old_template, new_template in [("single_article_notwitter.html", "single_article.html"),
                                   ("homepage_notwitter.html", "homepage.html")]:
    count = PageContent.admin_manager.filter(template=old_template).update(template=new_template)
    print("%s page contents switched from %s to %s" % (count, old_template, new_template))
