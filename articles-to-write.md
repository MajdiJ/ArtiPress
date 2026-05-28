# Articles to write

## Welcome to ArtiPress

The front-door article. Someone landing on the demo article list should be able to read this first and immediately understand what ArtiPress is and whether it's for them. Replaces both of the current generic example articles.

- One-paragraph pitch: drop-in folder, write Markdown, run one script
- Who it's for (and who it isn't — anyone needing a CMS or comments)
- Quick tour of what it generates (list page, article pages, author pages, print views)
- Link to the README for setup

## Why I built ArtiPress

The origin story — an expanded version of the README's second paragraph. Gives the project a human voice and gives the second author (Majdi) a reason to exist in the demo.

- The problem: keeping article page, list page, and SEO tags in sync by hand
- Why a backend felt like overkill for a personal static site
- Why Python + Markdown + JSON rather than an existing SSG
- What got cut from scope and why

## Writing your first article

A walkthrough that doubles as live documentation. Takes the reader from empty `content/` folder to a generated article page.

- Folder structure (`article.json`, `article.md`, `images/`)
- The required fields in `article.json` with a minimal working example
- Markdown conventions — start at `##`, image syntax, the auto-shift behaviour
- Running the generator and reading the output summary

## How related articles work

Explains the related-articles feature: how the keyword-overlap fallback picks siblings and when to override it with manual pins. Should `related_slugs`-pin a couple of other articles in this list to demonstrate the feature in situ.

- How keyword overlap is scored
- When to use `related_slugs` to pin manually
- When to use `excluded_related_slugs` to block a match
- Setting `related_articles_count: 0` to turn the whole thing off

## Markdown & styling reference

A reference page that intentionally exercises every renderable element. Doubles as a visual regression page when changing CSS, and as a "what does this look like?" lookup for writers. No cover image, so it also covers the no-image edge case in the list view.

- All heading levels, lists (ordered, unordered, nested), blockquotes
- Code blocks (inline and fenced), tables, horizontal rules
- Inline and block images, with and without alt text
- Links, emphasis, strikethrough

## Customising style and HTML templates

Probably the #1 thing a new user wants to know after getting the generator running: how do I make this look like *my* site? Walks through the template system end-to-end.

- Where templates live and which file maps to which page
- The variable system — how data from `article.json` reaches the templates
- Editing `components/` vs editing the base templates
- Where CSS lives and the split between `main.css` and the scoped files
- Pointing `base_template_paths` at custom files in `config.json`

## How ArtiPress is built for SEO and social sharing

A "what you get for free" article aimed at someone evaluating the project. Covers everything the generator emits to make articles discoverable and shareable.

- Generated `<meta>` tags from `article_strap_line` and `article_keywords_list`
- Open Graph and Twitter card tags for link previews
- Structured data (JSON-LD) for articles and authors
- Canonical URLs and how `base_url` feeds into them

## Gotchas and how ArtiPress catches them

Reframes a "common issues" post around the validation story: ArtiPress refuses to write any files until everything checks out, so most "issues" surface as clear errors before the build runs.

- The upfront validation pass — what gets checked
- Common errors: unknown author slug, missing image, malformed date
- Using `ARTIPRESS_DEBUG=1` for full tracebacks
- Image-conversion warnings and what they mean
