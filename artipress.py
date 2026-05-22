import json
import os
import re
from datetime import datetime

JSON_CONFIG_FILEPATH = "artipress_data/artipress.config.json"
CONFIG_DEFAULTS = {
    "base_url": "http://artipress.majdij.com",
    "website_title": "ArtiPress",
    "website_logo_url": "https://artipress.majdij.com/resources/images/logo.png",
    "input_articles_folder": "artipress_data/articles",
    "base_template_paths": {},
    "generated_articles_output_path": "articles",
    "recently_published_within_hours": 168,
    "date_format": "{day} %B %Y",
    "time_format": "%H:%M",
}
REQUIRED_JSON_CONFIG_FIELDS = [
    "base_template_paths.article_list",
    "base_template_paths.article_page",
    "base_template_paths.author_page",
    "base_template_paths.author_list",
    "input_articles_folder",
    "generated_articles_output_path",
]

JSON_ARTICLE_FILEPATH = "article.json"
REQUIRED_JSON_ARTICLE_FIELDS = [
    "article_title",
    "author_slugs",
    "article_image_url",
    "article_strap_line",
    "date.published"
]

AUTHOR_JSON_PATH = "artipress_data/authors/authors.json"
SOCIAL_LINKS_JSON_PATH = "artipress_data/authors/social_links.json"
DEFAULT_AUTHOR_PICTURE_URL = "/artipress_data/authors/author_pictures/default.svg"

RESERVED_FOLDERS_IN_ARTICLES_OUTPUT = [
    "authors",
]


CONFIG = {}
AUTHORS = []
SOCIAL_LINKS = {}

