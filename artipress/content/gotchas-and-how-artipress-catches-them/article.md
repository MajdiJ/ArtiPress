> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

ArtiPress is deliberately strict. The generator validates the entire site before it writes a single file, and most of what would have been a "common issue" elsewhere surfaces here as a clear error message that stops the build. This article walks through what gets checked, what each error looks like, and the two tools you have for everything else: warnings and `ARTIPRESS_DEBUG`.

The reason for the strictness is that the alternative is worse. A half-built `articles/` folder, half of it new and half of it from a previous run, is a much harder problem to diagnose than an error message telling you exactly what was wrong. ArtiPress would rather refuse to start than leave you with a partial build.

## The upfront validation pass

Before any HTML is written, the generator runs through a series of checks. Each one fails fast with a specific, named error. Here's the full list, roughly in the order they happen.

### Config file

`artipress/config.json` must exist, must be valid JSON, and must contain the required fields: `base_template_paths.article_list`, `base_template_paths.article_page`, `base_template_paths.author_page`, `base_template_paths.author_list`, `input_content_folder`, and `output_path`. Missing a field produces an error naming the missing key.

### Pillow

The Python imaging library is a hard dependency. ArtiPress uses it for WebP conversion and LQIP thumbnail generation. If it's not installed, the generator stops with a hint to run `pip install -r requirements.txt`.

### Template files

Every path in `base_template_paths` and `components_template_paths` is checked. Any missing file stops the build with the config key and the path that failed:

```
Error: template 'article_page': file missing at artipress/templates/article_page.html
```

This is the check that catches typos in `config.json` after moving templates around.

### authors.json and social_links.json

`authors.json` must exist, must be valid JSON, must be a JSON array (not an object). `social_links.json` must exist, must be valid JSON, must be a JSON object.

### article.md per folder

Every folder under `artipress/content/` must contain an `article.md`. Missing files are listed in one error so you can fix them all at once.

### article.json per folder

Every article folder must have an `article.json`, it must be valid JSON, and it must contain the required fields: `article_title`, `author_slugs`, `article_strap_line`, and `date.published`. Any failing folder names itself in the error.

### Author references

Every slug used in any article's `author_slugs` must exist in `authors.json`. A single error lists every unknown slug and which article folders reference it:

```
Error: authors.json: the following author slugs are referenced by articles but not defined:
  - 'jane-doe' (referenced by: example-article, my-second-post)
```

This is the check that catches the most common mistake, which is adding a new author to an article and forgetting to register them.

### Cover image existence

When an article sets `article_image_url` to a local path, the generator verifies the file actually exists on disk before generating the LQIP thumbnail. A missing image fails with the article folder name and the resolved path.

If every check passes, the generator prints `Validated N articles and M authors` and starts writing files. If anything fails, nothing is written.

## Common errors and what they actually mean

A few specific error messages come up often enough to be worth calling out.

### Unknown author slug

```
Error: authors.json: the following author slugs are referenced by articles but not defined:
  - 'new-author' (referenced by: my-article)
```

You added a slug to `article.json`'s `author_slugs` but didn't add a matching entry to `artipress/authors.json`. The fix is to add the entry. The slug must be lowercase and hyphenated (it becomes a URL).

### Missing cover image

```
Error: article 'my-article': article_image_url points to a missing file: artipress/content/my-article/images/cover.png
```

`article_image_url` resolves relative to the article's source folder. The most common cause is the file living somewhere else. For example, you wrote `images/cover.png` but the actual file is at `assets/cover.png`, or you renamed the file and forgot to update the JSON. Either move the file or update the path.

The error refers to the *source* path, not the output path. ArtiPress checks the source before it generates anything in the output folder.

### Malformed date

The date field is parsed with Python's `datetime.fromisoformat`. The format ArtiPress writes everywhere is ISO 8601 with a `Z` suffix:

```json
"date": { "published": "2026-05-28T00:00:00Z" }
```

If the date is malformed (e.g. `2026/05/28` or `28-05-2026`), the parser fails. Rather than crashing, the format function returns the original string, which means a malformed date appears verbatim in the rendered page: `2026/05/28` shown to the reader exactly as you typed it. That's not an error per se, but it's a sign the JSON needs fixing.

The safest format is the one shown above: ISO 8601, midnight UTC, with the `Z` suffix. If the time is exactly midnight, ArtiPress hides the time portion on the page. If it's anything else, the time is appended as "at HH:MM".

### Invalid JSON

```
Error: article folder 'my-article': Invalid JSON in file 'artipress/content/my-article/article.json': Expecting ',' delimiter: line 9 column 5 (char 142)
```

The article folder name, the file path, and the parser's line and column number are all in the message. Open the file, jump to the line, look for the missing comma, brace, or quote. JSON doesn't allow trailing commas. That catches everyone at least once.

### Missing template file

