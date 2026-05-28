> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

A tour of everything ArtiPress emits to make articles discoverable, citable, and shareable. The same `article.json` fields you fill in for the page itself feed every meta tag, structured-data field, and link preview on the page.

The point of putting all of this in the generator is that you only ever write the data once. The article title sits in `article_title`. The summary sits in `article_strap_line`. The keywords sit in `article_keywords_list`. ArtiPress fans those values out into every place a search engine, social platform, or aggregator might look for them. Change the strap line, and the meta description, Open Graph description, Twitter card description, and structured-data description all change with it.

## The basic `<meta>` block

The article-page template pulls in a component called `article_page_head_metadata.html`. It opens with the standard set of tags every page needs:

```html
<title>{article_title} | {website_title}</title>
<link rel="canonical" href="{base_url}/{output_path}/{article_id}" />
<meta name="description" content="{article_strap_line}" />
<meta name="keywords" content="{article_keywords_list}" />
```

The canonical URL is the article's permanent address on the site. Search engines use it to deduplicate identical content reached via different URLs (with and without a trailing slash, with and without UTM parameters, and so on). It's built from `base_url` in `config.json`, the output folder name, and the article slug.

The meta description is the strap line from `article.json`. That string shows up in three places: under the title in search results, in the article-list card on the site, and as the description in the link preview when someone shares the article. Treat it as the one-sentence pitch for the article.

The keywords meta is built from `article_keywords_list`, comma-separated. Modern search engines barely use it for ranking, but it's still useful because ArtiPress reuses the same list for the related-articles overlap score (see the [related articles article](/articles/how-related-articles-work/) for that algorithm).

## Author meta tags

Every author slug in the article's `author_slugs` list produces a separate `<meta name="author">` tag:

```html
<meta name="author" content="Majdi Jaigirdar" />
```

The name resolves through `authors.json`. The slug in the article references the entry there, and the entry's `author_name` is what ends up in the tag. Co-authored articles produce one tag per author, in the order they're listed.

## Open Graph

Open Graph is what Facebook, LinkedIn, Slack, Discord, iMessage, and most other platforms read when someone pastes a link. ArtiPress emits the full set:

```html
<meta property="og:title" content="{article_title} | {website_title}">
<meta property="og:description" content="{article_strap_line}">
<meta property="og:image" content="{base_url}{article_featured_image}">
<meta property="og:url" content="{base_url}/articles/{article_id}">
<meta property="og:type" content="article">
```

The `og:image` is built from the article's `article_image_url`. If the article has a cover image, the link preview will use it. If `article_image_url` is empty, the property still exists but resolves to just the `base_url`, which most platforms will fall back to a generic preview on. Setting a cover image is the single biggest improvement you can make to how your article looks when shared.

`og:type` is fixed to `article`. That unlocks two more properties Open Graph defines specifically for articles:

```html
<meta property="article:published_time" content="2026-05-28T00:00:00Z" />
<meta property="article:modified_time" content="..." />
```

Both are ISO 8601 timestamps from `article.json`'s `date.published` and `date.edited`. They feed into how platforms display the article's recency in the preview.

Each author also produces a profile URL:

```html
<meta property="article:author" content="{base_url}/articles/authors/majdi-jaigirdar" />
```

That points at the author's profile page, which ArtiPress generates from `authors.json`. The link is what lets a platform attribute the article to a specific person, not just a name string.

## Twitter cards

Twitter (now X) reads a different set of tags, but ArtiPress emits both so the same article looks correct on either:

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{article_title} | {website_title}">
<meta name="twitter:description" content="{article_strap_line}">
<meta name="twitter:image" content="{base_url}{article_featured_image}">
```

The card type is `summary_large_image`, which renders the cover image at full width in the tweet. That's the modern default and what most readers will expect.

The data sources are the same fields you've already filled in: title, strap line, cover image. Nothing to fill in twice.

## JSON-LD structured data

JSON-LD is the structured-data format Google and most other search engines use to understand what a page is. It's how a search result gets enhanced with the article's headline, date, image, and author rather than just being a blue link.

ArtiPress emits a complete `Article` object in `<script type="application/ld+json">`:

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "{base_url}/articles/{article_id}"
  },
  "headline": "{article_title}",
  "description": "{article_strap_line}",
  "image": ["{base_url}{article_featured_image}"],
  "author": [
    {
      "@type": "Person",
      "name": "Majdi Jaigirdar",
      "url": "{base_url}/articles/authors/majdi-jaigirdar"
    }
  ],
  "publisher": {
    "@type": "Organization",
    "name": "{website_title}",
    "logo": {
      "@type": "ImageObject",
      "url": "{website_logo_url}"
    }
  },
  "datePublished": "2026-05-28T00:00:00Z",
  "dateModified": "..."
}
```

The `author` field is an array of `Person` objects, one per author, each linked to the corresponding author page. The `publisher` is built from `website_title` and `website_logo_url` in `config.json`. That's the only place those two are used in the structured data, so make sure both are filled in for the publisher card to render properly in search results.

You can paste a generated article URL into [Google's Rich Results Test](https://search.google.com/test/rich-results) to confirm everything parses as expected.

## How `base_url` ties it all together

Every absolute URL on the page (the canonical, the Open Graph URL, the structured-data IDs, the social-sharing links) is built from `base_url` in `config.json`. Set it correctly and every preview points at the right place. Forget the trailing-slash rule (no trailing slash) and you'll get double slashes in shared links.

A small but important detail: `base_url` is also used to absolutise the cover image URL for Open Graph and Twitter cards. Social platforms expect absolute URLs there, not relative paths. That's why the templates concatenate `{base_url}{article_featured_image}` rather than emitting the path as-is.

## What you actually need to fill in

The good news: the data you need to fill in for full SEO and social coverage is the same data you'd fill in to write a decent article anyway.

In `article.json`:

- `article_title`. Already required.
- `article_strap_line`. Already required, and pulls double duty as meta description, OG description, Twitter description, and structured-data description.
- `date.published`. Already required.
- `author_slugs`. Already required, with the names and URLs resolved from `authors.json`.
- `article_image_url`. Optional, but worth setting. Every link preview improves dramatically with a cover image.
- `article_keywords_list`. Optional, but free leverage. The same list feeds related-article matching.

In `config.json`:

- `base_url`. Required for anything that needs an absolute URL.
- `website_title`. Used in the title tag suffix, the OG title, the Twitter title, and the structured-data publisher.
- `website_logo_url`. Used in the structured-data publisher logo.

Get those eight fields right and every article ArtiPress generates ships with a full SEO and social-sharing footprint, with no extra work per post.
