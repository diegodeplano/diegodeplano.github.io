"""Add a new paper to Publications.html.

Usage: python add_paper.py

The paper is inserted at the top of its category (newest first) with the next
two-digit number, e.g. [J17]. Titles can be typed in normal case: the page CSS
displays them in capitals. Upload the PDFs to files/ and the logo to images/
before running, so the script can check that the links will work.

When the paper has a link (DOI, IEEE Xplore, publisher page or arXiv), its BibTeX
entry is downloaded from Crossref or arXiv and shown behind a "BibTeX" button.
"""
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, unquote, urlencode

SITE = Path(__file__).resolve().parent
PUB_FILE = SITE / 'Publications.html'

# Words kept capitalised in BibTeX titles: styles that lowercase titles would otherwise print
# e.g. "lyapunov". Acronyms such as "BESS" are protected automatically.
PROPER_NOUNS = {'Perron', 'Frobenius', 'Fiedler', 'Laplacian', 'Lyapunov', 'Krasnoselskij', 'Sardinian', 'Carasau'}
# Skipped when the citation key takes the first word of the title, e.g. deplano2025convergence.
STOPWORDS = {'a', 'an', 'the', 'on', 'of', 'for', 'in', 'with', 'via', 'to', 'and', 'by', 'at', 'from',
             'under', 'over', 'into', 'within'}
# Combining accents (after Unicode decomposition) and special letters, as LaTeX commands.
ACCENTS = {'́': "'", '̀': '`', '̈': '"', '̂': '^', '̃': '~', '̄': '=',
           '̧': 'c ', '̌': 'v ', '̆': 'u ', '̊': 'r '}
SPECIAL = {'ø': r'{\o}', 'ß': r'{\ss}', 'æ': r'{\ae}', 'ł': r'{\l}'}

# prefix, id of the category banner section in Publications.html
CATEGORIES = {
    'a': ('A', 'section-category-arxiv'),
    'j': ('J', 'section-category-j'),
    'c': ('C', 'section-category-c'),
}


def full_url(link):
    """Accept 'ieeexplore.ieee.org/...' as well as full URLs."""
    link = link.strip()
    if link and not re.match(r'https?://', link):
        link = 'https://' + link
    return link


def file_href(filename):
    return 'files/' + quote(filename)


