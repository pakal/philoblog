from django.contrib import admin
from newsletter.models import Message, Submission, Subscription

# With USE_TZ = True, the date_hierarchy of changelists truncates dates via CONVERT_TZ(), which fails without the
# MariaDB time zone tables ("Database returned an invalid datetime value...") - and some hostings don't provide them
for model in (Message, Submission, Subscription):
    admin.site._registry[model].date_hierarchy = None
