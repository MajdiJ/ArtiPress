import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from typing import NoReturn

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
    "related_articles_count": 3,
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

_WARNING_COUNT = 0
_IMAGE_CONVERSION_COUNT = 0


def progress(msg: str) -> None:
    print(f"→ {msg}", flush=True)

def warn(msg: str, slug: str | None = None) -> None:
    global _WARNING_COUNT
    _WARNING_COUNT += 1
    prefix = f"Warning: [{slug}] " if slug else "Warning: "
    print(f"{prefix}{msg}", file=sys.stderr)

def fail(context: str, reason: str) -> NoReturn:
    raise SystemExit(f"Error: {context}: {reason}")


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
        warn(f"shared_assets_source_folder not found at '{src}' — skipping asset copy")
        return

    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

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

    from PIL import Image

    article_image_path = article_data.get("article_image_url", "")
    if not article_image_path:
        return None
    if article_image_path.startswith(("http://", "https://")):
        warn("LQIP skipped — article_image_url is a remote URL", slug=article_slug)
        return None

    # article_image_url is now a path relative to the article's source folder
    source_path = os.path.join(CONFIG["input_content_folder"], article_slug, article_image_path.lstrip("/"))
    if not os.path.exists(source_path):
        fail(f"article '{article_slug}'", f"article_image_url points to a missing file: {source_path}")

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
        fail(f"article '{article_slug}'", f"could not generate LQIP thumbnail for '{source_path}' — {e}")

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
    global _IMAGE_CONVERSION_COUNT

    if not webp_conversion_enabled(article_data):
        return

    from PIL import Image

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
                _IMAGE_CONVERSION_COUNT += 1
            except Exception as e:
                fail(f"article '{article_slug}'", f"could not convert '{src_path}' to WebP — {e}")

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
        fail(f"read '{path}'", "file not found")
    except PermissionError:
        fail(f"read '{path}'", "permission denied")

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
        warn(f"'#' (h1) used in markdown{where} — shifting all headings down one level (use '##' or deeper to avoid this)")
        def _shift(match):
            slash = match.group(1)
            level = int(match.group(2))
            return f'<{slash}h{min(level + 1, 6)}'
        html = re.sub(r'<(/?)h([1-6])\b', _shift, html, flags=re.IGNORECASE)

    return html

def render_template(template: str, variables: dict, source_label: str = "") -> str:
    def replacer(match):
        key = match.group(1).strip()
        if key not in variables:
            where = f" while rendering {source_label}" if source_label else ""
            raise KeyError(f"Template variable '{key}' not found{where}")
        return str(variables[key])

    return re.sub(r'\{html_var\((\w+)\)\}', replacer, template)



def validate_article_folders(article_folders):
    validated_articles = []

    for folder in article_folders:
        article_json_path = os.path.join(CONFIG["input_content_folder"], folder, JSON_ARTICLE_FILEPATH)
        try:
            article_data = validate_json(article_json_path, REQUIRED_JSON_ARTICLE_FIELDS)
            validated_articles.append((folder, article_data))
        except (FileNotFoundError, ValueError, KeyError) as e:
            fail(f"article folder '{folder}'", str(e))

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

    # Pillow is a hard dependency: LQIP + WebP conversion both need it, and the
    # generated HTML rewrites <img> srcs to .webp paths that would 404 without it.
    try:
        import PIL  # noqa: F401
    except ImportError:
        fail("Pillow", "required but not installed. Run: pip install -r requirements.txt")

    # Verify all template file paths exist before any generation begins
    all_template_paths = {
        **CONFIG.get("base_template_paths", {}),
        **CONFIG.get("components_template_paths", {}),
    }
    for key, path in all_template_paths.items():
        if path is None or not os.path.exists(path):
            fail(f"template '{key}'", f"file missing at {path}")

    # Load authors.json once
    authors_data = validate_json(AUTHOR_JSON_PATH, [])
    if not isinstance(authors_data, list):
        fail(AUTHOR_JSON_PATH, f"expected a JSON array, got {type(authors_data).__name__}")
    AUTHORS = authors_data

    # Load social_links.json once
    social_data = validate_json(SOCIAL_LINKS_JSON_PATH, [])
    if not isinstance(social_data, dict):
        fail(SOCIAL_LINKS_JSON_PATH, f"expected a JSON object, got {type(social_data).__name__}")
    SOCIAL_LINKS = social_data

    # Verify every article folder contains article.md
    article_folders = get_folders(CONFIG["input_content_folder"])
    missing_md = [
        folder for folder in article_folders
        if not os.path.exists(os.path.join(CONFIG["input_content_folder"], folder, "article.md"))
    ]
    if missing_md:
        fail("article.md", f"missing in folders: {missing_md}")

    validated_articles = validate_article_folders(article_folders)

    # Every author slug referenced by any article must exist in authors.json
    known_author_slugs = {a.get("author_slug") for a in AUTHORS if a.get("author_slug")}
    missing_refs: dict[str, list[str]] = {}
    for folder, article_data in validated_articles:
        for slug in article_data.get("author_slugs", []):
            if slug not in known_author_slugs:
                missing_refs.setdefault(slug, []).append(folder)
    if missing_refs:
        lines = [f"  - '{slug}' (referenced by: {', '.join(folders)})" for slug, folders in sorted(missing_refs.items())]
        fail("authors.json", "the following author slugs are referenced by articles but not defined:\n" + "\n".join(lines))

    return validated_articles