def fetch(url, as_json=True):
    req = urllib.request.Request(url, headers={'User-Agent': 'deplano-website-add-paper/1.0'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
            return json.loads(data) if as_json else data
        except urllib.error.HTTPError as e:  # rate limited (429) or busy server: wait and retry
            if e.code not in (429, 503) or attempt == 4:
                raise
            retry_after = e.headers.get('Retry-After', '')
            time.sleep(int(retry_after) if retry_after.isdigit() else 2 ** (attempt + 1))


def latex(text):
    """Plain text (possibly with HTML tags/entities) -> BibTeX-safe text."""
    text = html.unescape(re.sub(r'<[^>]+>', '', text))
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace('&', r'\&').replace('%', r'\%').replace('—', '---').replace('–', '--')
    out = []
    for ch in unicodedata.normalize('NFD', text):
        if ch in ACCENTS and out:
            out[-1] = '{\\' + ACCENTS[ch] + out[-1] + '}'
        else:
            out.append(SPECIAL.get(ch, ch))
    return ''.join(out)


def protect(title):
    """Brace acronyms and PROPER_NOUNS so that BibTeX styles keep their capitals."""
    def brace(m):
        word = m.group(0)
        return '{' + word + '}' if word in PROPER_NOUNS or re.fullmatch(r'[A-Z][A-Z0-9]+s?', word) else word
    return re.sub(r'(?<![\\A-Za-z])[A-Za-z][A-Za-z0-9]*', brace, title)


def ascii_letters(text):
    return re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


def make_key(family, year, title, taken):
    """Google Scholar-style key, e.g. ledda2025certification; the next title words are tried if taken."""
    words = [ascii_letters(w) for w in html.unescape(re.sub(r'<[^>]+>', '', title)).split()
             if w.lower() not in STOPWORDS]
    words = [w for w in words if w] or ['paper']
    base = ascii_letters(family) + str(year)
    for word in words + [words[0] + c for c in 'bcdefgh']:
        if base + word not in taken:
            return base + word
    raise ValueError('no free citation key for ' + base)


def format_bibtex(kind, key, fields):
    """fields: list of (name, value); empty values are dropped and the '=' signs aligned."""
    fields = [(name, value) for name, value in fields if value]
    width = max(len(name) for name, _ in fields)
    body = ',\n'.join(f'  {name.ljust(width)} = {{{value}}}' for name, value in fields)
    return f'@{kind}{{{key},\n{body}\n}}'


def bib_field(bibtex, name):
    m = re.search(rf'^\s*{name}\s*=\s*\{{(.*)\}},?\s*$', bibtex, re.MULTILINE)
    return m.group(1) if m else None


def canonical_doi(doi):
    """IEEE and EUCA DOIs are written in capitals, e.g. 10.1109/TAC.2025.3621993."""
    prefix, suffix = doi.split('/', 1)
    return f'{prefix}/{suffix.upper()}' if prefix in ('10.1109', '10.23919') else doi


def simplify(title):
    return re.sub(r'[^a-z0-9]', '', html.unescape(re.sub(r'<[^>]+>', '', title)).lower())


def find_doi(url, title, first_author):
    """DOI contained in the link, otherwise the Crossref record whose title matches."""
    m = re.search(r'(10\.\d{4,9}/[^\s"?#]+)', unquote(url))
    if m:
        return m.group(1)
    query = urlencode({'query.bibliographic': title, 'query.author': first_author, 'rows': 5, 'select': 'DOI,title'})
    items = fetch('https://api.crossref.org/works?' + query)['message']['items']
    score = lambda item: SequenceMatcher(None, simplify((item.get('title') or [''])[0]), simplify(title)).ratio()
    best = max(items, key=score, default=None)
    return best['DOI'] if best and score(best) > 0.9 else None


def bibtex_from_crossref(doi, taken):
    m = fetch('https://api.crossref.org/works/' + quote(doi))['message']
    year = (m.get('published-print') or m['issued'])['date-parts'][0][0]
    authors = m.get('author', [])
    containers = m.get('container-title') or ['']
    page = m.get('page') or m.get('article-number') or ''
    if page == '1-1':  # placeholder left in some IEEE early-access records
        page = ''
    names = [latex(f"{a['family']}, {a['given']}" if a.get('given') else a.get('family', a.get('name', '')))
             for a in authors]
    fields = [('author', ' and '.join(names)), ('title', protect(latex(m['title'][0])))]
    if m['type'] == 'journal-article':
        kind = 'article'
        fields.append(('journal', latex(containers[0])))
    elif m['type'] in ('proceedings-article', 'book-chapter'):
        kind = 'inproceedings'
        fields.append(('booktitle', latex(containers[-1])))
        if m['type'] == 'book-chapter':  # e.g. workshop proceedings in a Springer series
            fields += [('series', latex(containers[0]) if len(containers) > 1 else ''),
                       ('publisher', latex(m.get('publisher', '')))]
    else:
        kind = 'misc'
    fields += [('volume', m.get('volume')), ('number', m.get('issue')), ('pages', page.replace('-', '--')),
               ('year', str(year)), ('doi', canonical_doi(m['DOI']))]
    family = authors[0].get('family', authors[0].get('name', '')) if authors else 'anonymous'
    return format_bibtex(kind, make_key(family, year, m['title'][0], taken), fields)


def bibtex_from_arxiv(arxiv_id, taken):
    text = fetch('https://arxiv.org/bibtex/' + arxiv_id, as_json=False)
    raw = dict(re.findall(r'(\w+)\s*=\s*\{(.*?)\},?\s*$', text, re.MULTILINE))
    names = [n.strip() for n in raw['author'].split(' and ')]
    # "Diego Deplano" -> "Deplano, Diego"; longer names are left as BibTeX parses them anyway
    names = [', '.join(reversed(n.split())) if len(n.split()) == 2 else n for n in names]
    family = names[0].split(',')[0] if ',' in names[0] else names[0].split()[-1]
    fields = [('author', ' and '.join(latex(n) for n in names)), ('title', protect(latex(raw['title']))),
              ('year', raw['year']), ('eprint', raw.get('eprint', arxiv_id)), ('archivePrefix', 'arXiv'),
              ('primaryClass', raw.get('primaryClass'))]
    return format_bibtex('misc', make_key(family, raw['year'], raw['title'], taken), fields)


def fetch_bibtex(url, title, authors, existing):
    """BibTeX entry of a published paper (None if not found). existing: entries already on the page;
    a paper listed twice (e.g. L-CSS paper and CDC talk) reuses its entry, other keys stay unique."""
    arxiv = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', url)
    if arxiv:
        same = [b for b in existing if bib_field(b, 'eprint') == arxiv.group(1)]
        return same[0] if same else bibtex_from_arxiv(arxiv.group(1), taken_keys(existing))
    first_author = authors.split(',')[0].split('.')[-1].strip()
    doi = find_doi(url, title, first_author)
    if not doi:
        return None
    same = [b for b in existing if (bib_field(b, 'doi') or '').lower() == doi.lower()]
    return same[0] if same else bibtex_from_crossref(doi, taken_keys(existing))


def taken_keys(existing):
    return {re.match(r'@\w+\{([^,]+),', b).group(1) for b in existing}


def page_bibtex(content):
    """BibTeX entries already stored in Publications.html."""
    return [html.unescape(b) for b in re.findall(r'<template class="bib">(.*?)</template>', content, re.DOTALL)]


def render_bibtex(bibtex):
    """Hidden entry read by the BibTeX button (site.js)."""
    return f'\n        <template class="bib">{html.escape(bibtex, quote=False)}</template>' if bibtex else ''


def render_materials(materials, bibtex=False):
    """materials: list of (label, href, is_file), e.g. ('Slides', 'files/X.pdf', True).
    With bibtex, a BibTeX button comes first."""
    if not materials and not bibtex:
        return ''
    links = ''.join(
        f'<a href="{html.escape(href)}" target="_blank">{label}</a>' for label, href, _ in materials)
    button = '<button type="button" class="bib-btn">BibTeX</button>' if bibtex else ''
    return f'<br><span class="mat">{button}{links}</span>'


def render_authors(authors):
    return html.escape(authors).replace('D. Deplano', '<span class="me">D. Deplano</span>')


def render_xref(note, label):
    """Cross-reference to another entry, e.g. an L-CSS paper also listed as CDC talk."""
    return f' &ndash; {html.escape(note)}, see&nbsp;<a class="xref" href="#section-{label}">[{label}]</a>'


def render_paper(label, title, url, authors, venue, materials, logo, logo_alt, logo_href=None, xref=None,
                 bibtex=None):
    """HTML for one publication followed by its divider line. label is e.g. 'J11'.

    url can be None for accepted papers without a DOI yet: the title is then shown without a link.
    """
    title_html = f'<a href="{html.escape(url)}" target="_blank">{html.escape(title)}</a>' if url else html.escape(title)
    img = f'<img src="images/{logo}" alt="{html.escape(logo_alt)}" loading="lazy">'
    logo_html = f'<a href="{html.escape(logo_href)}" target="_blank">{img}</a>' if logo_href else img
    venue_html = html.escape(venue) + (render_xref(*xref) if xref else '')
    return f'''    <article class="pub container" id="section-{label}">
      <div class="pub-label">[{label}]</div>
      <div class="pub-body">
        <h3 class="pub-title">{title_html}</h3>
        <p class="pub-info">{render_authors(authors)}<br>{venue_html}{render_materials(materials, bool(bibtex))}</p>{render_bibtex(bibtex)}
      </div>
      <div class="pub-logo">{logo_html}</div>
    </article>
    <hr class="pub-sep container">
'''


def ordinal(n):
    suffix = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suffix}'


def ask(prompt):
    return input(prompt).strip()


def ask_yes(prompt):
    return ask(prompt + ' (y/n): ').lower().startswith('y')


def add_paper():
    print("Add a paper to Diego Deplano's website.")
    kind = ask('Is this a (j)ournal paper, (c)onference paper, or (a)rxiv preprint? ').lower()[:1]
    if kind not in CATEGORIES:
        print('Invalid type. Exiting.')
        return
    prefix, category_id = CATEGORIES[kind]

    title = ask('Paper title: ')
    authors = ask('Authors (e.g., D. Deplano, M. Franceschelli): ')
    if kind == 'j':
        journal = ask('Journal name (e.g., IEEE Transactions on Automatic Control): ')
        venue = f"{journal}, {ask('Year (and volume/pages if known): ')}"
        url = full_url(ask('DOI or IEEE Xplore link (blank if not yet available): '))
        logo_href = full_url(ask('Journal homepage URL (logo link): '))
        logo_alt = journal
        logo = ask('Logo filename in images/ (e.g., tacon.jpg): ')
    elif kind == 'a':
        journal = ask('Submitted to (journal/conference name): ')
        round_num = ask('Review round number (1, 2, 3, ...) or blank if new: ')
        year = ask('Year: ')
        venue = (f'Under review at {journal} ({ordinal(int(round_num))} round), {year}' if round_num
                 else f'Under review at {journal}, {year}')
        url = full_url(ask('arXiv link: '))
        logo_href, logo_alt, logo = 'https://arxiv.org', 'arXiv', 'ARXIV.jpg'
    else:
        conference = ask('Conference full name (e.g., 66th IEEE Conference on Decision and Control (CDC)): ')
        venue = f"{conference}, {ask('Year (and pages if known): ')}"
        url = full_url(ask('IEEE Xplore (or publisher) link (blank if not yet available): '))
        logo_href = full_url(ask('Conference homepage URL (logo link, blank for none): '))
        logo_alt = ask('Short conference name for the logo (e.g., IEEE CDC 2027): ')
        logo = ask('Logo filename in images/ (e.g., CDC27.jpg): ')

    file_base = ask('Base filename of the PDFs (e.g., "CDC27 - NN" for "CDC27 - NN - Manuscript.pdf"): ')
    materials = [('Manuscript', f'{file_base} - Manuscript.pdf')]
    if ask_yes('Do you have slides?'):
        materials.append(('Slides', f'{file_base} - Slides.pdf'))
    if ask_yes('Do you have a poster?'):
        materials.append(('Poster', f'{file_base} - Poster.pdf'))
    for _, filename in materials:
        if not (SITE / 'files' / filename).exists():
            print(f'  Warning: files/{filename} does not exist yet; upload it before publishing.')
    if not (SITE / 'images' / logo).exists():
        print(f'  Warning: images/{logo} does not exist yet.')
    links = [(label, file_href(filename), True) for label, filename in materials]
    if ask_yes('Do you have a video link?'):
        links.append(('Video', full_url(ask('Video link (e.g., https://youtu.be/...): ')), False))

    content = PUB_FILE.read_text(encoding='utf-8')
    header = re.search(rf'<section[^>]*id="{category_id}"[^>]*>.*?</section>\n?', content, re.DOTALL)
    if not header:
        print(f'Category banner id="{category_id}" not found in Publications.html. Exiting.')
        return
    numbers = [int(n) for n in re.findall(rf'\[{prefix}(\d+)\]', content)]
    label = f'{prefix}{max(numbers, default=0) + 1:02d}'

    bibtex = None
    if url:
        print('Downloading the BibTeX entry...')
        try:
            bibtex = fetch_bibtex(url, title, authors, page_bibtex(content))
        except Exception as e:  # network error or unexpected metadata: the paper is added anyway
            print(f'  Could not download the BibTeX entry ({e}).')
        if bibtex:
            print('\n' + bibtex + '\n')
            if not ask_yes('Add the BibTeX button with this entry?'):
                bibtex = None
        else:
            print('  No BibTeX entry found for this link: the paper is added without the BibTeX button.')

    entry = render_paper(label, title, url or None, authors, venue, links, logo, logo_alt, logo_href or None,
                         bibtex=bibtex)
    PUB_FILE.write_text(content[:header.end()] + entry + content[header.end():], encoding='utf-8')

    print(f'Paper added as [{label}].')
    print('Remember: update the "Last update" footer and add the new PDFs to sitemap.xml.')


if __name__ == '__main__':
    add_paper()
