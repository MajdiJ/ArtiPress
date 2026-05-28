> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

A demonstration article that puts every Markdown element ArtiPress renders into real prose, rather than listing them out. The [Markdown & styling reference](/articles/markdown-and-styling-reference/) is the exhaustive catalogue. This one is closer to what a normal post actually looks like.

## What you write versus what you see

Markdown gets out of the way. You write **bold** when you want a phrase to land. You write *italic* when you want a softer kind of emphasis, the sort that makes a reader slow down without quite realising why. ***Both at once*** when the moment calls for it. Inline `code` sits in the middle of a sentence without breaking the line height.

The default styling tries to be quiet enough that you can read past it. Most of the work of writing well in Markdown happens at the word level, not in the formatting.

---

## A quote, for atmosphere

> The first draft of anything is shit.
>
> — *Ernest Hemingway, probably*

---

## Lists

A short unordered list:

- One item.
- A second item, slightly longer so wrapping behaviour is visible.
    - A nested child.
    - Another nested child.
- A third top-level item.

A short ordered list:

1. Open the article folder.
2. Edit the Markdown file.
3. Run the generator.
4. Reload the page.

A task list. ArtiPress's default extensions don't include task lists, so the checkboxes render as literal `[x]` and `[ ]` rather than actual checkboxes:

- [x] Set up the repo.
- [x] Write the first article.
- [ ] Write a second article.
- [ ] Replace this list with something real.

---

## Code

Inline first: `const greet = name => "Hello, " + name`. Then a fenced block with a language hint, so the styling can colour it:

```javascript
function greet(name) {
  return `Hello, ${name}`;
}

console.log(greet("world"));
```

```bash
# Build the site
python artipress/artipress.py
```

---

## A table

The shape of the `article.json` schema, as a worked example:

| Field | Type | Required |
|---|---|---|
| `article_title` | string | Yes |
| `author_slugs` | array | Yes |
| `date.published` | ISO 8601 | Yes |
| `article_image_url` | string | No |
| `article_keywords_list` | array | No |

---

## An image

![A placeholder landscape](https://picsum.photos/seed/lorem/800/400)

*Fig. 1 — a stand-in cover image while you decide on real ones.*

---

## Links and footnotes

A direct link to the [README](https://github.com/majdiJ/ArtiPress) and a link to the [Markdown reference page](/articles/markdown-and-styling-reference/). External and internal both work; the path resolution is the same.

Footnotes are supported via the `footnotes` extension[^example]. They collect at the bottom of the rendered page regardless of where you define them.

[^example]: Like this. Footnote bodies can contain **inline formatting** and `inline code`.

---

## Nested blockquotes

Quotes nest as deeply as you want them to. The styling on each level should make the indentation visible without making the text harder to read:

> An outer thought.
>
> > A reply to the outer thought.
> >
> > > And a further reply to that one.

---

## Strikethrough (not rendered)

For completeness: ~~strikethrough~~ isn't enabled in the default extension set. The tildes appear as literal characters. The reference article covers the opt-in extension that adds it.

---

## Closing

Three asterisks for a horizontal rule:

***

*That's the loop. Write, save, regenerate. The rest is editing.*