def select_related_articles(current_slug: str, current_data: dict, all_articles: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """
    Pick up to `related_articles_count` articles related to the current one.

    Order: manual `related_slugs` (author wins) -> keyword/label overlap (desc count, ties by recency)
    -> most-recent remaining. Hidden articles are skipped by the auto stages but allowed in manual picks.
    """
    count = CONFIG.get("related_articles_count", 3)
    if count <= 0:
        return []

    by_slug = {slug: data for slug, data in all_articles}
    selected: list[str] = []
    # Asymmetric: only blocks auto-stage suggestions; manual related_slugs still win.
    excluded = set(current_data.get("excluded_related_slugs") or [])

    def add(slug: str) -> bool:
        if slug == current_slug or slug in selected or slug not in by_slug:
            return False
        selected.append(slug)
        return len(selected) >= count

    for slug in current_data.get("related_slugs") or []:
        if add(slug):
            return [(s, by_slug[s]) for s in selected]

    current_terms = {
        term.lower() for term in
        (current_data.get("article_keywords_list") or []) + (current_data.get("article_labels") or [])
    }
    overlap_pool = []
    for slug, data in all_articles:
        if slug == current_slug or slug in selected or slug in excluded or data.get("hide_from_article_list", False):
            continue
        other_terms = {
            term.lower() for term in
            (data.get("article_keywords_list") or []) + (data.get("article_labels") or [])
        }
        overlap = len(current_terms & other_terms)
        if overlap > 0:
            published = (data.get("date") or {}).get("published") or ""
            overlap_pool.append((overlap, published, slug))

    overlap_pool.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for _, _, slug in overlap_pool:
        if add(slug):
            return [(s, by_slug[s]) for s in selected]

    # all_articles is already sorted most-recent-first by validate_article_folders
    for slug, data in all_articles:
        if slug in excluded or data.get("hide_from_article_list", False):
            continue
        if add(slug):
            break

    return [(s, by_slug[s]) for s in selected]

def render_related_articles_section(current_slug: str, current_data: dict, all_articles: list[tuple[str, dict]], article_list_item_template: str, lqip_thumbnails: dict) -> str:
    related = select_related_articles(current_slug, current_data, all_articles)
    if not related:
        return ""
    cards_html = render_article_list_items_html(related, article_list_item_template, lqip_thumbnails, include_hidden=True)
    return (
        '<section class="artipress-related-articles">\n'
        '    <h2 class="artipress-related-articles-heading">Related articles</h2>\n'
        f'    {cards_html}\n'
        '</section>'
    )

def generate_article_page(article_slug: str, article_data: dict, output_path: str, lqip_thumbnail_url: str | None = None, validated_articles: list[tuple[str, dict]] | None = None, lqip_thumbnails: dict | None = None):

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

    if validated_articles is not None:
        article_list_item_template = read_file(CONFIG["components_template_paths"].get("article_list_item"))
        related_articles_html = render_related_articles_section(
            article_slug, article_data, validated_articles, article_list_item_template, lqip_thumbnails or {}
        )
    else:
        related_articles_html = ""

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
        "related_articles": related_articles_html,
    }

    # Pass 1: inject component contents and resolve top-level vars in the outer template
    base_page_template = render_template(article_page_template, {
        **replacement_vars,
        "article_page_head_metadata": read_file(CONFIG["components_template_paths"].get("article_page_head_metadata")),
        "articles_page_styling_and_scripts": read_file(CONFIG["components_template_paths"].get("articles_page_styling_and_scripts")),
        "article_page_head_application_json_ld": read_file(CONFIG["components_template_paths"].get("article_page_head_application_json_ld")),
        "article_page_main_article": read_file(CONFIG["components_template_paths"].get("article_page_main_article")),
    }, source_label=f"article page '{article_slug}' (pass 1)")

    # Pass 2: resolve variables that lived inside the injected component contents
    final_html = render_template(base_page_template, replacement_vars, source_label=f"article page '{article_slug}' (pass 2)")

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
    }, source_label=f"print page '{article_slug}' (pass 1)")

    # Pass 2: resolve variables inside injected component content
    final_html = render_template(base_print_template, replacement_vars, source_label=f"print page '{article_slug}' (pass 2)")

    write_file(output_path, final_html)

