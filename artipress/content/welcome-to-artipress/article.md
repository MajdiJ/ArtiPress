> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

ArtiPress is a static site generator for articles. You drop the `artipress/` folder into your website repo, write your articles in Markdown, and run one Python script. What comes out is a full article section: a list page, individual article pages, author pages, print views, SEO metadata, and pre-converted WebP images. There's no database, no backend, and no build pipeline that needs babysitting.

## Who this is for

ArtiPress is for people running a small static site (a portfolio, a project site, a personal blog) who want to add articles without standing up a CMS. If you already deploy HTML to Cloudflare Pages, GitHub Pages, or Netlify, it slots into your existing workflow without changing anything around it.

It's probably not for you if you need any of these:

- A web UI for writing posts. ArtiPress writes from your local filesystem.
- Reader comments, likes, or other dynamic features.
- Scheduled publishing, drafts behind auth, or a multi-author editorial workflow.
- Hundreds of articles a day from non-technical authors.

If any of those sound essential, you want a real CMS, not this.

## What you get when you run it

You write two files per article (`article.json` for the metadata, `article.md` for the body), and ArtiPress generates the rest:

- An article list page at the root of the output folder, with cards for every article.
- A page per article, with cover image, byline, related articles, and a sharing bar.
- A print-friendly view for each article at the same URL plus `/print.html`.
- Author pages built from `authors.json`, one per author, plus an author index.
- SEO and social tags (Open Graph, Twitter cards, JSON-LD structured data, canonical URLs) generated from the same metadata you already wrote.
- WebP image conversion, with a low-resolution blur-up placeholder for cover images.

It all lands in a single output folder. Commit that alongside the rest of your static site and you're done.

## Getting started

The [README](https://github.com/majdiJ/ArtiPress) walks through setup from start to finish: dropping the folder in, editing `config.json`, adding authors, and running the generator. The other articles in this demo cover the rest. Writing your first article, customising the templates, how related articles work, and what ArtiPress gives you for SEO out of the box.

If you want a tour, the article list is a good place to start.
