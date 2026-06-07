<h1>ArtiPress</h1>

<img align="left" src="docs/assets/artipress-logo.png" alt="ArtiPress logo" width="180" />

A static site generator for articles. Drop the `artipress/` folder into any existing website repo, write articles in Markdown, run one Python script, and get a fully generated article section: list page, individual article pages, author pages, print views, SEO metadata, and WebP images. No backend needed.

<br clear="left" />

I built this for my own portfolio website, which runs as a static site on Cloudflare Pages. I wanted articles on it, but managing them by hand in HTML would have meant keeping the article page, the list page, and all the SEO tags in sync every time I changed a title or description. That gets old fast. A full backend felt like overkill for a personal site with low traffic. So I wrote a Python script to generate everything from Markdown and JSON, it worked well for my site, and I turned it into its own project (ArtiPress!) so anyone in the same situation can use it.

## Prerequisites

- Python 3.10+
- Dependencies: `pip install -r requirements.txt` (Pillow and Markdown)

## Trying it locally

This repo ships with example articles in `artipress/content/`, but the generated `articles/` output folder is gitignored. To preview the demo site, install the dependencies and run the generator:

```sh
pip install -r requirements.txt
python artipress/artipress.py
```

Then open `articles/index.html` in your browser.

## Setup

1. Copy the `artipress/` folder into the root of your website repo.
2. Copy the `articles/` output folder into your repo (or point `output_path` — or, if the engine doesn't live at your webroot, the separate `output_disk_path`/`output_url_path` pair — in the config to wherever your site serves static files from).
3. Edit `artipress/config.json` with your site's details (see [Config](#config) below).
4. Update the templates in `artipress/templates/` to match your site's header, nav, and footer.
5. Add your authors to `artipress/authors.json`.
6. Run the generator.

## Writing an article

Each article lives in its own folder under `artipress/content/`:

```
artipress/content/
└── my-article-slug/
    ├── article.json   ← metadata
    ├── article.md     ← body content (Markdown)
    └── images/        ← any images referenced in the article
```

The folder name becomes the URL slug (e.g. `your-site.com/articles/my-article-slug/`).

### article.json

```json
{
  "article_title": "My Article Title",
  "author_slugs": ["jane-doe"],
  "article_strap_line": "A one-sentence summary shown on cards and in meta descriptions.",
  "date": {
    "published": "2026-05-21T00:00:00Z",
    "edited": "2026-05-28T00:00:00Z"
  },
  "article_image_url": "images/cover.png",
  "article_image_alt": "Descriptive alt text for the cover image",
  "article_labels": ["Python", "Tutorial"],
  "article_keywords_list": ["python", "tutorial", "beginner"],
  "related_slugs": [],
  "excluded_related_slugs": [],
  "hide_from_article_list": false,
  "convert_article_images_to_webp": true,
  "make_low_res_thumbnail": true
}
```

| Field | Required | Notes |
|---|---|---|
| `article_title` | Yes | Displayed as the article's `<h1>` |
| `author_slugs` | Yes | Array; each slug must exist in `authors.json` |
| `article_strap_line` | Yes | Subtitle shown on cards and in meta description |
| `date.published` | Yes | ISO 8601 (e.g. `2026-05-21T00:00:00Z`) |
| `date.edited` | No | Shown as "Edited on …" when set |
| `article_image_url` | No | Relative path from the article folder, or a full URL |
| `article_image_alt` | No | Alt text for the cover image |
| `article_labels` | No | Short tags shown on article cards |
| `article_keywords_list` | No | Used in `<meta keywords>` and related-article matching |
| `related_slugs` | No | Manually pin specific articles as related |
| `excluded_related_slugs` | No | Prevent specific articles from appearing as related |
| `hide_from_article_list` | No | `true` hides from the list but keeps the article page live |
| `convert_article_images_to_webp` | No | Default `true`. Converts images in `images/` to WebP |
| `make_low_res_thumbnail` | No | Default `true`. Generates a blurred LQIP placeholder for the cover image |

### article.md

Write the article body in standard Markdown. Headings should be `##` and lower — avoid `#`, since it maps to an `<h1>` tag and the page already has one (the generated article title). Using `#` is not semantically correct and will produce a warning. That said, if you do use it, ArtiPress will shift all headings down one level automatically rather than leaving broken structure.

Images can reference files from the `images/` folder: `![alt text](images/my-image.png)`. ArtiPress converts them to WebP automatically. WebP is better suited for the web than formats like PNG or JPEG — it produces significantly smaller file sizes at comparable quality, and ArtiPress also caps the resolution on conversion, so images load faster without noticeably affecting how they look on screen.

### Resources (images, videos, files)

Anything inside the article folder that isn't `article.md` or `article.json` is copied verbatim into the output, with the subfolder layout preserved. Reference resources by relative path from the article folder.

There's no enforced structure, but a shallow, conventional layout keeps things predictable:

```
artipress/content/my-article-slug/
├── article.json
├── article.md
├── images/        ← cover image and any inline images
├── videos/        ← optional, only if you have video clips
└── files/         ← optional, for PDFs and other downloads
```

Nest deeper if an article needs it (e.g. `images/diagrams/`, `images/screenshots/`) — the paths in your Markdown just have to resolve. Two things worth knowing:

- The LQIP placeholder is always written to `{slug}/images/` in the output. Keeping the cover image in `images/` keeps the source and the generated thumbnail in the same folder.
- Full URLs (`https://…`) and site-absolute paths (`/…`) are passed through untouched, so you can host assets elsewhere if you prefer.

## Authors

Authors are defined in `artipress/authors.json`:

```json
[
  {
    "author_name": "Jane Doe",
    "author_slug": "jane-doe",
    "author_bio": "Short bio. Markdown is supported.",
    "author_role": "Staff Writer",
    "author_picture_url": "default.svg",
    "social_links": {
      "github": { "handle": "janedoe", "link": "https://github.com/janedoe" },
      "linkedin": { "handle": "jane-doe", "link": "https://linkedin.com/in/jane-doe" }
    }
  }
]
```

The `author_slug` must be lowercase and hyphenated; it becomes the URL for the author's page. `author_picture_url` can be a filename inside `artipress/assets/author-pictures/` or a full URL.

Available social platforms are defined in `artipress/social_links.json`. The keys used in `social_links` (e.g. `github`, `linkedin`) must match keys in that file.

## Config

Edit `artipress/config.json`:

| Field | Default | Notes |
|---|---|---|
| `base_url` | — | Full site URL, no trailing slash (e.g. `https://example.com`) |
| `website_title` | `"ArtiPress"` | Site name used in page titles and metadata |
| `website_logo_url` | — | Full URL to your site logo |
| `output_path` | `"articles"` | Fallback for both of the below — used when only one path is needed |
| `output_disk_path` | `output_path` | Folder where generated files are written, relative to the project root |
| `output_url_path` | `output_path` | URL prefix baked into generated links and asset references, relative to the webroot |
| `recently_published_within_hours` | `168` | Hours before a "Recently Published" badge expires (168 = 1 week) |
| `related_articles_count` | `3` | Related articles shown per article page. Set to `0` to disable |
| `date_format` | `"{day} %B %Y"` | strftime pattern; `{day}` gives the day without a leading zero |
| `time_format` | `"%H:%M"` | Only shown when the published time is not midnight |

The `base_template_paths` and `components_template_paths` blocks point to the HTML templates. You generally won't need to change these unless you rename or move template files.

## Running the generator

From the project root:

```sh
python artipress/artipress.py
```

The script validates all articles and authors first. If anything's wrong (missing field, unknown author slug, missing image), it stops with an error before writing any files.

If everything passes, it prints a summary:
```
Done: 7 articles, 2 authors, 14 images, 0 warning(s) (took 1.23s)
```

## Output

The generator writes everything into the `output_disk_path` folder (default: `articles/`):

```
articles/
├── index.html                   ← article list page
├── _artipress/                  ← shared CSS, JS, icons (do not edit directly)
├── authors/
│   ├── index.html               ← author list page
│   └── jane-doe/
│       └── index.html           ← author profile page
└── my-article-slug/
    ├── index.html               ← article page
    ├── print.html               ← print-optimised view
    └── images/
        ├── cover.webp           ← converted from cover.png
        └── thumbnail.webp       ← LQIP blur-up placeholder
```

Commit the `articles/` output folder alongside your site's other static files.

## Customising templates

All templates are in `artipress/templates/`. Each one has a comment at the top listing which variables are required and which are optional. The base templates (`article_list.html`, `article_page.html`, etc.) are where you wire in your site's nav, header, and footer. The `components/` subdirectory has the smaller pieces like the article card layout and sharing bar; edit those to change the structure within a page.

CSS lives in `artipress/assets/style/`. `main.css` controls global layout; the other files are scoped to specific page types.

If you bring your own template file, update the corresponding path in `config.json`'s `base_template_paths` or `components_template_paths`.

## Debugging

Set `ARTIPRESS_DEBUG=1` to print a full traceback on unexpected errors:

```sh
ARTIPRESS_DEBUG=1 python artipress/artipress.py
```
