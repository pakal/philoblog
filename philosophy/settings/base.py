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

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
STATICFILES_DIRS = (
)
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_DIR, 'philosophy', 'templates'), ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.i18n',
                'django.core.context_processors.debug',
                'django.core.context_processors.request',
                'django.core.context_processors.media',
                'django.core.context_processors.csrf',
                'django.core.context_processors.tz',
                'sekizai.context_processors.sekizai',
                'django.core.context_processors.static',
                'cms.context_processors.cms_settings'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader'
            ],
        },
    },
]

MIDDLEWARE_CLASSES = [
    ## broken 'cms.middleware.utils.ApphookReloadMiddleware',
    ## SEEMS BUGGY 'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
    'request.middleware.RequestMiddleware',  # AFTER auth stuffs
    ## SEEMS BUGGY 'django.middleware.cache.FetchFromCacheMiddleware',
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

    'cms',
    'menus',
    'sekizai',
    'treebeard',
    'djangocms_text_ckeditor',
    'djangocms_style',
    'djangocms_column',
    'filer',
    'easy_thumbnails',
    'cmsplugin_filer_image',
    'cmsplugin_filer_file',
    'cmsplugin_filer_folder',
    'cmsplugin_filer_teaser',
    'cmsplugin_filer_utils',
    'cmsplugin_filer_video',
    'djangocms_snippet',
    'djangocms_googlemap',
    'djangocms_inherit',
    'djangocms_link',
    'cmsplugin_rst',
    'cmsplugin_raw_html',
    'aldryn_disqus',

    'taggit',
    'taggit_autosuggest',
    'djangocms_page_tags',
    'terms',

    # BREAKS django-terms, so don't use it
    # and don't even install it: 'softhyphen',

    'reversion',
    'compressor',

    'tinymce',
    'django_extensions',
    'newsletter',

    'request',  # analytics

    'philosophy'
]

LANGUAGES = (
    ## Customize this
    ('fr', gettext('French')),
    #('en', gettext('English')),
)

CMS_LANGUAGES = {
    ## Customize this
    1: [
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

CMS_TEMPLATES = (
    ## Customize this
    ('single_article.html', 'Single Article'),
    ('page.html', 'Page'),
    ('homepage.html', 'Homepage'),
)

CMS_PERMISSION = True
CMS_PUBLIC_FOR = "all"   # or "staff"

CMS_PLACEHOLDER_CONF = {}


MIGRATION_MODULES = {
}

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters'
)

## Django-compressor settings

COMPRESS_ENABLED = False

COMPRESS_PRECOMPILERS = (
    # unused('text/x-scss', 'django_libsass.SassCompiler'),
)


## CKEDITOR SETTINGS ##
#See http://docs.cksource.com/ckeditor_api/symbols/CKEDITOR.config.html for all settings

CKEDITOR_SETTINGS = {
            #'height': '320px',
            'toolbar_CMS': [
                ['Undo', 'Redo'],
                ['cmsplugins', '-', 'ShowBlocks'],
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

TAGGIT_CASE_INSENSITIVE = True


CMSPLUGIN_RST_SETTINGS_OVERRIDES = {"initial_header_level": 3, # minimum "h2" when rendered to html
                                    "smart_quotes": "alt"}


CMS_PLUGIN_PROCESSORS = (
    'terms.cms_plugin_processors.TermsProcessor',
)

TERMS_ENABLED = True
TERMS_DEFINITION_WIDGET = "basic"  # so that we can input html ; choices are 'auto', 'basic', 'tinymce', and 'ckeditor'
TERMS_REPLACE_FIRST_ONLY = True
TERMS_ADDITIONAL_IGNORED_TAGS = ()  # lost of other similar settings exist


NEWSLETTER_RICHTEXT_WIDGET = "tinymce.widgets.TinyMCE"
