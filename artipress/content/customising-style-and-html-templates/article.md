> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

After your first generator run, the next thing you'll want is to make ArtiPress look like the rest of your site. This walks through the template and styling layout: where each file lives, how the variable substitution works, and which knobs to turn for which kind of change.

ArtiPress is structured so the generator doesn't care where any of these files live. Every template path is a setting in `config.json`. Move a file, point the config at the new location, and the build keeps working. The defaults are sensible starting points, not magic conventions.

## The template layout

There are two folders to know about, both inside `artipress/templates/`.

`artipress/templates/` itself holds the **base templates**, one per page type the generator produces:

- `article_list.html`: the article list page (the root of the output folder).
- `article_page.html`: an individual article page.
- `article_print.html`: the print-friendly view of an article.
- `author_list.html`: the author index page.
- `author_page.html`: an individual author page.

These are the files where your site's header, navigation, and footer live. Editing them is how you make ArtiPress's pages look like part of your existing site.

`artipress/templates/components/` holds smaller, reusable pieces that the base templates pull in:

- `article_page_head_metadata.html`: title tag, canonical URL, meta description, Open Graph, and Twitter card tags.
- `articles_page_styling_and_scripts.html`: the `<link rel="stylesheet">` and `<script>` lines for article pages.
- `article_page_head_application_json_ld.html`: the JSON-LD structured-data script.
- `article_page_main_article.html`: the article body layout (header, sharing bar, image block, content, footer).
- `article_list_item.html`: a single card on the article list (also used inside the "Related articles" section).
- `article_list_styling_and_scripts.html`: styles and scripts for the list page.
- `author_list_item.html` and `author_list_styling_and_scripts.html`: the author index counterparts.
- `author_page_styling_and_scripts.html`: styles and scripts for an individual author page.
- `author_social_link.html`: a single social-link icon in the author profile.

The general rule: if the change you want is about the chrome around the article (header, nav, footer, sidebars), edit the base templates. If it's about the structure inside a particular block (the layout of a card, the order of items in the metadata block, what shows in the sharing bar), edit the matching component.

## The variable system

Every template is a plain HTML file with one extra syntax: `{html_var(some_name)}`. The generator does a regex pass over each template before writing the output, replacing every `{html_var(...)}` with the corresponding value.

A template can use two kinds of variables.

**Direct variables** are simple strings or numbers that come from `article.json` and `config.json`. The article page template can use any of these directly:

- `{html_var(article_title)}`: the article title.
- `{html_var(article_strap_line)}`: the strap line / meta description.
- `{html_var(article_authors)}`: the rendered HTML for the byline (linked author names).
- `{html_var(article_published_date)}`: the formatted published date.
- `{html_var(article_id)}`: the article slug.
- `{html_var(base_url)}`: the site base URL from `config.json`.
- `{html_var(website_title)}`: the site name from `config.json`.
- `{html_var(output_path)}`: the output folder name (e.g. `articles`).
- `{html_var(assets_url)}`: the URL prefix where shared CSS, JS, and icons are served from (e.g. `/articles/_artipress`).

**Component variables** are larger pieces of HTML that the generator builds by rendering a component template and substituting it in. The article page template uses:

- `{html_var(article_page_head_metadata)}`: the full `<meta>` block.
- `{html_var(articles_page_styling_and_scripts)}`: the styles and scripts.
- `{html_var(article_page_head_application_json_ld)}`: the JSON-LD block.
- `{html_var(article_page_main_article)}`: the article body.
- `{html_var(related_articles)}`: the optional related-articles section (an empty string when disabled or when there are no candidates).

Substitution runs in two passes. The first injects component contents and resolves direct variables in the outer template. The second resolves any `{html_var(...)}` references that lived *inside* the injected component contents. So a component can use its own variables (resolved when the component is rendered standalone, e.g. in `articles_page_styling_and_scripts.html`) and the outer template's variables (resolved on the second pass).

A useful side effect: if you reference an unknown variable, the generator fails loudly with the template's name and the variable that was missing. There's no silent fallback. Typo a name and you'll see it on the next run.

