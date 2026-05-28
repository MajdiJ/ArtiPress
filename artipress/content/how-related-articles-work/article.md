> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

The "Related articles" section at the bottom of every article page is built by a small ranking function. This is a walkthrough of how it picks, in what order, and which fields you set in `article.json` (and `config.json`) to override its choices.

The two articles pinned to the bottom of *this* page were chosen manually, using the mechanism described below. The third and fourth cards (if you see them) were filled in by the keyword-overlap stage. Treat the section as a live demo.

## The three stages, in order

ArtiPress fills each article's "Related articles" section by working through three stages and stopping as soon as it has enough cards. The target is set by `related_articles_count` in `config.json`. The demo site uses `4`. The default if you don't set it is `3`.

The stages run in this order:

1. **Manual pins.** Slugs in the current article's `related_slugs` field, in the order you wrote them.
2. **Keyword and label overlap.** Other articles ranked by how many keywords/labels they share with this one.
3. **Most recent.** Anything still missing is filled with the most recently published articles.

The first stage that produces enough hits wins. If you pin four articles and `related_articles_count` is four, stages two and three never run.

The current article is always skipped, and the same slug is never added twice. Everything else is a question of which stage picks it.

## Stage 1: manual pins (`related_slugs`)

`related_slugs` is an array of article slugs you want forced into the section, in the order you want them shown:

```json
"related_slugs": ["welcome-to-artipress", "writing-your-first-article"]
```

Use this when you know better than the keyword scorer does. A few cases come up often:

- The two articles are part of a series and you want the next instalment to lead.
- One article cites another directly and that link should always surface.
- The keyword overlap would pick something technically related but topically wrong (two posts that both use the keyword "python" but cover very different things, say).

Two behaviours worth knowing. Manual pins **can include hidden articles**: articles with `hide_from_article_list: true` are normally invisible to the related-articles algorithm, but a manual pin overrides that. It's how you reference a deliberately unlisted article from another article without making it public. Second, manual pins **beat `excluded_related_slugs`**. If a slug appears in both, the manual pin wins. The exclusion list only blocks the automatic stages.

If a slug in `related_slugs` does not match any real article folder, it's silently ignored. Mistype it and your article just falls back to whatever stage two would have picked.

## Stage 2: keyword and label overlap

If manual pins don't fill the slot count, ArtiPress scores every other article against the current one and ranks them by how much they have in common.

The score is the size of the set intersection between two sets:

- The current article's set: `article_keywords_list` ∪ `article_labels`, lowercased.
- Each candidate article's set: same fields, same treatment.

So if this article's keywords are `["artipress", "related articles", "manual pins"]` and a candidate article's keywords are `["artipress", "tutorial", "markdown"]`, they share `artipress` and the score is 1. Duplicates within an article don't double-count. Both lists are merged into a `set` before the overlap is calculated.

Ties are broken by publication date, newer wins. So among articles that share the same number of terms with the current one, the most recently published comes first.

A few rules apply to which candidates are even considered:

- Articles with `hide_from_article_list: true` are skipped.
- Articles listed in the current article's `excluded_related_slugs` are skipped.
- Articles with **zero** overlapping terms are skipped (a score of 0 doesn't count as a candidate; it falls through to stage 3).

The practical takeaway: keywords matter. The same word in two articles' `article_keywords_list` is what makes them related as far as ArtiPress is concerned. If two related articles aren't finding each other, the fastest fix is to add a couple of shared keywords. If two unrelated articles keep pairing up, the fix is to remove the keyword that links them or add the other one to your `excluded_related_slugs`.

Labels count the same as keywords for the purpose of overlap. That's occasionally useful. A label is shorter and shows up on the card, so it has two jobs. But it also means a generic label like "Reference" will pull in everything else marked "Reference" too.

## Stage 3: recency fallback

If stages 1 and 2 between them haven't produced `related_articles_count` cards, ArtiPress fills the rest by walking the full article list (already sorted most-recent-first by the validation pass) and adding articles one at a time until the section is full.

`excluded_related_slugs` and `hide_from_article_list: true` are still respected here. The current article and anything already picked are still skipped.

Stage 3 is the reason a brand-new article with no keywords will still have a populated "Related articles" section. It falls all the way through and grabs the four most recent posts. That's usually fine for a single article. It's not a great long-term solution. Filling the keywords list is what makes stage 2 do useful work.

## `excluded_related_slugs`: blocking specific matches

`excluded_related_slugs` is the opposite of `related_slugs`. Listing a slug here removes it from consideration by stages 2 and 3 of the current article only:

```json
"excluded_related_slugs": ["example-article-artipress"]
```

Reach for it when the keyword scorer keeps surfacing a particular article that doesn't belong in this context. The most common reason: two articles share a generic keyword like "markdown" or "python" without actually being about the same topic.

The exclusion is one-directional. Putting article B in article A's exclusion list doesn't stop A from appearing under B. You'd need to add A to B's exclusion list separately. The asymmetry is intentional: relevance can be one-way.

And, again: a slug in both `related_slugs` and `excluded_related_slugs` will still appear. Manual pins beat exclusions.

## Turning the section off entirely

If you want no "Related articles" section anywhere on the site, set:

```json
"related_articles_count": 0
```

in `config.json`. ArtiPress treats `0` as a hard off-switch and skips the work entirely. The section is left blank and the template's `{html_var(related_articles)}` resolves to an empty string, which collapses out of the page.

There's no per-article way to hide the section on one page. Setting `related_articles_count` to 0 in `config.json` is global. If you want a single article without related cards, the workaround is to pin one article via `related_slugs` and add the rest to `excluded_related_slugs`. But at that point you're fighting the feature. Turning it off site-wide is usually the right call.

## A quick mental model

When you're deciding what to put in `article.json`, the order of operations to keep in your head is:

1. If you have specific articles that should always appear: put them in `related_slugs`.
2. Make sure `article_keywords_list` is filled with terms that genuinely describe the article. Stage 2 lives or dies on this list.
3. If a specific article keeps wrongly pairing up with this one, add it to `excluded_related_slugs`.
4. If you don't care about the section site-wide, set `related_articles_count: 0` and stop thinking about any of this.

For most articles you'll only ever touch step 2. Steps 1 and 3 are escape hatches for the cases where the keyword scorer isn't enough on its own.
