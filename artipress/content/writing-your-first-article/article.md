> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

This walks through writing an article from an empty `content/` folder to a generated page. It assumes you've already dropped ArtiPress into your repo and filled in `artipress/config.json`. The [README](https://github.com/majdiJ/ArtiPress) covers the setup part. Everything below picks up at the moment you decide to write a post.

## The folder

Every article lives in its own folder under `artipress/content/`. The folder name is the slug, and the slug becomes the URL path. A folder called `my-first-post` ends up at `/articles/my-first-post/` in the output.

A minimal article folder looks like this:

```
artipress/content/
└── my-first-post/
    ├── article.json
    ├── article.md
    └── images/
        └── cover.png
```

`article.json` holds the metadata. `article.md` holds the body. The `images/` folder is conventional but not required. It's just a folder, and ArtiPress copies it (along with anything else in the article folder) straight into the output. Only two filenames get treated specially: `article.json` and `article.md`. Everything else is copied verbatim.

That same rule applies to non-image resources. If an article needs videos, PDFs, or other downloads, drop them into the article folder and reference them by relative path. There's no enforced layout, but a shallow, conventional one (`images/`, `videos/`, `files/`) keeps things easy to scan when you come back to an article months later. Nest deeper if it helps (`images/diagrams/`, `images/screenshots/`); the only thing that matters is that the paths you write in Markdown resolve to real files on disk. One small reason to keep the cover image in `images/`: ArtiPress always writes its LQIP placeholder there, so source and generated files stay in the same folder.

One reserved name to know about: `authors`. The generator writes the author pages into `articles/authors/`, so a folder called `authors` inside `content/` would collide. Pick any other slug.

## The minimum article.json

Four required fields. The generator refuses to start if any are missing:

```json
{
  "article_title": "My First Post",
  "author_slugs": ["majdi-jaigirdar"],
  "article_strap_line": "A one-sentence summary, used on cards and as the meta description.",
  "date": {
    "published": "2026-05-28T00:00:00Z"
  }
}
```

That's a complete, valid `article.json`. Drop it into a folder with an `article.md`, run the generator, and you've published an article.

Every author slug in `author_slugs` must exist in `artipress/authors.json`. The strap line shows up on the article list card and inside the `<meta name="description">` tag in the head, so it's worth writing carefully. The published date is ISO 8601; the `Z` means UTC. If the time is exactly midnight, ArtiPress hides the time portion on the rendered page. Anything else, and you'll see "at HH:MM" appended.

A few more fields you'll usually want:

- `article_image_url` and `article_image_alt` give the article a cover image. The URL is a path relative to the article folder (for example, `images/cover.png`), or an absolute URL.
- `article_labels` are short tags shown on the article card.
- `article_keywords_list` feeds the `<meta keywords>` tag and gets used to score related-article matches.
- `date.edited` adds an "Edited on …" line under the byline.

All optional. Leave them out and the corresponding piece of the page either degrades gracefully or disappears.

## The Markdown body

Write `article.md` in standard Markdown. ArtiPress runs it through `python-markdown` with these extensions on: tables, fenced code blocks, footnotes, sane lists, and `md_in_html`. That covers everything you'd reasonably expect from a Markdown article.

### Start at ##, not #

The page already has an `<h1>` (the one generated from `article_title`). So in the body you should start at `##`. A page with two `<h1>` elements isn't semantically correct, and most accessibility tools will flag it.

ArtiPress won't let you ship a broken structure, though. If it spots an `<h1>` in your rendered Markdown, it shifts every heading in the body down one level (clamped at `<h6>`) and prints a warning. Use `##` and deeper from the start and you'll never see the warning. The auto-shift is there so a stray `#` doesn't silently produce a page with two competing top-level headings.

### Images

Image syntax is the normal Markdown form, with the path written relative to the article folder:

```markdown
![A descriptive alt text](images/diagram.png)
```

The generator copies the entire `images/` folder into the output. If `convert_article_images_to_webp` is left at its default (`true`), any raster image (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`) gets converted to WebP, resized down if it's wider than 1200px, and the original is deleted from the output. The Markdown still says `images/diagram.png`, but ArtiPress rewrites the `<img src>` in the generated HTML to `images/diagram.webp` so the link doesn't break.

Absolute paths and full `http(s)://` URLs are left alone. Use those for images hosted elsewhere or for SVGs you don't want re-encoded.

If you set the article's `article_image_url` to a local image, ArtiPress also generates a tiny blurred WebP placeholder (the "LQIP") that the article page loads first while the full image streams in. Set `make_low_res_thumbnail: false` to skip it.

### Everything else

Tables, fenced code blocks, lists, blockquotes, footnotes, inline HTML, they all work the way you'd expect. There's a separate reference article that exercises every renderable element if you want to see what each one looks like in the default styling.

## Running the generator

From the project root:

```sh
python artipress/artipress.py
```

The first thing it does is validate. It checks that the config file has every required field, that Pillow is installed, that every template file pointed at by the config actually exists on disk, that every article folder has an `article.md` and a valid `article.json`, and that every author slug referenced by an article exists in `authors.json`. If any of that fails, it prints an error and exits without writing a single file.

If validation passes, the build happens in stages and prints a progress line for each:

```
→ Validated 8 articles and 2 authors
→ Copied shared assets + 8 article asset folders
→ Converted 6 images to WebP
→ Generated 5 LQIP thumbnails
→ Generated 8 article pages
→ Generated 8 print pages
→ Generated article-list page
→ Generated author-list page
→ Generated 2 author pages
Done: 8 articles, 2 authors, 6 images, 0 warning(s) (took 1.18s)
```

The last line is the summary. The article count, author count, and image count are self-explanatory. The warning count covers everything non-fatal: `#`-heading shifts, missing social icons, anything ArtiPress wants to flag without stopping the build. A clean run is `0 warning(s)`. If you see anything else, scroll up; every warning is printed in full above the summary.

When the run finishes, you have a fresh `articles/` folder (or whatever you set `output_path` to). The article you just wrote is at `articles/<your-slug>/index.html`. Open it in a browser to preview.

## When something is wrong

ArtiPress is deliberately strict about errors. If the JSON is malformed, you see exactly which file. If a required field is missing, you see which field. If an author slug doesn't exist, you see which articles reference it. The aim is that the error message tells you what to fix without needing a traceback.

If you do hit something unexpected (a crash with no useful context, or behaviour you can't explain), set `ARTIPRESS_DEBUG=1` and re-run:

```sh
ARTIPRESS_DEBUG=1 python artipress/artipress.py
```

That prints the full Python traceback instead of the friendly summary. It's almost always a bug worth reporting on GitHub if you need it.

That's the loop. Write two files in a folder, run one command, get an article. Repeat as needed.