def generate_all_article_pages(validated_articles: list[tuple[str, dict]], lqip_thumbnails: dict):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["output_path"], folder, "index.html")
        generate_article_page(folder, article_data, output_path, lqip_thumbnails.get(folder), validated_articles, lqip_thumbnails)

def copy_all_article_assets(validated_articles: list[tuple[str, dict]]):
    for folder, _ in validated_articles:
        copy_article_assets(folder)

def generate_all_article_prints(validated_articles: list[tuple[str, dict]]):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["output_path"], folder, "print.html")
        generate_article_print(folder, article_data, output_path)

def render_article_list_items_html(validated_articles, article_list_item_template, lqip_thumbnails: dict | None = None, include_hidden: bool = False):
    """
    Render the grid of article cards used on both the article list page and individual author pages.

    Args:
        validated_articles: list of (folder, article_data) tuples.
        article_list_item_template: raw template string for a single card.
        include_hidden: if True, render articles with hide_from_article_list=true too (used by related-articles when the author manually opted them in).
    Returns:
        HTML string wrapping the cards in an .artipress-articles-container div.
    """
    article_list_items_html = f"<div class=\"artipress-articles-container\" data-recently-published-hours=\"{CONFIG.get('recently_published_within_hours', 0)}\">\n"

    for folder, article_data in validated_articles:

        if not include_hidden and article_data.get("hide_from_article_list", False):
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
        }, source_label=f"article-list item for '{folder}'"))

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
    replacement_vars["article_list_styling_and_scripts"] = render_template(article_list_styling_and_scripts, replacement_vars, source_label="article-list styling component")

    final_html = render_template(article_list_template, replacement_vars, source_label="article-list page")

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
        }, source_label=f"author-list item for '{author_slug}'"))

    author_list_items_html += "\n</div>"

    replacement_vars = {
        "author_list_items": author_list_items_html,
        "base_url": CONFIG["base_url"],
        "output_path": CONFIG["output_path"],
        "assets_url": assets_url(),
        "website_title": CONFIG["website_title"],
    }
    replacement_vars["author_list_styling_and_scripts"] = render_template(author_list_styling_and_scripts, replacement_vars, source_label="author-list styling component")

    final_html = render_template(author_list_template, replacement_vars, source_label="author-list page")

    write_file(output_path, final_html)

