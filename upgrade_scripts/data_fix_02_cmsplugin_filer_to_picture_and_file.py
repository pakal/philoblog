"""
One-off data fix (django-cms upgrade ladder): convert every abandoned cmsplugin-filer plugin
(no release since 2016, no django-cms 4+ support, blocks django-filer at 1.x) to its maintained
equivalent, IN PLACE:
  - FilerImagePlugin -> djangocms_picture "PicturePlugin"
  - FilerFilePlugin  -> djangocms_file "FilePlugin"
The cms_cmsplugin row (placeholder, position, tree path, parent TextPlugin) is kept, only its
subclass row (same cmsplugin_ptr_id) and plugin_type change, so page layouts and the
<cms-plugin> references inside TextPlugin bodies are untouched.

Must run AFTER `migrate` created the djangocms_picture/djangocms_file tables, reads the leftover
cmsplugin_filer_* tables with raw SQL (the cmsplugin-filer app itself is already uninstalled),
then drops them.

Field mapping, from inspecting the live data (70 image + 2 file rows, draft + public copies):
  - image_id / caption_text / alignment (left/right/center/'') / width / height -> same fields.
  - alt_text -> attributes {"alt": ...}  (template falls back to image default alt text / label
    when empty, like cmsplugin-filer did; same for caption -> image default caption).
  - free_link -> link_url, page_link -> link_page, target_blank -> link_target "_blank",
    link_attributes -> link_attributes.
  - use_autoscale -> use_automatic_scaling (only rendered as the "img-responsive" CSS class, no
    placeholder width is ever configured), use_original_image -> use_no_cropping,
    crop/upscale -> use_crop/use_upscale.
  - When only one of width/height is set, cmsplugin-filer computed the other from the image
    aspect ratio, whereas djangocms-picture crops to a golden-ratio box if use_crop is set: so
    use_crop is disabled in that case, to keep the exact same rendered image.
  - original_link / file_link / image_url / description / thumbnail_option / style: 0 live rows.
  - File plugin: title -> file_name, file -> file_src, target_blank -> link_target "_blank",
    link_attributes -> attributes, file size always shown (as with cmsplugin-filer).

Run via: manage.py shell -c "exec(open('upgrade_scripts/data_fix_02_cmsplugin_filer_to_picture_and_file.py').read())"
"""
import json

from django.db import connection, transaction

cur = connection.cursor()


def fetch_dicts(sql):
    cur.execute(sql)
    columns = [col[0] for col in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


with transaction.atomic():

    for column, value in [("original_link", 1), ("file_link_id", None), ("image_url", None),
                          ("description", None), ("thumbnail_option_id", None)]:
        cur.execute("SELECT COUNT(*) FROM cmsplugin_filer_image_filerimage WHERE %s %s" % (
            column, "= 1" if value else "IS NOT NULL AND %s <> ''" % column))
        assert cur.fetchone()[0] == 0, "unexpected usage of %s, mapping must be extended" % column

    images = fetch_dicts("SELECT * FROM cmsplugin_filer_image_filerimage")
    for row in images:
        width, height = row["width"], row["height"]
        use_crop = bool(row["crop"])
        if bool(width) != bool(height):
            use_crop = False  # keep aspect ratio, instead of djangocms-picture's golden-ratio cropping
        cur.execute(
            "INSERT INTO djangocms_picture_picture (cmsplugin_ptr_id, template, picture_id, external_picture,"
            " width, height, alignment, caption_text, attributes, link_url, link_page_id, link_target,"
            " link_attributes, use_automatic_scaling, use_no_cropping, use_crop, use_upscale,"
            " use_responsive_image, thumbnail_options_id)"
            " VALUES (%s, 'default', %s, '', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'inherit', NULL)",
            [
                row["cmsplugin_ptr_id"],
                row["image_id"],
                width,
                height,
                row["alignment"] or "",
                row["caption_text"] or "",
                json.dumps({"alt": row["alt_text"]} if row["alt_text"] else {}),
                row["free_link"] or None,
                row["page_link_id"],
                "_blank" if row["target_blank"] else "",
                row["link_attributes"] or "{}",
                bool(row["use_autoscale"]),
                bool(row["use_original_image"]),
                use_crop,
                bool(row["upscale"]),
            ],
        )
    cur.execute("UPDATE cms_cmsplugin SET plugin_type = 'PicturePlugin' WHERE plugin_type = 'FilerImagePlugin'")
    print("FilerImagePlugin -> PicturePlugin:", len(images), "/", cur.rowcount)

    files = fetch_dicts("SELECT * FROM cmsplugin_filer_file_filerfile")
    for row in files:
        cur.execute(
            "INSERT INTO djangocms_file_file (cmsplugin_ptr_id, template, file_src_id, file_name, link_target,"
            " link_title, show_file_size, attributes) VALUES (%s, 'default', %s, %s, %s, '', 1, %s)",
            [
                row["cmsplugin_ptr_id"],
                row["file_id"],
                row["title"] or "",
                "_blank" if row["target_blank"] else "",
                row["link_attributes"] or "{}",
            ],
        )
    cur.execute("UPDATE cms_cmsplugin SET plugin_type = 'FilePlugin' WHERE plugin_type = 'FilerFilePlugin'")
    print("FilerFilePlugin -> FilePlugin:", len(files), "/", cur.rowcount)

    cur.execute("SELECT COUNT(*) FROM cms_cmsplugin WHERE plugin_type LIKE 'Filer%%'")
    assert cur.fetchone()[0] == 0

# DDL auto-commits on MariaDB, so done after the data transaction
for table in ["cmsplugin_filer_image_filerimage", "cmsplugin_filer_file_filerfile"]:
    cur.execute("DROP TABLE %s" % table)
cur.execute("DELETE FROM django_migrations WHERE app IN ('cmsplugin_filer_image', 'cmsplugin_filer_file')")
print("dropped old cmsplugin-filer tables")
