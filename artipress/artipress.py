import json
import os
import re
import shutil
from datetime import datetime

import markdown as md_lib


# Run from the project root regardless of where the script is invoked from
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
os.chdir(_PROJECT_ROOT)

JSON_CONFIG_FILEPATH = "artipress/config.json"
CONFIG_DEFAULTS = {
    "base_url": "https://artipress.majdij.com",
    "website_title": "ArtiPress",
    "website_logo_url": "https://artipress.majdij.com/resources/images/logo.png",
    "input_content_folder": "artipress/content",
    "shared_assets_source_folder": "artipress/assets",
    "base_template_paths": {},
    "output_path": "articles",
    "shared_assets_subfolder": "_artipress",
    "recently_published_within_hours": 168,
    "date_format": "{day} %B %Y",
    "time_format": "%H:%M",
}
REQUIRED_JSON_CONFIG_FIELDS = [
    "base_template_paths.article_list",
    "base_template_paths.article_page",
    "base_template_paths.author_page",
    "base_template_paths.author_list",
    "input_content_folder",
    "output_path",
]

JSON_ARTICLE_FILEPATH = "article.json"
REQUIRED_JSON_ARTICLE_FIELDS = [
    "article_title",
    "author_slugs",
    "article_strap_line",
    "date.published"
]

AUTHOR_JSON_PATH = "artipress/authors.json"
SOCIAL_LINKS_JSON_PATH = "artipress/social_links.json"
DEFAULT_AUTHOR_PICTURE_FILENAME = "default.svg"

RESERVED_FOLDERS_IN_ARTICLES_OUTPUT = [
    "authors",
]

LQIP_THUMBNAIL_MAX_WIDTH = 100
LQIP_THUMBNAIL_FILENAME = "thumbnail.webp"

RASTER_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif")
WEBP_CONVERSION_MAX_WIDTH = 1200
WEBP_CONVERSION_QUALITY = 85

CONFIG = {}
AUTHORS = []
SOCIAL_LINKS = {}


def assets_url() -> str:
    return f"/{CONFIG['output_path']}/{CONFIG['shared_assets_subfolder']}"

def author_picture_deploy_url(filename: str) -> str:
    return f"{assets_url()}/author-pictures/{filename}"

def social_icon_deploy_url(filename: str) -> str:
    return f"{assets_url()}/icons/{filename}"

def article_asset_deploy_url(article_slug: str, relative_path: str) -> str:
    return f"/{CONFIG['output_path']}/{article_slug}/{relative_path.lstrip('/')}"

def resolve_article_image_url(article_slug: str, image_path: str) -> str:
    if not image_path:
        return ""
    if image_path.startswith(("http://", "https://", "/")):
        return image_path
    return article_asset_deploy_url(article_slug, image_path)

def resolve_author_picture_url(filename: str) -> str:
    if not filename:
        return ""
    if filename.startswith(("http://", "https://", "/")):
        return filename
    return author_picture_deploy_url(filename)

def resolve_social_icon_url(filename: str) -> str:
    if not filename:
        return ""
    if filename.startswith(("http://", "https://", "/")):
        return filename
    return social_icon_deploy_url(filename)

def copy_shared_assets():
    src = CONFIG["shared_assets_source_folder"]
    dst = os.path.join(CONFIG["output_path"], CONFIG["shared_assets_subfolder"])

    if not os.path.exists(src):
        print(f"Warning: shared_assets_source_folder not found at '{src}' — skipping asset copy")
        return

    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Copied shared assets: {src} -> {dst}")

def copy_article_assets(article_slug: str):
    src = os.path.join(CONFIG["input_content_folder"], article_slug)
    dst = os.path.join(CONFIG["output_path"], article_slug)

    if not os.path.exists(src):
        return

    for entry in os.scandir(src):
        if entry.name in ("article.md", "article.json"):
            continue
        dst_entry = os.path.join(dst, entry.name)
        if entry.is_dir():
            if os.path.exists(dst_entry):
                shutil.rmtree(dst_entry)
            shutil.copytree(entry.path, dst_entry)
        else:
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(entry.path, dst_entry)