def render_author_social_links_html(social_links, social_link_template, social_links_registry, author_slug: str = ""):
    """
    Render a <ul> of social link icons for an author. Returns "" if the author has no usable links.
    Skips + warns when a platform is missing from the registry or its icon file is missing.
    """
    if not social_links:
        return ""

    items_html = ""
    for platform_key, data in social_links.items():
        if platform_key not in social_links_registry:
            warn(f"social platform '{platform_key}' not found in social_links.json — skipping", slug=author_slug or None)
            continue

        registry_entry = social_links_registry[platform_key]
        icon_filename = registry_entry.get("icon", "")
        # Verify the source icon exists. Skip remote URLs (we can't check those).
        if icon_filename and not icon_filename.startswith(("http://", "https://", "/")):
            source_icon_path = os.path.join(CONFIG["shared_assets_source_folder"], "icons", icon_filename)
            if not os.path.exists(source_icon_path):
                warn(f"icon file '{source_icon_path}' missing for platform '{platform_key}' — skipping", slug=author_slug or None)
                continue
        elif not icon_filename:
            warn(f"no icon configured for platform '{platform_key}' — skipping", slug=author_slug or None)
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
        }, source_label=f"social link '{platform_key}' for author '{author_slug}'")

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
        author_slug=author_slug,
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
    replacement_vars["author_page_styling_and_scripts"] = render_template(author_page_styling_and_scripts, replacement_vars, source_label=f"author page styling component for '{author_slug}'")

    final_html = render_template(author_page_template, replacement_vars, source_label=f"author page '{author_slug}'")

    output_path = os.path.join(CONFIG["output_path"], "authors", author_slug, "index.html")
    write_file(output_path, final_html)

def generate_all_author_pages(validated_articles: list[tuple[str, dict]], lqip_thumbnails: dict):
    for author in AUTHORS:
        generate_author_page(author, validated_articles, SOCIAL_LINKS, lqip_thumbnails)

def main():
    global CONFIG, AUTHORS, SOCIAL_LINKS

    started = time.perf_counter()

    config_data = validate_json(JSON_CONFIG_FILEPATH, REQUIRED_JSON_CONFIG_FIELDS)
    CONFIG = {**CONFIG_DEFAULTS, **config_data}

    validated_articles = startup_checks()
    progress(f"Validated {len(validated_articles)} articles and {len(AUTHORS)} authors")

    # Copy source assets before LQIP/HTML generation so they aren't wiped by the article folder copy
    copy_shared_assets()
    copy_all_article_assets(validated_articles)
    progress(f"Copied shared assets + {len(validated_articles)} article asset folders")

    # Convert raster images in each article's output folder to WebP (replacing originals).
    # Runs after the copy step so it operates on the output copy, leaving the source folder untouched.
    convert_all_article_images(validated_articles)
    progress(f"Converted {_IMAGE_CONVERSION_COUNT} images to WebP")

    lqip_thumbnails = generate_all_lqip_thumbnails(validated_articles)
    progress(f"Generated {sum(1 for v in lqip_thumbnails.values() if v)} LQIP thumbnails")

    generate_all_article_pages(validated_articles, lqip_thumbnails)
    progress(f"Generated {len(validated_articles)} article pages")

    generate_all_article_prints(validated_articles)
    progress(f"Generated {len(validated_articles)} print pages")

    generate_article_list_page(validated_articles, lqip_thumbnails)
    progress("Generated article-list page")

    generate_author_list_page()
    progress("Generated author-list page")

    generate_all_author_pages(validated_articles, lqip_thumbnails)
    progress(f"Generated {len(AUTHORS)} author pages")

    elapsed = time.perf_counter() - started
    print(
        f"Done: {len(validated_articles)} articles, {len(AUTHORS)} authors, "
        f"{_IMAGE_CONVERSION_COUNT} images, {_WARNING_COUNT} warning(s) "
        f"(took {elapsed:.2f}s)"
    )



if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # Already formatted as "Error: ..." by fail() or raised directly with a message.
        raise
    except Exception as e:
        if os.environ.get("ARTIPRESS_DEBUG", "").strip().lower() not in ("", "0", "false"):
            raise
        print(f"Error: unexpected failure — {type(e).__name__}: {e}", file=sys.stderr)
        print("Hint: set ARTIPRESS_DEBUG=1 to see the full traceback.", file=sys.stderr)
        sys.exit(1)