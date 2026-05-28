> This article serves two purposes: showing how ArtiPress turns a Markdown file and an article.json into a finished article page, and giving the list view, article page, and author page something real to render while you work on the design and layout.

I built ArtiPress because I wanted articles on my portfolio site and none of the existing options fit the way I already worked. My site is static, deployed to Cloudflare Pages. The HTML, CSS, and assets live in a repo, I push a commit, and the site is live a minute later. That workflow is the whole reason I like maintaining the site. I didn't want articles to drag in a different one.

## The problem with hand-rolled HTML

The honest first attempt was just writing each article as its own HTML file. That works for one. It doesn't work for several.

The moment you have more than a couple of articles, you're keeping the same information in sync across four or five places. The title sits in the article's `<h1>`, in the `<title>` tag, in the meta description, in the Open Graph card, in the JSON-LD block, and on a card somewhere on a list page. Change the title and you're now editing six files to keep them consistent. Miss one and the social preview says one thing while the page says another.

The same applies to author bylines, cover images, publish dates, and keyword tags. Each article is a small consistency problem, and the list page is a bigger one. I tried to keep it tidy for a while, then accepted I was going to forget a tag somewhere and ship a broken share preview to LinkedIn.

## Why not a backend

The natural next step is to put a CMS behind it. Ghost, WordPress, a headless CMS plus a static frontend. They all solve the consistency problem. None of them fit a personal site that gets traffic in the low hundreds a week.

A backend means a server to keep running, updates to apply, a database to back up, and an admin login I'd forget the password to. It's a lot of moving parts to host a handful of posts I write a few times a year. The maintenance surface is bigger than the thing being maintained.

A headless CMS gets rid of the server, but it puts my article content behind someone else's login and rate limits. If the service raises its prices or shuts down, the articles are stuck behind an export step. Markdown files in a git repo don't have that problem.

## Why Python, Markdown, and JSON

There are good static site generators that already exist. I looked at them. The reason I didn't use one is that most of them want to own the whole site. They give you a theme system, a routing layer, and a build pipeline, and in exchange you reorganise your project around their conventions. That's a fair trade if you're starting fresh. It's a bad trade if you already have a site you're happy with and you only want to add an `articles/` section to it.

ArtiPress is small on purpose. The article body is Markdown because Markdown is the format I want to write in. The metadata is a separate JSON file because mixing config into frontmatter makes both harder to validate. The output is plain HTML in a folder you commit alongside the rest of your site. The generator is a Python script because Python was already installed on my machine, and because Pillow handles the image conversion without me writing it.

The result drops into an existing repo without asking the rest of the site to change. The header, footer, and styling come from templates I edit directly. The output goes wherever I tell it to. Nothing about the site outside the `articles/` folder is touched.

## What got cut

A surprising amount of the work on ArtiPress was deciding what not to build.

- **No drafts, no scheduled publishing.** A file is either in `content/` or it isn't. Git branches are the draft system.
- **No comments, likes, or any read-time interactivity.** That needs a backend, and a backend is what the whole project is avoiding.
- **No plugin system.** Plugins are a tax you pay forever on a feature you might use once. The templates are editable and the source is small enough to fork. That's the extension story.
- **No live preview server.** Open the generated HTML in a browser. That's the preview.
- **No theme marketplace.** The templates ship as a working example and you edit them. Designing for someone else's site is harder than designing for your own, so I didn't try.

Every one of those is a reasonable feature. None of them are reasonable features for the size of project I wanted to maintain alone. Cutting them is the reason ArtiPress fits in a single folder and reads top to bottom.

## Where it goes from here

ArtiPress does what I needed it to do, which means the bar for adding to it is high. New features have to earn their place by being either things I want for my own site or things that catch real errors before they ship. The validation pass keeps growing in that direction. The template and styling system probably won't.

If that scope sounds like a fit for your site too, the rest of the articles here cover how to use it. If it sounds too small, that's the right reaction, and a heavier tool is probably the right answer for you.
