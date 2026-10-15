import copy
import os

gettext = lambda s: s

# Build paths inside the project like this: os.path.join(ROOT_DIR, ...)
import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print("ROOT_DIR", ROOT_DIR)


# Application definition

ROOT_URLCONF = 'philosophy.urls'

WSGI_APPLICATION = 'philosophy.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

# Datetimes stored in UTC (see upgrade_scripts/data_fix_07_convert_datetimes_to_utc.py); SQL date truncations need the
# MariaDB time zone tables, else "Database returned an invalid datetime value. Are time zone definitions installed?"
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
STATICFILES_DIRS = (
)
SITE_ID = 1

# Keep historical int primary keys (no schema change), silences models.W042 since Django 3.2
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_DIR, 'philosophy', 'templates'), ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.static',
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

MIDDLEWARE = [
    "philosophy.middlewares.ReverseProxyFixer",
    # 'cms.middleware.utils.ApphookReloadMiddleware' -> enable this to autoreload server when apphooks are modified
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

INSTALLED_APPS = [
    'djangocms_admin_style',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.redirects',

    'cms',
    'menus',
    'sekizai',
    'treebeard',
    'parler',
    'djangocms_versioning',
    'djangocms_alias',
    'djangocms_text',
    'filer',
    'easy_thumbnails',
    'djangocms_picture',
    'djangocms_file',
    'djangocms_snippet',
    'djangocms_link',
    'cmsplugin_rst',
    'cmsplugin_raw_html',

    'djangocms_page_sitemap',

    'terms',

    # BREAKS django-terms, so don't use it
    # and don't even install it: 'softhyphen'

    'reversion',
    'compressor',

    'tinymce',
    'django_extensions',
    'newsletter',

    'philosophy'
]

LANGUAGES = (
    ## Customize this
    ('fr', gettext('French')),
    #('en', gettext('English')),
)

CMS_LANGUAGES = {
    ## Customize this
    1 : [
        {
            'redirect_on_fallback': True,
            'code': 'fr',
            'hide_untranslated': False,
            'public': True,
            'name': gettext('fr'),
        },
        #{
        #    'redirect_on_fallback': True,
        #    'code': 'en',
        #    'hide_untranslated': False,
        #    'public': True,
        #    'name': gettext('en'),
        #},
    ],
    'default': {
        'redirect_on_fallback': True,
        'public': True,
        'hide_untranslated': False,
    },
}
CMS_LANGUAGES[2] = copy.deepcopy(CMS_LANGUAGES[1])  # SAME CONF FOR BOTH SITE IDS (a copy, since django-parler mutates it)

CMS_TEMPLATES = (
    ## Customize this
    ('single_article.html', 'Single Article'),
    ('page.html', 'Page'),
    ('homepage.html', 'Homepage'),
)

CMS_PERMISSION = True
CMS_PUBLIC_FOR = "all"   # or "staff"

CMS_TEMPLATE_INHERITANCE = True
CMS_PLACEHOLDER_CONF = {}  # unused atm
CMS_PLUGIN_CONTEXT_PROCESSORS = []
CMS_PLUGIN_PROCESSORS = []
CMS_UNESCAPED_RENDER_MODEL_TAGS = False

CMS_CACHE_DURATIONS = {  # in seconds
    'menus': 60 * 60,
    'content': 60,
    'permissions': 60 * 60,
}

CMS_CACHE_PREFIX = "philocms-"  # useful if multiple CMS installations
CMS_PAGE_CACHE = True
CMS_PLACEHOLDER_CACHE = True
CMS_PLUGIN_CACHE = True

CMS_CONFIRM_VERSION4 = True  # the database was migrated from django-cms 3, see upgrade_scripts/data_fix_03*

CMS_TOOLBARS = None  # all, by default
CMS_TOOLBAR_ANONYMOUS_ON = True
CMS_TOOLBAR_HIDE = False


## django-compat-patcher settings, restoring Django APIs still used by old dependencies
from django_compat_patcher.default_settings import DCP_EXCLUDE_FIXER_IDS as _DCP_DEFAULT_EXCLUDES
DCP_EXCLUDE_FIXER_IDS = _DCP_DEFAULT_EXCLUDES + [
    # unneeded, and its "callable booleans" fail the auth.C009/C010 checks of Django 6.1
    "fix_behaviour_contrib_auth_user_is_anonymous_is_authenticated_callability",
]

MIGRATION_MODULES = {
}

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters'
)

## Django-compressor settings

COMPRESS_ENABLED = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "compressor": {"BACKEND": "compressor.storage.CompressorFileStorage"},
}

COMPRESS_PRECOMPILERS = (
    # unused('text/x-scss', 'django_libsass.SassCompiler'),
)


## djangocms-text settings (TipTap editor, accepting the toolbar format of the former CKEditor 4) ##

TEXT_EDITOR_SETTINGS = {
            'toolbar_CMS': [
                ['Undo', 'Redo'],
                ['CMSPlugins', '-', 'ShowBlocks'],
                ['Font', 'FontSize', 'Format', 'Styles'],
                ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                ['Maximize', ''],
                '/',
                ['Bold', 'Italic', 'Underline', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                ['CreateDiv', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
                ['Link', 'Unlink'],
                ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Table'],
                ['Source']
            ],
}

CMSPLUGIN_RST_SETTINGS_OVERRIDES = {"initial_header_level": 2, # minimum "h2" when rendered to html
                                    "smart_quotes": "alt"}


CMS_PLUGIN_PROCESSORS = (
    'terms.cms_plugin_processors.TermsProcessor',
)

TERMS_ENABLED = True
TERMS_DEFINITION_WIDGET = "basic"  # so that we can input html ; choices are 'auto', 'basic', 'tinymce', and 'ckeditor'
TERMS_REPLACE_FIRST_ONLY = True
TERMS_ADDITIONAL_IGNORED_TAGS = ()  # lost of other similar settings exist


NEWSLETTER_RICHTEXT_WIDGET = "tinymce.widgets.TinyMCE"
NEWSLETTER_THUMBNAIL = "sorl-thumbnail"
NEWSLETTER_USE_HTTPS = True  # for links in sent emails

INTERNAL_IPS = [
    '127.0.0.1',
]

CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 3600
CACHE_MIDDLEWARE_KEY_PREFIX = ""  # No multi-site for now

TEXT_AUTO_HYPHENATE = False  # Breaks copy/paste to otehr software!
