"""Shared helpers for the i18n_dump_page / i18n_apply_translation management commands,
used to translate CMS pages from French into other languages (see Notes.txt for the workflow).
"""

# Maps a plugin_type (CMSPlugin.plugin_type) to the name of its single free-text field
# that should be translated. Plugin types not listed here (SnippetPlugin, PagesOverviewPlugin,
# CMSAliasPlugin...) carry no page-specific translatable text.
TRANSLATABLE_PLUGIN_FIELDS = {
    "RstPlugin": "body",
    "TextPlugin": "body",
    "PicturePlugin": "caption_text",
    "LinkPlugin": "name",
    "FilePlugin": "link_title",
    "CMSRawHtmlPlugin": "body",
}

# The per-category "intro" snippet (icon + category name + lead sentence) is shared across
# all articles of a category instead of being page-specific (see category_badge in
# philosophy/templatetags/extra_tags.py). Rather than asking every page-translation agent to
# re-translate it, English versions were created once (see Notes.txt) and copied SnippetPtr
# plugins get silently repointed to them here.
SNIPPET_GROUPER_FR_TO_EN = {
    1: 12,  # arts_and_leasures_intro -> arts_and_leasures_intro_en
    2: 13,  # justice_and_ethics_intro -> justice_and_ethics_intro_en
    3: 14,  # psychology -> psychology_en
    5: 15,  # politics -> politics_en
}