## Editing components vs editing base templates

A worked example. Say you want to remove the WhatsApp icon from the article's sharing bar. The sharing bar lives inside the `<article>` block, so it's a component-level change. Open `artipress/templates/components/article_page_main_article.html`, delete the `<li>` block containing the WhatsApp link, save. Done. The next generator run produces pages without it.

Now say you want to add a sidebar to every article page that shows your recent posts from a different part of your site. That's chrome around the article, so it's a base-template change. Open `artipress/templates/article_page.html`, add your `<aside>` next to the `<main>`, save, regenerate.

The split holds for the author and list pages too. The base template owns the page shell; the component owns the repeating structure inside it.

## Where CSS lives

All CSS is in `artipress/assets/style/`:

- `main.css`: global layout, typography defaults, and anything that should apply across every page.
- `article_md_elements.css`: styles for the elements rendered from Markdown (headings, paragraphs, lists, code blocks, tables, blockquotes). This is the file to edit when you want headings or code blocks to look different.
- `article_main_element.css`: the layout of the article page itself (header, byline, sharing bar, footer).
- `article_list_cards.css`: the card layout on the article list page and the related-articles section.
- `author_list_cards.css`: the card layout on the author index page.
- `author_page_base.css`: the layout of an individual author page.
- `lqip.css`: the styles that make the low-resolution placeholder image fade out as the full image loads.

The split is by scope. `main.css` is loaded on every page; the others are loaded only on the pages that need them. The generator copies the whole `artipress/assets/` folder into the output as `articles/_artipress/`, so the templates reference styles via `{html_var(assets_url)}/style/...`.

If you want to add your own CSS file, drop it in `artipress/assets/style/` and add a `<link rel="stylesheet">` to whichever component pulls in the styles for the page you want it on. Usually that's `articles_page_styling_and_scripts.html` for article pages, or `article_list_styling_and_scripts.html` for the list page.

## Pointing the config at custom files

If you want to keep ArtiPress on its own update cadence, don't edit the files in `artipress/templates/` directly. Make copies somewhere else in your repo and point the config at the copies. Every template path lives in `artipress/config.json` under `base_template_paths` or `components_template_paths`:

```json
{
  "base_template_paths": {
    "article_list": "artipress/templates/article_list.html",
    "article_page": "site/templates/articles/page.html",
    "article_print": "artipress/templates/article_print.html",
    "author_page": "artipress/templates/author_page.html",
    "author_list": "artipress/templates/author_list.html"
  },
  "components_template_paths": {
    "article_page_head_metadata": "artipress/templates/components/article_page_head_metadata.html",
    ...
  }
}
```

That example points `article_page` at a custom file at `site/templates/articles/page.html` while leaving every other path on the defaults. The generator resolves each path relative to the project root.

The path checks happen at startup. If any file pointed at by the config is missing, the generator stops before any work happens, naming the key and the path that failed. That makes it safe to move templates around: a typo or missing file is caught immediately, not after a half-finished build.

## A practical order of operations

For most sites, the customisation order that wastes the least time is roughly:

1. Edit the base templates first to plug in your site's header, nav, and footer. The article list and article page templates are the highest-leverage edits. Start there.
2. Open the article list page and a sample article page in a browser. Make sure your chrome is rendering and is positioned the way you want it.
3. Tune `main.css` for typography and global colour. Most other styling decisions will hang off the choices you make here.
4. Open the [Markdown & styling reference](/articles/markdown-and-styling-reference/) and use it as a live regression page while you edit `article_md_elements.css`. Every renderable element is on that one page.
5. Adjust the component templates if you need to change the structure inside a card, the order of items in a header, or which icons appear in the sharing bar.
6. Only point `config.json` at custom paths once you've decided you want to keep ArtiPress's defaults pristine. Until then, editing the files in place is fine. They're yours.

Everything above is reversible. The generator never edits the templates or CSS. It only reads them. You can iterate as aggressively as you like.