def format_display_date(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        date_format = CONFIG.get("date_format", "{day} %B %Y")
        time_format = CONFIG.get("time_format", "%H:%M")
        date_part = dt.strftime(date_format.replace("{day}", str(dt.day)))
        if dt.hour == 0 and dt.minute == 0:
            return date_part
        return f"{date_part} at {dt.strftime(time_format)}"
    except (ValueError, AttributeError):
        return iso_string

def get_nested(data: dict, key: str):
    """
    Retrieve a value from a nested dictionary using a dot-notation key. Returns None if any part of the path is missing.
    
    Args:
        data: The dictionary to traverse.
        key:  The dot-notation key to look up.
    Returns:
        The value at the nested key, or None if any part of the path is missing.
    """
    keys = key.split(".")
    for k in keys:
        if not isinstance(data, dict) or k not in data:
            return None
        data = data[k]
    return data

def validate_json(filepath: str, required_fields: list[str]) -> dict:
    """
    Validate that the JSON file exists, is valid JSON, and contains required fields. Raises FileNotFoundError, ValueError, or KeyError with descriptive messages if validation fails.

    Args:
        filepath:        Path to the JSON file to validate.
        required_fields: List of dot-notation keys that must be present in the JSON.
    Returns:
        The loaded JSON data as a dictionary if validation passes.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file '{filepath}': {e}")

    missing = [f for f in required_fields if get_nested(data, f) is None]
    if missing:
        raise KeyError(f"JSON is missing required fields: {missing}")

    return data

def get_folders(directory: str, ignore: list[str] = []) -> list[str]:
    """
    Returns a list of top-level folder names within a given directory.

    Args:
        directory: Path to the directory to scan.
        ignore:    List of folder names to exclude.
    Returns:
        A list of folder names (not full paths).
    """
    return [
        entry.name
        for entry in os.scandir(directory)
        if entry.is_dir() and entry.name not in ignore
    ]

def get_author_info(author_slug: str, authors: list[dict]) -> dict:
    """
    Retrieves author details from a pre-loaded authors list by their slug.

    Args:
        author_slug: The unique slug identifier for the author (e.g. "john-doe").
        authors:     Pre-loaded list of author dicts (from AUTHORS global).

    Returns:
        A dict containing the author's details, or an empty dict if not found.
    """
    return next(
        (author for author in authors if author.get("author_slug") == author_slug),
        {}
    )

def make_author_meta_tag(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured meta tag.
    meta_tags = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        if meta_tags == "":
            meta_tags += f"<meta name=\"author\" content=\"{author_info.get('author_name', 'Unknown Author')}\" />"
        else:
            meta_tags += f"\n<meta name=\"author\" content=\"{author_info.get('author_name', 'Unknown Author')}\" />"

    return meta_tags

def make_author_og_meta_tag(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured Open Graph meta tag.
    og_meta_tags = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        if og_meta_tags == "":
            og_meta_tags += f"<meta property=\"article:author\" content=\"{CONFIG['base_url']}/articles/authors/{author_slug}\" />"
        else:
            og_meta_tags += f"\n<meta property=\"article:author\" content=\"{CONFIG['base_url']}/articles/authors/{author_slug}\" />"

    return og_meta_tags

def make_author_ld_json(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured application/ld+json script tag.
    authors_ld_json = []
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        author_ld_json = {
            "@type": "Person",
            "name": author_info.get("author_name", "Unknown Author"),
            "url": f"{CONFIG['base_url']}/articles/authors/{author_slug}"
        }
        authors_ld_json.append(author_ld_json)

    return json.dumps(authors_ld_json, indent=4)

def make_author_html_element(article_data: dict) -> str:
    # Get a list of the article's authors' details using `get_author_info` and the `author_slugs` field in `article_data`. Appened to structured html element.
    html_authors_info = ""
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)

        if html_authors_info == "":
            html_authors_info += f"<a href='/articles/authors/{author_slug}'>{author_info.get('author_name', 'Unknown Author')}</a>"
        else:
            html_authors_info += f", <a href='/articles/authors/{author_slug}'>{author_info.get('author_name', 'Unknown Author')}</a>"
    
    return html_authors_info

def make_author_plain_text(article_data: dict) -> str:
    names = []
    for author_slug in article_data["author_slugs"]:
        author_info = get_author_info(author_slug, AUTHORS)
        names.append(author_info.get("author_name", "Unknown Author"))
    return ", ".join(names)

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"No file found at: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when reading: {path}")

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def markdown_to_html(md: str) -> str:
    """
    Convert Markdown to plain HTML (no added styling).

    Supports
    Block elements
      • ATX headings          # H1 ... ###### H6
      • Setext headings       underlined with === or ---
      • Paragraphs
      • Fenced code blocks    ``` or ~~~, with optional language tag
      • Indented code blocks  4 spaces or 1 tab
      • Blockquotes           > (nested >> supported)
      • Unordered lists       - / * / +  (nested, loose/tight)
      • Ordered lists         1. 2. 3.   (nested, respects start number)
      • Task lists            - [x] done  /  - [ ] todo
      • Tables                GFM-style with alignment and escaped pipes
      • Horizontal rules      --- / *** / ___
      • Raw HTML passthrough

    Inline elements
      • Bold                  **text** or __text__
      • Italic                *text* or _text_  (word-boundary aware)
      • Bold + italic         ***text*** or ___text___
      • Strikethrough         ~~text~~
      • Inline code           `code` or ``code``  (HTML-escaped)
      • Links                 [text](url "title")  (unlimited paren nesting)
      • Reference links       [text][id]  +  [id]: url "title"
      • Images                ![alt](url "title")
      • Reference images      ![alt][id]
      • Autolinks             <https://...>  <email@...>
      • Footnotes             [^id]  +  [^id]: definition
      • Hard line breaks      trailing 2 spaces or trailing backslash
      • Escape sequences      backslash before *, _, `, [, etc.

    Known limitations
      • Footnote definitions must be single-line (no indented continuation)
      • Shortcut reference links [text] without [] are not supported
    """

    #  helpers

    def _escape_html(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    #  Phase 1: strip reference-link & footnote definitions

    ref_links = {}        # lower-id -> (url, title)
    footnotes_def = {}    # id -> body text
    footnote_order = []   # ids in order of first use

    def _strip_ref_links(text):
        pat = re.compile(
            r'^[ ]{0,3}\[([^\]]+)\]:\s+<?([^>\s]+)>?'
            r'(?:[ \t]+(?:"([^"]*)"|\'([^\']*)\'|\(([^)]*)\)))?[ \t]*$',
            re.MULTILINE,
        )
        for m in pat.finditer(text):
            key = m.group(1).lower()
            url = m.group(2)
            title = m.group(3) or m.group(4) or m.group(5) or ""
            ref_links[key] = (url, title)
        return pat.sub("", text)

    def _strip_footnote_defs(text):
        pat = re.compile(r'^\[\^([^\]]+)\]:\s+(.*)', re.MULTILINE)
        for m in pat.finditer(text):
            footnotes_def[m.group(1)] = m.group(2).strip()
        return pat.sub("", text)

    md = _strip_ref_links(md)
    md = _strip_footnote_defs(md)
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = md.strip('\n')

    # Phase 2: inline processor

    def process_inline(text):
        """Apply inline Markdown rules and return HTML."""
        placeholders = {}
        _pid = [0]

        def ph(val):
            key = f'\x00{_pid[0]}\x00'
            _pid[0] += 1
            placeholders[key] = val
            return key

        # 1. Escape sequences  \* \_ etc.
        text = re.sub(
            r'\\([\\`*_{}\[\]()#+\-.!|~<>])',
            lambda m: ph(m.group(1)),
            text,
        )

        # 2. Inline code  ``...``  or  `...`  (HTML-escaped)
        def _code(m):
            body = m.group(1) if m.group(1) is not None else m.group(2)
            return ph(f'<code>{_escape_html(body)}</code>')
        text = re.sub(r'``(.+?)``|`(.+?)`', _code, text, flags=re.DOTALL)

        # 3. Autolinks  <https://...>  or  <email@host>
        text = re.sub(
            r'<((?:https?|ftp)://[^>]+)>',
            lambda m: ph(f'<a href="{m.group(1)}">{m.group(1)}</a>'),
            text,
        )
        text = re.sub(
            r'<([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})>',
            lambda m: ph(f'<a href="mailto:{m.group(1)}">{m.group(1)}</a>'),
            text,
        )

        # 4-7. Images and links — unified character-scanning pass.
        #
        #   Using a character scanner (rather than regex) means URLs with
        #   arbitrarily nested parentheses are handled correctly, e.g.
        #   [Rust](https://en.wikipedia.org/wiki/Rust_(programming_language))
        #   or any number of levels deeper.
        #
        #   Images (![) are checked before plain links ([) so that '!['
        #   is never misread as a standalone '['.  Reference-style syntax
        #   [label][id] / ![alt][id] is handled in the same loop.

        def _find_url(pos):
            """Scan from `pos` (just after the opening '('), tracking paren
            depth, and return (url, title, end_pos) or None on failure."""
            depth = 1
            j = pos
            n = len(text)
            while j < n:
                c = text[j]
                if c == '\\' and j + 1 < n:   # skip escaped character
                    j += 2
                    continue
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        inner = text[pos:j].strip()
                        # Optional trailing title:  url "title"  or  url 'title'
                        tm = (re.match(r'^(.*?)\s+"([^"]*)"$', inner, re.DOTALL) or
                              re.match(r"^(.*?)\s+'([^']*)'$", inner, re.DOTALL))
                        if tm:
                            return tm.group(1).strip(), tm.group(2), j + 1
                        return inner, None, j + 1
                j += 1
            return None   # unmatched '(' — not a valid link

        i_scan = 0
        out_parts = []
        while i_scan < len(text):
            is_img = (text[i_scan] == '!' and
                      i_scan + 1 < len(text) and
                      text[i_scan + 1] == '[')
            is_lnk = text[i_scan] == '['

            if not (is_img or is_lnk):
                out_parts.append(text[i_scan])
                i_scan += 1
                continue

            bk_start = i_scan + (2 if is_img else 1)  # position after '['

            # Find the closing ']'
            k = bk_start
            while k < len(text) and text[k] != ']':
                if text[k] == '\\' and k + 1 < len(text):
                    k += 2
                else:
                    k += 1
            if k >= len(text):   # no closing ']' — emit literally
                out_parts.append(text[i_scan])
                i_scan += 1
                continue

            label = text[bk_start:k]
            after = k + 1        # position after ']'
            matched = False

            if after < len(text) and text[after] == '(':
                # Inline  [label](url)  or  ![alt](url)
                res = _find_url(after + 1)
                if res is not None:
                    url, title, end = res
                    t = f' title="{title}"' if title else ''
                    if is_img:
                        out_parts.append(ph(f'<img src="{url}" alt="{label}"{t}>'))
                    else:
                        out_parts.append(ph(f'<a href="{url}"{t}>{label}</a>'))
                    i_scan = end
                    matched = True

            elif after < len(text) and text[after] == '[':
                # Reference  [label][id]  or  ![alt][id]  (empty id → use label)
                m2 = after + 1
                while m2 < len(text) and text[m2] != ']':
                    m2 += 1
                if m2 < len(text):
                    ref_id = (text[after + 1:m2] or label).lower()
                    if ref_id in ref_links:
                        url, title = ref_links[ref_id]
                        t = f' title="{title}"' if title else ''
                        if is_img:
                            out_parts.append(ph(f'<img src="{url}" alt="{label}"{t}>'))
                        else:
                            out_parts.append(ph(f'<a href="{url}"{t}>{label}</a>'))
                        i_scan = m2 + 1
                        matched = True

            if not matched:
                out_parts.append(text[i_scan])
                i_scan += 1

        text = ''.join(out_parts)

        # 8. Footnote references  [^id]
        def _fn_ref(m):
            fn_id = m.group(1)
            if fn_id not in footnote_order:
                footnote_order.append(fn_id)
            n = footnote_order.index(fn_id) + 1
            return ph(f'<sup><a href="#fn-{fn_id}" id="fnref-{fn_id}">[{n}]</a></sup>')
        text = re.sub(r'\[\^([^\]]+)\]', _fn_ref, text)

        # 9. Bold+italic, bold, italic, strikethrough
        #    *  variants — no word-boundary restriction (standard behaviour)
        #    _  variants — word-boundary aware (won't fire inside foo_bar_baz)
        text = re.sub(r'\*{3}(.+?)\*{3}',
                      lambda m: ph(f'<strong><em>{m.group(1)}</em></strong>'), text)
        text = re.sub(r'(?<!\w)_{3}(.+?)_{3}(?!\w)',
                      lambda m: ph(f'<strong><em>{m.group(1)}</em></strong>'), text)
        text = re.sub(r'\*{2}(.+?)\*{2}',
                      lambda m: ph(f'<strong>{m.group(1)}</strong>'), text)
        text = re.sub(r'(?<!\w)_{2}(.+?)_{2}(?!\w)',
                      lambda m: ph(f'<strong>{m.group(1)}</strong>'), text)
        text = re.sub(r'\*(.+?)\*',
                      lambda m: ph(f'<em>{m.group(1)}</em>'), text)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)',
                      lambda m: ph(f'<em>{m.group(1)}</em>'), text)
        text = re.sub(r'~~(.+?)~~',
                      lambda m: ph(f'<del>{m.group(1)}</del>'), text)

        # 10. Hard line breaks: 2+ trailing spaces or trailing backslash
        text = re.sub(r'  +\n', '<br>\n', text)
        text = re.sub(r'\\\n', '<br>\n', text)

        # Restore placeholders
        for key, val in placeholders.items():
            text = text.replace(key, val)

        return text

    # Phase 3: block helpers

    def _indent(line):
        m = re.match(r'^([ \t]*)', line)
        return len(m.group(1).expandtabs(4)) if m else 0

    _HR    = re.compile(r'^[ ]{0,3}((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$')
    _UL    = re.compile(r'^([ \t]*)([-*+])\s+(.*)')
    _OL    = re.compile(r'^([ \t]*)(\d+)\.\s+(.*)')
    _BQ    = re.compile(r'^[ ]{0,3}>')
    _FENCE = re.compile(r'^(`{3,}|~{3,})(.*)')
    _ATX   = re.compile(r'^(#{1,6})[ \t]+(.*?)[ \t]*#*\s*$')
    _PARA_STOP = re.compile(
        r'^(?:#{1,6}[ \t]|[ ]{0,3}>'
        r'|`{3,}|~{3,}'
        r'|[ \t]*(?:[-*+]|\d+\.)\s)'
    )  # HR is checked separately via _HR (which has $ anchor) to avoid
       # falsely matching ***bold*** or ---text as paragraph breaks

    def _parse_table(lines, i):
        if i + 1 >= len(lines):
            return None, i
        sep = lines[i + 1]
        sep_pat = re.compile(
            r'^[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$'
        )
        if not sep_pat.match(sep):
            return None, i
        if '|' not in sep and '|' not in lines[i]:
            return None, i

        _PIPE_PH = '\x01'

        def split_row(row):
            row = row.strip().replace('\\|', _PIPE_PH)
            if row.startswith('|'): row = row[1:]
            if row.endswith('|'):   row = row[:-1]
            return [c.strip().replace(_PIPE_PH, '|') for c in row.split('|')]

        def col_align(s):
            s = s.strip()
            l, r = s.startswith(':'), s.endswith(':')
            if l and r: return 'center'
            if r:       return 'right'
            if l:       return 'left'
            return ''

        headers = split_row(lines[i])
        aligns  = [col_align(s) for s in split_row(sep)]
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and '|' in lines[i]:
            rows.append(split_row(lines[i]))
            i += 1

        def sty(j):
            a = aligns[j] if j < len(aligns) else ''
            return f' style="text-align:{a}"' if a else ''

        ths = ''.join(f'<th{sty(j)}>{process_inline(h)}</th>'
                      for j, h in enumerate(headers))
        trs = ''.join(
            '<tr>' + ''.join(f'<td{sty(j)}>{process_inline(c)}</td>'
                             for j, c in enumerate(row)) + '</tr>'
            for row in rows
        )
        return f'<table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>', i

    def _parse_list(lines, i):
        n = len(lines)
        is_ul    = bool(_UL.match(lines[i]))
        item_re  = _UL if is_ul else _OL
        list_tag = 'ul' if is_ul else 'ol'

        start_num = 1
        if not is_ul:
            m0 = _OL.match(lines[i])
            start_num = int(m0.group(2)) if m0 else 1

        base_ind = _indent(lines[i])
        items = []

        while i < n:
            line = lines[i]
            if not line.strip():
                if items:
                    items[-1]['body'].append(line)
                i += 1
                continue
            m = item_re.match(line)
            curr_ind = _indent(line)
            if m and curr_ind == base_ind:
                content = m.group(3)
                task_m  = re.match(r'^\[([ xX])\]\s+(.*)', content)
                if task_m:
                    task    = task_m.group(1).lower() == 'x'
                    content = task_m.group(2)
                else:
                    task = None
                items.append({'task': task, 'first': content, 'body': []})
                i += 1
            elif curr_ind > base_ind and items:
                items[-1]['body'].append(line)
                i += 1
            else:
                break

        # Loose list if blank lines appear between/within any items
        list_is_loose = any(any(not l.strip() for l in item['body'])
                            for item in items)

        li_parts = []
        for item in items:
            body = item['body']
            while body and not body[-1].strip():
                body.pop()

            checkbox = ''
            if item['task'] is not None:
                chk      = ' checked' if item['task'] else ''
                checkbox = f'<input type="checkbox" disabled{chk}> '

            first_html  = process_inline(item['first'])
            first_block = (f'<p>{checkbox}{first_html}</p>' if list_is_loose
                           else f'{checkbox}{first_html}')

            if body:
                non_empty = [l for l in body if l.strip()]
                min_ind   = min((_indent(l) for l in non_empty), default=0)
                stripped  = [l[min_ind:] if l.strip() else '' for l in body]
                li_content = f'{first_block}\n{_parse_blocks(stripped)}'
            else:
                li_content = first_block

            li_parts.append(f'<li>{li_content}</li>')

        start_attr = f' start="{start_num}"' if (not is_ul and start_num != 1) else ''
        return f'<{list_tag}{start_attr}>{"".join(li_parts)}</{list_tag}>', i

    def _parse_blockquote(lines, i):
        n = len(lines)
        bq_lines = []
        while i < n:
            line = lines[i]
            if _BQ.match(line):
                bq_lines.append(re.sub(r'^[ ]{0,3}>\s?', '', line))
                i += 1
            elif bq_lines and line.strip():
                bq_lines.append(line)
                i += 1
            else:
                break
        return f'<blockquote>\n{_parse_blocks(bq_lines)}\n</blockquote>', i

    def _parse_blocks(lines):
        result = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            if not line.strip():
                i += 1
                continue

            # fenced code block
            fence_m = _FENCE.match(line)
            if fence_m:
                fc   = fence_m.group(1)[0]
                flen = len(fence_m.group(1))
                lang = fence_m.group(2).strip()
                code_lines = []
                i += 1
                while i < n:
                    if re.match(rf'^{re.escape(fc)}{{{flen},}}\s*$', lines[i]):
                        i += 1
                        break
                    code_lines.append(lines[i])
                    i += 1
                lang_attr = f' class="language-{lang}"' if lang else ''
                result.append(
                    f'<pre><code{lang_attr}>{_escape_html(chr(10).join(code_lines))}</code></pre>'
                )
                continue

            # indented code block
            if line.startswith('    ') or line.startswith('\t'):
                code_lines = []
                while i < n and (lines[i].startswith('    ') or
                                 lines[i].startswith('\t') or
                                 not lines[i].strip()):
                    raw = lines[i]
                    if raw.startswith('    '):   code_lines.append(raw[4:])
                    elif raw.startswith('\t'):   code_lines.append(raw[1:])
                    else:                        code_lines.append('')
                    i += 1
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()
                result.append(
                    f'<pre><code>{_escape_html(chr(10).join(code_lines))}</code></pre>'
                )
                continue

            # ATX heading
            atx_m = _ATX.match(line)
            if atx_m:
                lv = len(atx_m.group(1))
                result.append(f'<h{lv}>{process_inline(atx_m.group(2))}</h{lv}>')
                i += 1
                continue

            # setext heading
            if i + 1 < n and line.strip():
                nxt = lines[i + 1]
                if re.match(r'^=+\s*$', nxt):
                    result.append(f'<h1>{process_inline(line)}</h1>')
                    i += 2
                    continue
                if re.match(r'^-+\s*$', nxt) and not _UL.match(line):
                    result.append(f'<h2>{process_inline(line)}</h2>')
                    i += 2
                    continue

            # horizontal rule
            if _HR.match(line):
                result.append('<hr>')
                i += 1
                continue

            # blockquote
            if _BQ.match(line):
                bq_html, i = _parse_blockquote(lines, i)
                result.append(bq_html)
                continue

            # list
            if _UL.match(line) or _OL.match(line):
                lst_html, i = _parse_list(lines, i)
                result.append(lst_html)
                continue

            # table
            if i + 1 < n:
                tbl_html, new_i = _parse_table(lines, i)
                if tbl_html is not None:
                    result.append(tbl_html)
                    i = new_i
                    continue

            # raw HTML block
            if re.match(r'^<(?!(?:https?|ftp)://|[a-zA-Z0-9._%+\-]+@)(?:[a-zA-Z][a-zA-Z0-9-]*(?:\s|>|/>|$)|/[a-zA-Z])', line):
                html_block = []
                while i < n and lines[i].strip():
                    html_block.append(lines[i])
                    i += 1
                result.append('\n'.join(html_block))
                continue

            # paragraph
            para = []
            while i < n and lines[i].strip():
                l = lines[i]
                if _PARA_STOP.match(l) or _HR.match(l):
                    break
                if i + 1 < n and re.match(r'^[=\-]+\s*$', lines[i + 1]):
                    break
                para.append(l)
                i += 1
            if para:
                result.append(f'<p>{process_inline(chr(10).join(para))}</p>')

        return '\n'.join(result)

    # Phase 4: run

    html = _parse_blocks(md.split('\n'))

    # Phase 5: footnotes section

    if footnote_order:
        items_html = '\n'.join(
            f'<li id="fn-{fid}">'
            f'{process_inline(footnotes_def.get(fid, ""))} '
            f'<a href="#fnref-{fid}">&#8617;</a></li>'
            for fid in footnote_order
        )
        html += (f'\n<section class="footnotes"><ol>\n{items_html}\n</ol></section>')

    return html

def render_template(template: str, variables: dict) -> str:
    def replacer(match):
        key = match.group(1).strip()
        if key not in variables:
            raise KeyError(f"Template variable '{key}' not found in provided dictionary")
        return str(variables[key])

    return re.sub(r'\{html_var\((\w+)\)\}', replacer, template)



def validate_article_folders(article_folders):
    validated_articles = []

    for folder in article_folders:
        article_json_path = os.path.join(CONFIG["input_articles_folder"], folder, JSON_ARTICLE_FILEPATH)
        try:
            article_data = validate_json(article_json_path, REQUIRED_JSON_ARTICLE_FIELDS)
            print(f"Validated article: {article_data['article_title']}")
            validated_articles.append((folder, article_data))
        except (FileNotFoundError, ValueError, KeyError) as e:
            raise SystemExit(f"Error in article folder '{folder}': {e}")

    # Order: most-recently-published first; ties broken alphabetically by title.
    # Two passes leverage sort stability — the title order from pass 1 is preserved within each date group in pass 2.
    validated_articles.sort(key=lambda item: (item[1].get("article_title") or "").lower())
    validated_articles.sort(
        key=lambda item: (item[1].get("date") or {}).get("published") or "",
        reverse=True,
    )

    return validated_articles

def startup_checks() -> list[tuple[str, dict]]:
    global AUTHORS, SOCIAL_LINKS

    # Verify all template file paths exist before any generation begins
    all_template_paths = {
        **CONFIG.get("base_template_paths", {}),
        **CONFIG.get("components_template_paths", {}),
    }
    for key, path in all_template_paths.items():
        if path is None or not os.path.exists(path):
            raise SystemExit(f"Template file missing for '{key}': {path}")

    # Load authors.json once
    authors_data = validate_json(AUTHOR_JSON_PATH, [])
    if not isinstance(authors_data, list):
        raise ValueError(f"Expected a JSON array in {AUTHOR_JSON_PATH}, got {type(authors_data).__name__}")
    AUTHORS = authors_data

    # Load social_links.json once
    social_data = validate_json(SOCIAL_LINKS_JSON_PATH, [])
    if not isinstance(social_data, dict):
        raise ValueError(f"Expected a JSON object in {SOCIAL_LINKS_JSON_PATH}, got {type(social_data).__name__}")
    SOCIAL_LINKS = social_data

    # Verify every article folder contains article.md
    article_folders = get_folders(CONFIG["input_articles_folder"])
    missing_md = [
        folder for folder in article_folders
        if not os.path.exists(os.path.join(CONFIG["input_articles_folder"], folder, "article.md"))
    ]
    if missing_md:
        raise SystemExit(f"Missing article.md in folders: {missing_md}")

    return validate_article_folders(article_folders)


def generate_article_page(article_slug: str, article_data: dict, output_path: str):

    article_page_template = read_file(CONFIG["base_template_paths"].get("article_page"))
    article_md_content = read_file(os.path.join(CONFIG["input_articles_folder"], article_slug, "article.md"))

    # Combine the 3 templates components into one article page base template
    base_page_template = render_template(article_page_template, {
        "article_page_head_metadata": read_file(CONFIG["components_template_paths"].get("article_page_head_metadata")),
        "articles_page_styling_and_scripts": read_file(CONFIG["components_template_paths"].get("articles_page_styling_and_scripts")),
        "article_page_head_application_json_ld": read_file(CONFIG["components_template_paths"].get("article_page_head_application_json_ld")),
        "article_page_main_article": read_file(CONFIG["components_template_paths"].get("article_page_main_article")),
    })

    # Construct published date
    ISO_published_date = article_data.get("date", {}).get("published", "")
    published_date_element = format_display_date(ISO_published_date)

    # Construct edited date (if it exists and has a value)
    ISO_edited_date = ""
    edited_date_element = ""
    if article_data.get("date", {}).get("edited") not in (None, ""):
        ISO_edited_date = article_data.get("date", {}).get("edited", "")
        edited_date_element = f' | Edited on {format_display_date(ISO_edited_date)}'

    replacement_vars = {
        "article_title": article_data.get("article_title", "Untitled Article"),
        "website_title": CONFIG["website_title"],
        "generated_articles_output_path": CONFIG["generated_articles_output_path"],
        "base_url": CONFIG["base_url"],
        "article_id": article_slug,
        "article_strap_line": article_data.get("article_strap_line", ""),
        "article_keywords_list": ", ".join(article_data.get("article_keywords", [])),
        "author_meta_tags": make_author_meta_tag(article_data),
        "article_featured_image": article_data.get("article_image_url", ""),
        "article_published_date_iso": ISO_published_date,
        "article_edited_date_iso_iso": ISO_edited_date,
        "og_meta_tags_authors": make_author_og_meta_tag(article_data),
        "json_ld_authors": make_author_ld_json(article_data),
        "article_authors": make_author_html_element(article_data),
        "article_published_date": published_date_element,
        "article_edited_date": edited_date_element,
        "website_logo_url": CONFIG.get("website_logo_url", ""),
        "article_image_url": article_data.get("article_image_url", ""),
        "article_image_alt": article_data.get("article_image_alt", ""),
        "article_html_content": markdown_to_html(article_md_content),
    }

    # Render the final html 
    final_html = render_template(base_page_template, replacement_vars)

    # Save the rendered template to the output path
    write_file(output_path, final_html)

    pass

def generate_article_print(article_slug: str, article_data: dict, output_path: str):

    article_print_template = read_file(CONFIG["base_template_paths"].get("article_print"))
    article_md_content = read_file(os.path.join(CONFIG["input_articles_folder"], article_slug, "article.md"))

    ISO_published_date = article_data.get("date", {}).get("published", "")

    edited_date_text = ""
    if article_data.get("date", {}).get("edited") not in (None, ""):
        edited_date_text = f' | Edited on {format_display_date(article_data["date"]["edited"])}'

    replacement_vars = {
        "article_title": article_data.get("article_title", "Untitled Article"),
        "website_title": CONFIG["website_title"],
        "generated_articles_output_path": CONFIG["generated_articles_output_path"],
        "base_url": CONFIG["base_url"],
        "article_id": article_slug,
        "article_strap_line": article_data.get("article_strap_line", ""),
        "article_authors": make_author_plain_text(article_data),
        "article_published_date": format_display_date(ISO_published_date),
        "article_edited_date": edited_date_text,
        "article_edited_date_iso": edited_date_text,
        "article_image_url": article_data.get("article_image_url", ""),
        "article_image_alt": article_data.get("article_image_alt", ""),
        "article_html_content": markdown_to_html(article_md_content),
    }

    # Pass 1: inject component content and resolve top-level template variables
    base_print_template = render_template(article_print_template, {
        **replacement_vars,
        "articles_page_styling_and_scripts": read_file(CONFIG["components_template_paths"].get("articles_page_styling_and_scripts")),
        "article_page_main_article": read_file(CONFIG["components_template_paths"].get("article_page_main_article")),
    })

    # Pass 2: resolve variables inside injected component content
    final_html = render_template(base_print_template, replacement_vars)

    write_file(output_path, final_html)

    pass

def generate_all_article_pages(validated_articles: list[tuple[str, dict]]):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["generated_articles_output_path"], folder, "index.html")
        generate_article_page(folder, article_data, output_path)

def generate_all_article_prints(validated_articles: list[tuple[str, dict]]):
    for folder, article_data in validated_articles:
        output_path = os.path.join(CONFIG["generated_articles_output_path"], folder, "print.html")
        generate_article_print(folder, article_data, output_path)

def render_article_list_items_html(validated_articles, article_list_item_template):
    """
    Render the grid of article cards used on both the article list page and individual author pages.

    Args:
        validated_articles: list of (folder, article_data) tuples.
        article_list_item_template: raw template string for a single card.
    Returns:
        HTML string wrapping the cards in an .artipress-articles-container div.
    """
    article_list_items_html = f"<div class=\"artipress-articles-container\" data-recently-published-hours=\"{CONFIG.get('recently_published_within_hours', 0)}\">\n"

    for folder, article_data in validated_articles:

        if article_data.get("hide_from_article_list", False):
            continue

        article_labels = ""
        #  Check to see if there are any labels for the article
        if article_data.get("article_labels"):
            article_labels += "<p class=\"artipress-article-card-labels\">"

            for label in article_data.get("article_labels", []):
                article_labels += f"<span class=\"artipress-article-card-label\">{label}</span>"
            
            article_labels += "</p>"
        
        else:
            # If there are no labels, just place an epty div that will be used for spacing
            article_labels = "<div class=\"artipress-article-card-labels-empty\"></div>"

        article_authors = ""
        for author_slug in article_data["author_slugs"]:
            author_info = get_author_info(author_slug, AUTHORS)
            if article_authors != "":
                article_authors += ", "
            article_authors += author_info.get('author_name', 'Unknown Author')

        article_list_items_html += ("\n" + render_template(article_list_item_template, {
            "article_title": article_data.get("article_title", "Untitled Article"),
            "article_strap_line": article_data.get("article_strap_line", ""),
            "article_labels": article_labels,
            "article_authors": article_authors,
            "article_published_date": format_display_date(article_data.get("date", {}).get("published", "")),
            "article_published_date_iso": article_data.get("date", {}).get("published", ""),
            "article_image_url": article_data.get("article_image_url", ""),
            "article_image_alt": article_data.get("article_image_alt", ""),
            "article_url": f"/{CONFIG['generated_articles_output_path']}/{folder}/index.html",
        }))

    article_list_items_html += "\n</div>"
    return article_list_items_html

def generate_article_list_page(validated_articles: list[tuple[str, dict]]):

    article_list_template = read_file(CONFIG["base_template_paths"].get("article_list"))
    article_list_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("article_list_styling_and_scripts"))
    article_list_item_template = read_file(CONFIG["components_template_paths"].get("article_list_item"))

    output_path = os.path.join(CONFIG["generated_articles_output_path"], "index.html")

    article_list_items_html = render_article_list_items_html(validated_articles, article_list_item_template)

    final_html = render_template(article_list_template, {
        "article_list_styling_and_scripts": article_list_styling_and_scripts,
        "article_list_items": article_list_items_html,
        "base_url": CONFIG["base_url"],
    })

    write_file(output_path, final_html)

def generate_author_list_page():

    author_list_template = read_file(CONFIG["base_template_paths"].get("author_list"))
    author_list_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("author_list_styling_and_scripts"))
    author_list_item_template = read_file(CONFIG["components_template_paths"].get("author_list_item"))

    output_path = os.path.join(CONFIG["generated_articles_output_path"], "authors", "index.html")

    author_list_items_html = "<div class=\"artipress-authors-container\">\n"

    # For each author, render an author list item using `author_list_item_template` and the author's data
    for author in AUTHORS:
        author_slug = author.get("author_slug", "")

        # Skip the role element entirely when the author has no role set
        author_role = (author.get("author_role") or "").strip()
        author_role_formatted = (
            f'<p class="artipress-author-card-role">{author_role}</p>'
            if author_role else ""
        )

        # Fall back to the default avatar when an author has no picture
        author_picture_url = (author.get("author_picture_url") or "").strip() or DEFAULT_AUTHOR_PICTURE_URL

        author_list_items_html += ("\n" + render_template(author_list_item_template, {
            "author_name": author.get("author_name", "Unknown Author"),
            "author_role_formatted": author_role_formatted,
            "author_picture_url": author_picture_url,
            "author_url": f"/{CONFIG['generated_articles_output_path']}/authors/{author_slug}/index.html",
        }))

    author_list_items_html += "\n</div>"

    # Render the author list template with the generated author list items
    final_html = render_template(author_list_template, {
        "author_list_styling_and_scripts": author_list_styling_and_scripts,
        "author_list_items": author_list_items_html,
        "base_url": CONFIG["base_url"],
    })

    # Save the rendered template to the output path
    write_file(output_path, final_html)

def render_author_social_links_html(social_links, social_link_template, social_links_registry):
    """
    Render a <ul> of social link icons for an author. Returns "" if the author has no usable links.
    Skips + warns when a platform is missing from the registry or its icon file is missing.
    """
    if not social_links:
        return ""

    items_html = ""
    for platform_key, data in social_links.items():
        if platform_key not in social_links_registry:
            print(f"Warning: social platform '{platform_key}' not found in social_links.json — skipping")
            continue

        registry_entry = social_links_registry[platform_key]
        icon_path = registry_entry.get("icon", "")
        local_icon_path = icon_path.lstrip("/")
        if not icon_path or not os.path.exists(local_icon_path):
            print(f"Warning: icon file '{local_icon_path}' missing for platform '{platform_key}' — skipping")
            continue

        platform_name = registry_entry.get("name", platform_key)
        handle = (data.get("handle") or "").strip()
        link = (data.get("link") or "").strip()
        if not link:
            continue

        aria_label = f"{platform_name}: {handle}" if handle else platform_name

        items_html += "\n" + render_template(social_link_template, {
            "social_link_url": link,
            "social_link_icon_url": icon_path,
            "social_link_aria_label": aria_label,
            "social_link_title": aria_label,
        })

    if not items_html:
        return ""

    return f'<ul class="social-links">{items_html}\n</ul>'

def generate_author_page(author_data: dict, validated_articles: list[tuple[str, dict]], social_links_registry: dict):
    author_slug = author_data.get("author_slug", "")
    author_name = author_data.get("author_name", "Unknown Author")

    author_page_template = read_file(CONFIG["base_template_paths"].get("author_page"))
    author_page_styling_and_scripts = read_file(CONFIG["components_template_paths"].get("author_page_styling_and_scripts"))
    article_list_item_template = read_file(CONFIG["components_template_paths"].get("article_list_item"))
    social_link_template = read_file(CONFIG["components_template_paths"].get("author_social_link"))

    # Filter to articles this author wrote or co-wrote
    author_articles = [
        (folder, article_data) for folder, article_data in validated_articles
        if author_slug in article_data.get("author_slugs", [])
    ]

    if author_articles:
        author_articles_list_items = render_article_list_items_html(author_articles, article_list_item_template)
    else:
        author_articles_list_items = "<p>No articles yet.</p>"

    # Role -- omit the <p> entirely when empty
    author_role = (author_data.get("author_role") or "").strip()
    author_role_formatted = (
        f'<p class="author-role">{author_role}</p>'
        if author_role else ""
    )

    # Bio -- raw kept for meta description, markdown rendered for the page body
    author_bio = author_data.get("author_bio", "")
    author_bio_html = markdown_to_html(author_bio) if author_bio else ""

    # Picture -- fall back to default if missing
    author_picture_url = (author_data.get("author_picture_url") or "").strip() or DEFAULT_AUTHOR_PICTURE_URL

    # Social links -- empty string if author has none / all skipped
    author_social_links_formatted = render_author_social_links_html(
        author_data.get("social_links", {}),
        social_link_template,
        social_links_registry,
    )

    replacement_vars = {
        "website_title": CONFIG["website_title"],
        "base_url": CONFIG["base_url"],
        "author_name": author_name,
        "author_slug": author_slug,
        "author_bio": author_bio,
        "author_picture_url": author_picture_url,
        "author_page_styling_and_scripts": author_page_styling_and_scripts,
        "author_role_formatted": author_role_formatted,
        "author_bio_html": author_bio_html,
        "author_social_links_formatted": author_social_links_formatted,
        "author_articles_list_items": author_articles_list_items,
    }

    final_html = render_template(author_page_template, replacement_vars)

    output_path = os.path.join(CONFIG["generated_articles_output_path"], "authors", author_slug, "index.html")
    write_file(output_path, final_html)

def generate_all_author_pages(validated_articles: list[tuple[str, dict]]):
    for author in AUTHORS:
        generate_author_page(author, validated_articles, SOCIAL_LINKS)
        print(f"Generated author page: {author.get('author_name', 'Unknown Author')}")

def main():
    global CONFIG, AUTHORS, SOCIAL_LINKS

    config_data = validate_json(JSON_CONFIG_FILEPATH, REQUIRED_JSON_CONFIG_FIELDS)
    CONFIG = {**CONFIG_DEFAULTS, **config_data}

    validated_articles = startup_checks()

    generate_all_article_pages(validated_articles)
    generate_all_article_prints(validated_articles)
    generate_article_list_page(validated_articles)
    generate_author_list_page()
    generate_all_author_pages(validated_articles)



if __name__ == "__main__":
    main()