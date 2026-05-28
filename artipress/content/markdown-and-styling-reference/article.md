> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

A single page that exercises every Markdown element ArtiPress renders. Use it as a syntax lookup when writing, or as a visual regression target when you edit `article_md_elements.css` and want to see what changed.

This article has no `article_image_url` set, deliberately. That makes it the live test case for how the article-list card and the article page degrade when no cover image is provided. Both should still look correct.

The Markdown extensions enabled in `artipress.py` are `tables`, `fenced_code`, `footnotes`, `sane_lists`, and `md_in_html`. Anything outside that set renders as raw Markdown text. See the **Strikethrough** section near the bottom for an example.

## Headings

The page template already produces an `<h1>` from `article_title`, so the body starts at `<h2>`. Use `##` through `######` in your Markdown. Writing a `#` triggers ArtiPress's auto-shift safety net (it shifts everything down a level and prints a warning), so the convention is to start at `##` from the beginning.

### This is an h3

The next level down.

#### This is an h4

A subsection of a subsection.

##### This is an h5

##### sized for deeper outlines.

###### This is an h6

The smallest renderable heading. The auto-shift logic clamps at six, so even a shifted `<h6>` stays at `<h6>`.

## Paragraphs and emphasis

A normal paragraph reads like this. Inside a paragraph, words can be *italic*, **bold**, or ***bold and italic***. Underscores work too: _italic_ and __bold__.

`Inline code` is wrapped in single backticks. Multiple `inline` snippets in `one` paragraph behave as you'd expect.

Links come in two forms. A [direct link to the README](https://github.com/majdiJ/ArtiPress) puts the URL right in the text. A [reference-style link][artipress-repo] resolves to a definition further down. Both render to the same `<a>` tag.

[artipress-repo]: https://github.com/majdiJ/ArtiPress

## Lists

### Unordered

- First item
- Second item, with a slightly longer label so wrapping behaviour is visible
- Third item

### Ordered

1. First step
2. Second step
3. Third step

### Nested

- Top-level item
    - A nested unordered child
    - Another nested child
        - And one deeper still
- Second top-level item
    1. A nested ordered child
    2. A second nested ordered child
- Third top-level item

Indenting nested items by four spaces is the safest convention. The `sane_lists` extension is enabled, which makes the parser stricter about list boundaries and less surprising when lists sit next to paragraphs.

## Blockquotes

> A standard blockquote. The strap line at the top of every demo article uses this element.

Blockquotes nest:

> The outer quote.
>
> > The inner quote, indented one level.
> >
> > > A third level if you really need it.

## Code blocks

Inline code looks like `this`. Fenced code blocks use triple backticks.

Without a language hint:

```
def hello():
    return "world"
```

With a language hint (the renderer adds a `language-*` class for the styling to hook into):

```python
def hello() -> str:
    return "world"
```

```json
{
  "article_title": "Example",
  "author_slugs": ["majdi-jaigirdar"],
  "article_strap_line": "A one-line summary.",
  "date": { "published": "2026-05-28T00:00:00Z" }
}
```

```sh
python artipress/artipress.py
```

## Tables

A basic table:

| Field | Type | Required |
|---|---|---|
| `article_title` | string | Yes |
| `author_slugs` | array | Yes |
| `article_strap_line` | string | Yes |
| `date.published` | ISO 8601 | Yes |
| `article_image_url` | string | No |
| `article_labels` | array | No |

With column alignment (left, centre, right):

| Left aligned | Centre aligned | Right aligned |
|:---|:---:|---:|
| a | b | c |
| a longer cell | also longer | aligned right |
| short | x | 42 |

## Horizontal rules

Three dashes on their own line:

---

Three asterisks:

***

Three underscores:

___

All three render to the same `<hr>` element. Pick whichever is easiest to read in source.

## Images

Block images use the standard Markdown syntax. Any path that doesn't start with `http(s)://` or `/` is treated as relative to the article folder, copied into the output, and (with `convert_article_images_to_webp` left at its default `true`) converted to WebP. The `<img src>` in the generated HTML is rewritten to the `.webp` path so the link still works:

```markdown
![Alt text describing the image](images/diagram.png)
```

Omitting the alt text produces an empty `alt=""` attribute. That's correct for purely decorative images, and incorrect for anything carrying meaning. Assistive technologies will skip it:

```markdown
![](images/decorative-flourish.png)
```

A remote image is passed through unchanged. No copying, no WebP conversion, no LQIP. The `<img src>` is exactly the URL you wrote:

![ArtiPress logo](https://artipress.majdij.com/resource/image/logo.png)

Inline images sit inside a paragraph rather than on their own line. They use the same syntax, ![tiny inline copy](https://artipress.majdij.com/resource/image/logo.png), they just happen to land next to text. The CSS for `.article-md img` controls how this looks; constrain `max-height` there if inline images get unruly.

## Footnotes

The `footnotes` extension is enabled, so footnote syntax is supported[^demo-footnote]. The footnote definitions can sit anywhere in the document. They collect at the bottom of the rendered page regardless of where you write them[^second-one].

[^demo-footnote]: Like this. Footnote bodies can contain **inline formatting** and `inline code`.
[^second-one]: A second footnote, to show how the back-reference arrows render in sequence.

## Inline HTML

`md_in_html` is enabled, which lets HTML and Markdown share the page. A `<div>` that opts back in to Markdown processing via `markdown="1"`:

<div class="example-callout" markdown="1">

**This paragraph lives inside a `<div>`.** The `markdown="1"` attribute tells the parser to keep processing Markdown inside the element, so the bold above and the `inline code` here still render.

</div>

A `<details>`/`<summary>` block, useful for collapsible asides:

<details>
<summary>Click to expand</summary>
This content is inside a <code>&lt;details&gt;</code> element. The surrounding tags don't opt in to Markdown, so the contents are treated as raw HTML. Write Markdown inside here and it will not render.
</details>

## Strikethrough (not rendered)

Strikethrough is **not** enabled in ArtiPress's default extension set. Writing `~~text~~` does not produce a `<del>` element; the tildes render as literal characters:

~~This entire sentence is wrapped in double tildes and still renders normally.~~

If you want strikethrough, add a Markdown extension that provides it (for example `pymdownx.tilde` from `pymdown-extensions`) to the `_MD_EXTENSIONS` list in `artipress.py`. The same approach applies to anything else missing from the default set. Task lists, attribute lists, definition lists, and so on are all available as opt-in extensions.

## End of reference

Everything above runs through the same pipeline as any other article. Change the styling in `artipress/assets/style/article_md_elements.css`, rerun the generator, reload this page, and every element on the list will show the change in one place. That makes this article useful in two directions: as a syntax lookup when you're writing, and as the page to open first when you're editing CSS.