```
Error: template 'article_page': file missing at artipress/templates/article_page.html
```

The config key and the path that failed are both in the message. Either the file genuinely isn't there, or you moved templates around and forgot to update `config.json`.

## Warnings: non-fatal but worth reading

The build doesn't stop on warnings. They print to stderr as the generator runs and get tallied in the summary line:

```
Done: 8 articles, 2 authors, 6 images, 3 warning(s) (took 1.18s)
```

A non-zero warning count means scroll up. Each warning is on its own line and prefixed with `Warning:`. The ones you'll see most often:

### `#` (h1) used in markdown — headings shifted down

The article's Markdown contained an `<h1>`-producing heading (`#` at the start of a line). The page already has an `<h1>` from the article title, so ArtiPress shifted every heading down one level to keep the structure valid. The fix is to start at `##` in your Markdown.

### Social platform not found in social_links.json

An author's `social_links` block references a platform key that isn't in `artipress/social_links.json`. Typically a typo or a new platform that hasn't been registered. The link is skipped on the author page. Add the platform to `social_links.json` or fix the typo.

### Icon file missing for platform

A platform is registered in `social_links.json` but the icon file it points to doesn't exist in `artipress/assets/icons/`. The link is skipped. Add the icon file or update the registry to point at a file that exists.

### LQIP skipped — article_image_url is a remote URL

The cover image is hosted somewhere else (e.g. `https://cdn.example.com/cover.jpg`), so ArtiPress can't generate a local low-resolution placeholder for it. The page still renders fine. It just loads the cover image directly with no blur-up. If you want LQIP, copy the image into the article folder and use a local path.

## Image conversion warnings

The WebP conversion step (controlled per-article by `convert_article_images_to_webp`, default `true`) is treated as a hard requirement, not a best-effort. If Pillow can't convert one of the article's images, the generator stops with the article folder name and the file path that failed. The reason is that the generated HTML rewrites `<img src>` paths to `.webp`. Leaving the original on disk would produce broken links.

If you want to leave images alone for a specific article (for example, you have a heavily optimised image you don't want re-encoded, or an animated GIF the conversion would flatten), set `"convert_article_images_to_webp": false` in that article's `article.json`. The generator will copy the file unchanged and emit the original path in the HTML.

## Output cleanup: anything stale gets removed

At the end of a successful build, ArtiPress sweeps the output folder and removes anything that isn't accounted for by the current source. At the root of `output_path` (default `articles/`), the only entries kept are `index.html`, the shared-assets folder (`_artipress/` by default), the `authors/` folder, and one folder per article in `content/`. Inside `authors/`, only `index.html` and one folder per slug in `authors.json` are kept. Everything else is deleted, and the removed entries are listed in the build output:

```
→ Removed 2 stale output entries: old-article-slug, authors/former-contributor
```

This is usually what you want. Rename a content folder and the old slug's output folder disappears. Delete an article and its page is gone next build. Remove an author from `authors.json` and their `/authors/{slug}/` page goes with them.

Two cases where it bites:

- **You renamed a slug and links to the old URL still exist.** Other articles' `related_slugs`, external links, the search-engine cache — all now 404. ArtiPress doesn't write redirects. Either keep the old slug, add a redirect rule at your hosting layer, or accept the 404s.
- **You put your own files into `output_path/`.** A hand-written `robots.txt`, a Cloudflare `_redirects` file, or any other static asset dropped at the root of `articles/` will be removed on the next build. Keep those files elsewhere in your site repo and let your build pipeline put them in place.

Cleanup only runs after generation succeeds. A validation failure mid-build leaves the output alone, so a failed run never destroys output from a previous successful one.

## `ARTIPRESS_DEBUG=1`: the escape hatch

Most errors are caught by the validation pass and produce friendly, named messages. A small number (internal bugs, unexpected I/O failures, edge cases the validation didn't cover) print only a one-line summary:

```
Error: unexpected failure — KeyError: 'article_title'
Hint: set ARTIPRESS_DEBUG=1 to see the full traceback.
```

For those, set `ARTIPRESS_DEBUG` to anything other than empty, `0`, or `false` and re-run:

```sh
ARTIPRESS_DEBUG=1 python artipress/artipress.py
```

The full Python traceback prints instead of the friendly summary. The line numbers and the call chain are usually enough to identify either the article or the template that triggered the problem. If you can't make sense of it, an issue with the traceback attached is the right next step.

## The general philosophy

The pattern across all of this: ArtiPress would rather fail loud at the start of the build than produce a partial output that silently breaks something downstream. Every error includes the file and the field that caused it. Every warning points at the article or author it applies to. The result is that "common issues" mostly stop being a category. They surface as specific, actionable error messages before any HTML reaches disk.

If you do hit something the generator doesn't explain clearly, that's a bug worth reporting. The aim is for the error to be the documentation.
