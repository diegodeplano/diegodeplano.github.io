"""Add a new paper to Publications.html.

Usage: python add_paper.py

The paper is inserted at the top of its category (newest first) with the next
two-digit number, e.g. [J17]. Titles can be typed in normal case: the page CSS
displays them in capitals. Upload the PDFs to files/ and the logo to images/
before running, so the script can check that the links will work.
"""
import html
import re
from pathlib import Path
from urllib.parse import quote

SITE = Path(__file__).resolve().parent
PUB_FILE = SITE / 'Publications.html'

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


def render_materials(materials):
    """materials: list of (label, href, is_file), e.g. ('Slides', 'files/X.pdf', True)."""
    if not materials:
        return ''
    links = '<span class="sep">-</span>'.join(
        f'<a href="{html.escape(href)}" target="_blank">{label}</a>' for label, href, _ in materials)
    return f'<br><span class="mat">Material links: {links}</span>'


def render_authors(authors):
    return html.escape(authors).replace('D. Deplano', '<span class="me">D. Deplano</span>')


def render_xref(note, label):
    """Cross-reference to another entry, e.g. an L-CSS paper also listed as CDC talk."""
    return f' &ndash; {html.escape(note)}, see&nbsp;<a class="xref" href="#section-{label}">[{label}]</a>'


def render_paper(label, title, url, authors, venue, materials, logo, logo_alt, logo_href=None, xref=None):
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
        <p class="pub-info">{render_authors(authors)}<br>{venue_html}{render_materials(materials)}</p>
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

    entry = render_paper(label, title, url or None, authors, venue, links, logo, logo_alt, logo_href or None)
    PUB_FILE.write_text(content[:header.end()] + entry + content[header.end():], encoding='utf-8')

    print(f'Paper added as [{label}].')
    print('Remember: update the "Last update" footer and add the new PDFs to sitemap.xml.')


if __name__ == '__main__':
    add_paper()