def generate_lqip_thumbnail(article_slug: str, article_data: dict) -> str | None:
    if not article_data.get("make_low_res_thumbnail", True):
        return None

    try:
        from PIL import Image
    except ImportError:
        print(f"Warning: [{article_slug}] Pillow is not installed — LQIP thumbnails disabled. Run: pip install Pillow")
        return None

    article_image_path = article_data.get("article_image_url", "")
    if not article_image_path:
        return None
    if article_image_path.startswith(("http://", "https://")):
        print(f"Warning: [{article_slug}] LQIP skipped — article_image_url is a remote URL")
        return None

    # article_image_url is now a path relative to the article's source folder
    source_path = os.path.join(CONFIG["input_content_folder"], article_slug, article_image_path.lstrip("/"))
    if not os.path.exists(source_path):
        print(f"Warning: [{article_slug}] Article image not found at '{source_path}' — skipping LQIP thumbnail")
        return None

    output_dir = os.path.join(CONFIG["output_path"], article_slug, "images")
    output_path = os.path.join(output_dir, LQIP_THUMBNAIL_FILENAME)
    thumbnail_url = f"/{CONFIG['output_path']}/{article_slug}/images/{LQIP_THUMBNAIL_FILENAME}"

    try:
        with Image.open(source_path) as img:
            original_width, original_height = img.size
            if original_width <= LQIP_THUMBNAIL_MAX_WIDTH:
                return None
            new_height = max(1, round(original_height * LQIP_THUMBNAIL_MAX_WIDTH / original_width))
            thumbnail = img.resize((LQIP_THUMBNAIL_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            os.makedirs(output_dir, exist_ok=True)
            thumbnail.save(output_path, "WEBP", quality=60)
            return thumbnail_url
    except Exception as e:
        print(f"Warning: [{article_slug}] Could not generate LQIP thumbnail for '{source_path}' — {e}. Falling back to single image.")
        return None

def generate_all_lqip_thumbnails(validated_articles: list[tuple[str, dict]]) -> dict:
    return {slug: generate_lqip_thumbnail(slug, data) for slug, data in validated_articles}

def map_image_path_to_webp(path: str) -> str:
    if not path or path.startswith(("http://", "https://", "/")):
        return path
    lower = path.lower()
    for ext in RASTER_IMAGE_EXTENSIONS:
        if lower.endswith(ext):
            return path[: -len(ext)] + ".webp"
    return path

def remap_html_images_to_webp(html: str) -> str:
    def replace(match):
        prefix, src, suffix = match.group(1), match.group(2), match.group(3)
        return f'{prefix}{map_image_path_to_webp(src)}{suffix}'
    return re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', replace, html, flags=re.IGNORECASE)

def webp_conversion_enabled(article_data: dict) -> bool:
    return bool(article_data.get("convert_article_images_to_webp", True))

def convert_article_images(article_slug: str, article_data: dict) -> None:
    if not webp_conversion_enabled(article_data):
        return

    try:
        from PIL import Image
    except ImportError:
        print(f"Warning: [{article_slug}] Pillow is not installed — WebP image conversion disabled. Run: pip install Pillow")
        return

    article_output_dir = os.path.join(CONFIG["output_path"], article_slug)
    if not os.path.exists(article_output_dir):
        return

    for root, _, files in os.walk(article_output_dir):
        for filename in files:
            if not filename.lower().endswith(RASTER_IMAGE_EXTENSIONS):
                continue
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(root, os.path.splitext(filename)[0] + ".webp")
            try:
                with Image.open(src_path) as img:
                    if img.mode in ("P", "LA", "RGBA"):
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")
                    width, height = img.size
                    if width > WEBP_CONVERSION_MAX_WIDTH:
                        new_height = max(1, round(height * WEBP_CONVERSION_MAX_WIDTH / width))
                        img = img.resize((WEBP_CONVERSION_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
                    img.save(dst_path, "WEBP", quality=WEBP_CONVERSION_QUALITY)
                if src_path != dst_path:
                    os.remove(src_path)
            except Exception as e:
                print(f"Warning: [{article_slug}] Could not convert '{src_path}' to WebP — {e}")

def convert_all_article_images(validated_articles: list[tuple[str, dict]]) -> None:
    for slug, data in validated_articles:
        convert_article_images(slug, data)

def make_lqip_card_thumbnail(full_url: str, alt: str, thumbnail_url: str) -> str:
    return (
        f'<div class="article-card-thumbnail lqip-wrapper">\n'
        f'    <img src="{thumbnail_url}" alt="" class="lqip-placeholder" aria-hidden="true">\n'
        f'    <img src="{full_url}" alt="{alt}" class="lqip-full" loading="lazy" decoding="async">\n'
        f'</div>'
    )

def make_lqip_featured_image_block(full_url: str, alt: str, thumbnail_url: str) -> str:
    return (
        '<div class="article-image-container article-content featured-article-image">\n'
        '    <div class="lqip-wrapper featured-lqip-wrapper">\n'
        f'        <img src="{thumbnail_url}" alt="" class="lqip-placeholder" aria-hidden="true">\n'
        f'        <img src="{full_url}" alt="{alt}" class="lqip-full">\n'
        '    </div>\n'
        '</div>'
    )

def format_display_date(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        date_format = CONFIG.get("date_format", "{day} %B %Y")
        time_format = CONFIG.get("time_format", "%H:%M")
        date_part = dt.strftime(date_format.replace("{day}", str(dt.day)))
        if dt.hour == 0 and dt.minute == 0:
            return date_part
        return f"{date_part} at {dt.strftime(time_format)}"
    except (ValueError, AttributeError):
        return iso_string

def get_nested(data: dict, key: str):
    """
    Retrieve a value from a nested dictionary using a dot-notation key. Returns None if any part of the path is missing.
    
    Args:
        data: The dictionary to traverse.
        key:  The dot-notation key to look up.
    Returns:
        The value at the nested key, or None if any part of the path is missing.
    """
    keys = key.split(".")
    for k in keys:
        if not isinstance(data, dict) or k not in data:
            return None
        data = data[k]
    return data

def validate_json(filepath: str, required_fields: list[str]) -> dict:
    """
    Validate that the JSON file exists, is valid JSON, and contains required fields. Raises FileNotFoundError, ValueError, or KeyError with descriptive messages if validation fails.

    Args:
        filepath:        Path to the JSON file to validate.
        required_fields: List of dot-notation keys that must be present in the JSON.
    Returns:
        The loaded JSON data as a dictionary if validation passes.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file '{filepath}': {e}")

    missing = [f for f in required_fields if get_nested(data, f) is None]
    if missing:
        raise KeyError(f"JSON is missing required fields: {missing}")

    return data

def get_folders(directory: str, ignore: list[str] = []) -> list[str]:
    """
    Returns a list of top-level folder names within a given directory.

    Args:
        directory: Path to the directory to scan.
        ignore:    List of folder names to exclude.
    Returns:
        A list of folder names (not full paths).
    """
    return [
        entry.name
        for entry in os.scandir(directory)
        if entry.is_dir() and entry.name not in ignore
    ]

def get_author_info(author_slug: str, authors: list[dict]) -> dict:
    """
    Retrieves author details from a pre-loaded authors list by their slug.

    Args:
        author_slug: The unique slug identifier for the author (e.g. "john-doe").
        authors:     Pre-loaded list of author dicts (from AUTHORS global).

    Returns:
        A dict containing the author's details, or an empty dict if not found.
    """
    return next(
        (author for author in authors if author.get("author_slug") == author_slug),
        {}
    )

def make_author_meta_tag(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured meta tag.
    meta_tags = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        if meta_tags == "":
            meta_tags += f"<meta name=\"author\" content=\"{author_info.get('author_name', 'Unknown Author')}\" />"
        else:
            meta_tags += f"\n<meta name=\"author\" content=\"{author_info.get('author_name', 'Unknown Author')}\" />"

    return meta_tags

def make_author_og_meta_tag(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured Open Graph meta tag.
    og_meta_tags = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        if og_meta_tags == "":
            og_meta_tags += f"<meta property=\"article:author\" content=\"{CONFIG['base_url']}/articles/authors/{author_slug}\" />"
        else:
            og_meta_tags += f"\n<meta property=\"article:author\" content=\"{CONFIG['base_url']}/articles/authors/{author_slug}\" />"

    return og_meta_tags

def make_author_ld_json(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured application/ld+json script tag.
    authors_ld_json = []
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        author_ld_json = {
            "@type": "Person",
            "name": author_info.get("author_name", "Unknown Author"),
            "url": f"{CONFIG['base_url']}/articles/authors/{author_slug}"
        }
        authors_ld_json.append(author_ld_json)

    return json.dumps(authors_ld_json, indent=4)

def make_author_html_element(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured html element.
    html_authors_info = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)

        if html_authors_info == "":
            html_authors_info += f"<a href='/articles/authors/{author_slug}'>{author_info.get('author_name', 'Unknown Author')}</a>"
        else:
            html_authors_info += f", <a href='/articles/authors/{author_slug}'>{author_info.get('author_name', 'Unknown Author')}</a>"
    
    return html_authors_info

def make_author_plain_text(article_data: dict) -> str:
    names = []
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        names.append(author_info.get("author_name", "Unknown Author"))
    return ", ".join(names)

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"No file found at: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when reading: {path}")

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

_MD_EXTENSIONS = ["tables", "fenced_code", "footnotes", "sane_lists", "md_in_html"]

def markdown_to_html(md: str, source_label: str = "") -> str:
    html = md_lib.markdown(md, extensions=_MD_EXTENSIONS)

    # Conditional heading shift: if the author used '#' (h1) in their markdown,
    # shift every heading down one level (clamped at h6) so the page template's
    # title remains the sole h1.
    if re.search(r'<h1\b', html, flags=re.IGNORECASE):
        where = f" in '{source_label}'" if source_label else ""
        print(f"Warning: '#' (h1) used in markdown{where} — shifting all headings down one level (use '##' or deeper to avoid this)")
        def _shift(match):
            slash = match.group(1)
            level = int(match.group(2))
            return f'<{slash}h{min(level + 1, 6)}'
        html = re.sub(r'<(/?)h([1-6])\b', _shift, html, flags=re.IGNORECASE)

    return html

def render_template(template: str, variables: dict) -> str:
    def replacer(match):
        key = match.group(1).strip()
        if key not in variables:
            raise KeyError(f"Template variable '{key}' not found in provided dictionary")
        return str(variables[key])

    return re.sub(r'\{html_var\((\w+)\)\}', replacer, template)



def validate_article_folders(article_folders):
    validated_articles = []

    for folder in article_folders:
        article_json_path = os.path.join(CONFIG["input_content_folder"], folder, JSON_ARTICLE_FILEPATH)
        try:
            article_data = validate_json(article_json_path, REQUIRED_JSON_ARTICLE_FIELDS)
            print(f"Validated article: {article_data['article_title']}")
            validated_articles.append((folder, article_data))
        except (FileNotFoundError, ValueError, KeyError) as e:
            raise SystemExit(f"Error in article folder '{folder}': {e}")

    # Order: most-recently-published first; ties broken alphabetically by title.
    # Two passes leverage sort stability — the title order from pass 1 is preserved within each date group in pass 2.
    validated_articles.sort(key=lambda item: (item[1].get("article_title") or "").lower())
    validated_articles.sort(
        key=lambda item: (item[1].get("date") or {}).get("published") or "",
        reverse=True,
    )

    return validated_articles

def startup_checks() -> list[tuple[str, dict]]:
    global AUTHORS, SOCIAL_LINKS

    # Verify all template file paths exist before any generation begins
    all_template_paths = {
        **CONFIG.get("base_template_paths", {}),
        **CONFIG.get("components_template_paths", {}),
    }
    for key, path in all_template_paths.items():
        if path is None or not os.path.exists(path):
            raise SystemExit(f"Template file missing for '{key}': {path}")

    # Load authors.json once
    authors_data = validate_json(AUTHOR_JSON_PATH, [])
    if not isinstance(authors_data, list):
        raise ValueError(f"Expected a JSON array in {AUTHOR_JSON_PATH}, got {type(authors_data).__name__}")
    AUTHORS = authors_data

    # Load social_links.json once
    social_data = validate_json(SOCIAL_LINKS_JSON_PATH, [])
    if not isinstance(social_data, dict):
        raise ValueError(f"Expected a JSON object in {SOCIAL_LINKS_JSON_PATH}, got {type(social_data).__name__}")
    SOCIAL_LINKS = social_data

    # Verify every article folder contains article.md
    article_folders = get_folders(CONFIG["input_content_folder"])
    missing_md = [
        folder for folder in article_folders
        if not os.path.exists(os.path.join(CONFIG["input_content_folder"], folder, "article.md"))
    ]
    if missing_md:
        raise SystemExit(f"Missing article.md in folders: {missing_md}")

    return validate_article_folders(article_folders)


def generate_article_page(article_slug: str, article_data: dict, output_path: str, lqip_thumbnail_url: str | None = None):

    article_page_template = read_file(CONFIG["base_template_paths"].get("article_page"))
    article_md_content = read_file(os.path.join(CONFIG["input_content_folder"], article_slug, "article.md"))

    # Construct published date
    ISO_published_date = article_data.get("date", {}).get("published", "")
    published_date_element = format_display_date(ISO_published_date)

    # Construct edited date (if it exists and has a value)
    ISO_edited_date = ""
    edited_date_element = ""
    if article_data.get("date", {}).get("edited") not in (None, ""):
        ISO_edited_date = article_data.get("date", {}).get("edited", "")
        edited_date_element = f' | Edited on {format_display_date(ISO_edited_date)}'

    raw_article_image_path = article_data.get("article_image_url", "")
    if webp_conversion_enabled(article_data):
        raw_article_image_path = map_image_path_to_webp(raw_article_image_path)
    article_image_url = resolve_article_image_url(article_slug, raw_article_image_path)
    article_image_alt = article_data.get("article_image_alt", "")
    if article_image_url and lqip_thumbnail_url:
        article_image_block = make_lqip_featured_image_block(article_image_url, article_image_alt, lqip_thumbnail_url)
    elif article_image_url:
        article_image_block = (
            '<div class="article-image-container article-content featured-article-image">\n'
            f'        <img src="{article_image_url}" alt="{article_image_alt}"/>\n'
            '    </div>'
        )
    else:
        article_image_block = ""

    article_html_content = markdown_to_html(article_md_content, source_label=article_slug)
    if webp_conversion_enabled(article_data):
        article_html_content = remap_html_images_to_webp(article_html_content)

    replacement_vars = {
        "article_title": article_data.get("article_title", "Untitled Article"),
        "website_title": CONFIG["website_title"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "base_url": CONFIG["base_url"],
        "article_id": article_slug,
        "article_strap_line": article_data.get("article_strap_line", ""),
        "article_keywords_list": ", ".join(article_data.get("article_keywords_list", [])),
        "author_meta_tags": make_author_meta_tag(article_data),
        "article_featured_image": article_image_url,
        "article_published_date_iso": ISO_published_date,
        "article_edited_date_iso": ISO_edited_date,
        "og_meta_tags_authors": make_author_og_meta_tag(article_data),
        "json_ld_authors": make_author_ld_json(article_data),
        "article_authors": make_author_html_element(article_data),
        "article_published_date": published_date_element,
        "article_edited_date": edited_date_element,
        "website_logo_url": CONFIG.get("website_logo_url", ""),
        "article_image_block": article_image_block,
        "article_html_content": article_html_content,
    }

    # Pass 1: inject component contents and resolve top-level vars in the outer template
    base_page_template = render_template(article_page_template, {
        **replacement_vars,
        "article_page_head_metadata": read_file(CONFIG["components_template_paths"].get("article_page_head_metadata")),
        "articles_page_styling_and_scripts": read_file(CONFIG["components_template_paths"].get("articles_page_styling_and_scripts")),
        "article_page_head_application_json_ld": read_file(CONFIG["components_template_paths"].get("article_page_head_application_json_ld")),
        "article_page_main_article": read_file(CONFIG["components_template_paths"].get("article_page_main_article")),
    })

    # Pass 2: resolve variables that lived inside the injected component contents
    final_html = render_template(base_page_template, replacement_vars)

    write_file(output_path, final_html)

def generate_article_print(article_slug: str, article_data: dict, output_path: str):

    article_print_template = read_file(CONFIG["base_template_paths"].get("article_print"))
    article_md_content = read_file(os.path.join(CONFIG["input_content_folder"], article_slug, "article.md"))

    ISO_published_date = article_data.get("date", {}).get("published", "")

    edited_date_text = ""
    if article_data.get("date", {}).get("edited") not in (None, ""):
        edited_date_text = f' | Edited on {format_display_date(article_data["date"]["edited"])}'

    raw_article_image_path = article_data.get("article_image_url", "")
    if webp_conversion_enabled(article_data):
        raw_article_image_path = map_image_path_to_webp(raw_article_image_path)
    article_image_url = resolve_article_image_url(article_slug, raw_article_image_path)
    article_image_alt = article_data.get("article_image_alt", "")
    if article_image_url:
        article_image_block = (
            '<div class="article-image-container article-content featured-article-image">\n'
            f'        <img src="{article_image_url}" alt="{article_image_alt}"/>\n'
            '    </div>'
        )
    else:
        article_image_block = ""

    article_html_content = markdown_to_html(article_md_content, source_label=f"{article_slug} (print)")
    if webp_conversion_enabled(article_data):
        article_html_content = remap_html_images_to_webp(article_html_content)

    replacement_vars = {
        "article_title": article_data.get("article_title", "Untitled Article"),
        "website_title": CONFIG["website_title"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "base_url": CONFIG["base_url"],
        "article_id": article_slug,
        "article_strap_line": article_data.get("article_strap_line", ""),
        "article_authors": make_author_plain_text(article_data),
        "article_published_date": format_display_date(ISO_published_date),
        "article_edited_date": edited_date_text,
        "article_edited_date_iso": edited_date_text,
        "article_image_block": article_image_block,
        "article_html_content": article_html_content,
    }

    # Pass 1: inject component content and resolve top-level template variables
    base_print_template = render_template(article_print_template, {
        **replacement_vars,
        "articles_page_styling_and_scripts": read_file(CONFIG["components_template_paths"].get("articles_page_styling_and_scripts")),
        "article_page_main_article": read_file(CONFIG["components_template_paths"].get("article_page_main_article")),
    })

    # Pass 2: resolve variables inside injected component content
    final_html = render_template(base_print_template, replacement_vars)

    write_file(output_path, final_html)

def generate_all_article_pages(validated_articles: list[tuple[str, dict]], lqip_thumbnails: dict):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["output_path"], folder, "index.html")
        generate_article_page(folder, article_data, output_path, lqip_thumbnails.get(folder))

def copy_all_article_assets(validated_articles: list[tuple[str, dict]]):
    for folder, _ in validated_articles:
        copy_article_assets(folder)

def generate_all_article_prints(validated_articles: list[tuple[str, dict]]):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["output_path"], folder, "print.html")
        generate_article_print(folder, article_data, output_path)

def render_article_list_items_html(validated_articles, article_list_item_template, lqip_thumbnails: dict | None = None):
    """
    Render the grid of article cards used on both the article list page and individual author pages.

    Args:
        validated_articles: list of (folder, article_data) tuples.
        article_list_item_template: raw template string for a single card.
    Returns:
        HTML string wrapping the cards in an .artipress-articles-container div.
    """
    article_list_items_html = f"<div class=\"artipress-articles-container\" data-recently-published-hours=\"{CONFIG.get('recently_published_within_hours', 0)}\">\n"

    for folder, article_data in validated_articles:

        if article_data.get("hide_from_article_list", False):
            continue

        article_labels = ""
        #  Check to see if there are any labels for the article
        if article_data.get("article_labels"):
            article_labels += "<p class=\"artipress-article-card-labels\">"

            for label in article_data.get("article_labels", []):
                article_labels += f"<span class=\"artipress-article-card-label\">{label}</span>"
            
            article_labels += "</p>"
        
        else:
            # If there are no labels, just place an epty div that will be used for spacing
            article_labels = "<div class=\"artipress-article-card-labels-empty\"></div>"

        article_authors = ""
        for author_slug in article_data["author_slugs"]:
            author_info = get_author_info(author_slug, AUTHORS)
            if article_authors != "":
                article_authors += ", "
            article_authors += author_info.get('author_name', 'Unknown Author')

        raw_card_image_path = article_data.get("article_image_url", "")
        if webp_conversion_enabled(article_data):
            raw_card_image_path = map_image_path_to_webp(raw_card_image_path)
        article_image_url = resolve_article_image_url(folder, raw_card_image_path)
        article_image_alt = article_data.get("article_image_alt", "")
        thumbnail_url = (lqip_thumbnails or {}).get(folder)
        if article_image_url and thumbnail_url:
            article_card_thumbnail = make_lqip_card_thumbnail(article_image_url, article_image_alt, thumbnail_url)
        elif article_image_url:
            article_card_thumbnail = (
                f'<img src="{article_image_url}" alt="{article_image_alt}" class="article-card-thumbnail" loading="lazy" decoding="async" />'
            )
        else:
            article_card_thumbnail = ""

        article_list_items_html += ("\n" + render_template(article_list_item_template, {
            "article_title": article_data.get("article_title", "Untitled Article"),
            "article_strap_line": article_data.get("article_strap_line", ""),
            "article_labels": article_labels,
            "article_authors": article_authors,
            "article_published_date": format_display_date(article_data.get("date", {}).get("published", "")),
            "article_published_date_iso": article_data.get("date", {}).get("published", ""),
            "article_card_thumbnail": article_card_thumbnail,
            "article_url": f"/{CONFIG['output_path']}/{folder}/index.html",
        }))

    article_list_items_html += "\n</div>"
    return article_list_items_html

def generate_article_list_page(validated_articles: list[tuple[str, dict]], lqip_thumbnails: dict):

    article_list_template = read_file(CONFIG["base_template_paths"].get("article_list"))
    article_list_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("article_list_styling_and_scripts"))
    article_list_item_template = read_file(CONFIG["components_template_paths"].get("article_list_item"))

    output_path = os.path.join(CONFIG["output_path"], "index.html")

    article_list_items_html = render_article_list_items_html(validated_articles, article_list_item_template, lqip_thumbnails)

    replacement_vars = {
        "article_list_items": article_list_items_html,
        "base_url": CONFIG["base_url"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "website_title": CONFIG["website_title"],
    }
    # Resolve any {html_var(...)} inside the component snippet before injecting it
    replacement_vars["article_list_styling_and_scripts"] = render_template(article_list_styling_and_scripts, replacement_vars)

    final_html = render_template(article_list_template, replacement_vars)

    write_file(output_path, final_html)

def generate_author_list_page():

    author_list_template = read_file(CONFIG["base_template_paths"].get("author_list"))
    author_list_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("author_list_styling_and_scripts"))
    author_list_item_template = read_file(CONFIG["components_template_paths"].get("author_list_item"))

    output_path = os.path.join(CONFIG["output_path"], "authors", "index.html")

    author_list_items_html = "<div class=\"artipress-authors-container\">\n"

    # For each author, render an author list item using `author_list_item_template` and the author's data
    for author in AUTHORS:
        author_slug = author.get("author_slug", "")

        # Skip the role element entirely when the author has no role set
        author_role = (author.get("author_role") or "").strip()
        author_role_formatted = (
            f'<p class="artipress-author-card-role">{author_role}</p>'
            if author_role else ""
        )

        # Fall back to the default avatar when an author has no picture
        author_picture_filename = (author.get("author_picture_url") or "").strip() or DEFAULT_AUTHOR_PICTURE_FILENAME
        author_picture_url = resolve_author_picture_url(author_picture_filename)

        author_list_items_html += ("\n" + render_template(author_list_item_template, {
            "author_name": author.get("author_name", "Unknown Author"),
            "author_role_formatted": author_role_formatted,
            "author_picture_url": author_picture_url,
            "author_url": f"/{CONFIG['output_path']}/authors/{author_slug}/index.html",
        }))

    author_list_items_html += "\n</div>"

    replacement_vars = {
        "author_list_items": author_list_items_html,
        "base_url": CONFIG["base_url"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "website_title": CONFIG["website_title"],
    }
    replacement_vars["author_list_styling_and_scripts"] = render_template(author_list_styling_and_scripts, replacement_vars)

    final_html = render_template(author_list_template, replacement_vars)

    write_file(output_path, final_html)

def render_author_social_links_html(social_links, social_link_template, social_links_registry):
    """
    Render a <ul> of social link icons for an author. Returns "" if the author has no usable links.
    Skips + warns when a platform is missing from the registry or its icon file is missing.
    """
    if not social_links:
        return ""

    items_html = ""
    for platform_key, data in social_links.items():
        if platform_key not in social_links_registry:
            print(f"Warning: social platform '{platform_key}' not found in social_links.json — skipping")
            continue

        registry_entry = social_links_registry[platform_key]
        icon_filename = registry_entry.get("icon", "")
        # Verify the source icon exists. Skip remote URLs (we can't check those).
        if icon_filename and not icon_filename.startswith(("http://", "https://", "/")):
            source_icon_path = os.path.join(CONFIG["shared_assets_source_folder"], "icons", icon_filename)
            if not os.path.exists(source_icon_path):
                print(f"Warning: icon file '{source_icon_path}' missing for platform '{platform_key}' — skipping")
                continue
        elif not icon_filename:
            print(f"Warning: no icon configured for platform '{platform_key}' — skipping")
            continue

        platform_name = registry_entry.get("name", platform_key)
        handle = (data.get("handle") or "").strip()
        link = (data.get("link") or "").strip()
        if not link:
            continue

        aria_label = f"{platform_name}: {handle}" if handle else platform_name

        items_html += "\n" + render_template(social_link_template, {
            "social_link_url": link,
            "social_link_icon_url": resolve_social_icon_url(icon_filename),
            "social_link_aria_label": aria_label,
            "social_link_title": aria_label,
        })

    if not items_html:
        return ""

    return f'<ul class="social-links">{items_html}\n</ul>'

def generate_author_page(author_data: dict, validated_articles: list[tuple[str, dict]], social_links_registry: dict, lqip_thumbnails: dict | None = None):
    author_slug = author_data.get("author_slug", "")
    author_name = author_data.get("author_name", "Unknown Author")

    author_page_template = read_file(CONFIG["base_template_paths"].get("author_page"))
    author_page_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("author_page_styling_and_scripts"))
    article_list_item_template = read_file(CONFIG["components_template_paths"].get("article_list_item"))
    social_link_template = read_file(CONFIG["components_template_paths"].get("author_social_link"))

    # Filter to articles this author wrote or co-wrote
    author_articles = [
        (folder, article_data) for folder, article_data in validated_articles
        if author_slug in article_data.get("author_slugs", [])
    ]

    if author_articles:
        author_articles_list_items = render_article_list_items_html(author_articles, article_list_item_template, lqip_thumbnails)
    else:
        author_articles_list_items = "<p>No articles yet.</p>"

    # Role -- omit the <p> entirely when empty
    author_role = (author_data.get("author_role") or "").strip()
    author_role_formatted = (
        f'<p class="author-role">{author_role}</p>'
        if author_role else ""
    )

    # Bio -- raw kept for meta description, markdown rendered for the page body
    author_bio = author_data.get("author_bio", "")
    author_bio_html = markdown_to_html(author_bio, source_label=f"author bio: {author_name}") if author_bio else ""

    # Picture -- fall back to default if missing
    author_picture_filename = (author_data.get("author_picture_url") or "").strip() or DEFAULT_AUTHOR_PICTURE_FILENAME
    author_picture_url = resolve_author_picture_url(author_picture_filename)

    # Social links -- empty string if author has none / all skipped
    author_social_links_formatted = render_author_social_links_html(
        author_data.get("social_links", {}),
        social_link_template,
        social_links_registry,
    )

    replacement_vars = {
        "website_title": CONFIG["website_title"],
        "base_url": CONFIG["base_url"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "author_name": author_name,
        "author_slug": author_slug,
        "author_bio": author_bio,
        "author_picture_url": author_picture_url,
        "author_role_formatted": author_role_formatted,
        "author_bio_html": author_bio_html,
        "author_social_links_formatted": author_social_links_formatted,
        "author_articles_list_items": author_articles_list_items,
    }
    replacement_vars["author_page_styling_and_scripts"] = render_template(author_page_styling_and_scripts, replacement_vars)

    final_html = render_template(author_page_template, replacement_vars)

    output_path = os.path.join(CONFIG["output_path"], "authors", author_slug, "index.html")
    write_file(output_path, final_html)

def generate_all_author_pages(validated_articles: list[tuple[str, dict]], lqip_thumbnails: dict):
    for author in AUTHORS:
        generate_author_page(author, validated_articles, SOCIAL_LINKS, lqip_thumbnails)
        print(f"Generated author page: {author.get('author_name', 'Unknown Author')}")

def main():
    global CONFIG, AUTHORS, SOCIAL_LINKS

    config_data = validate_json(JSON_CONFIG_FILEPATH, REQUIRED_JSON_CONFIG_FIELDS)
    CONFIG = {**CONFIG_DEFAULTS, **config_data}

    validated_articles = startup_checks()

    # Copy source assets before LQIP/HTML generation so they aren't wiped by the article folder copy
    copy_shared_assets()
    copy_all_article_assets(validated_articles)

    # Convert raster images in each article's output folder to WebP (replacing originals).
    # Runs after the copy step so it operates on the output copy, leaving the source folder untouched.
    convert_all_article_images(validated_articles)

    lqip_thumbnails = generate_all_lqip_thumbnails(validated_articles)

    generate_all_article_pages(validated_articles, lqip_thumbnails)
    generate_all_article_prints(validated_articles)
    generate_article_list_page(validated_articles, lqip_thumbnails)
    generate_author_list_page()
    generate_all_author_pages(validated_articles, lqip_thumbnails)



if __name__ == "__main__":
    main()