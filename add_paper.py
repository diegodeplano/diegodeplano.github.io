"""Add a new paper to Publications.html.

Usage: python add_paper.py

The paper is inserted at the top of its category (newest first) with the next
two-digit number, e.g. [J12]. Titles can be typed in normal case: the page CSS
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

LINK_CLASS = ('u-active-none u-border-none u-btn u-button-link u-button-style u-hover-none '
              'u-none u-text-black u-text-hover-palette-2-base')
SEPARATOR = ' &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; '


def full_url(link):
    """Accept 'ieeexplore.ieee.org/...' as well as full URLs."""
    link = link.strip()
    if link and not re.match(r'https?://', link):
        link = 'https://' + link
    return link


def file_href(filename):
    return 'files/' + quote(filename)


def material_link(label, href, is_file):
    file_class = ' u-file-link' if is_file else ''
    return (f'<a href="{html.escape(href)}" class="{LINK_CLASS}{file_class} u-btn-2" '
            f'target="_blank">{label}</a>')


def render_materials(materials):
    """materials: list of (label, href, is_file), e.g. ('Slides', 'files/X.pdf', True)."""
    links = [material_link(*m) for m in materials]
    if not links:
        return ''
    rest = ''.join(f'<span style="font-style: italic;">{SEPARATOR}{link}</span>' for link in links[1:])
    return f'<br>Material links:&nbsp; &nbsp; &nbsp; {links[0]}{rest}'


def render_authors(authors):
    return html.escape(authors).replace(
        'D. Deplano', '<span style="text-decoration: underline !important;">D. Deplano</span>')


def render_xref(note, label):
    """Cross-reference to another entry, e.g. an L-CSS paper also listed as CDC talk."""
    return (f' &nbsp;&ndash;&nbsp; {html.escape(note)}, see&nbsp;'
            f'<a class="pub-xref" href="#section-{label}">[{label}]</a>')


def render_paper(label, title, url, authors, venue, materials, logo, logo_alt, logo_href=None, xref=None):
    """HTML for one publication followed by its divider line. label is e.g. 'J11'.

    url can be None for accepted papers without a DOI yet: the title is then shown without a link.
    """
    logo_link = f' data-href="{html.escape(logo_href)}" data-target="_blank"' if logo_href else ''
    venue_html = html.escape(venue) + (render_xref(*xref) if xref else '')
    title_html = (f'<a href="{html.escape(url)}" class="{LINK_CLASS} u-btn-1" target="_blank">{html.escape(title)}</a>'
                  if url else html.escape(title))
    return f'''    <section class="u-clearfix u-section-paper" id="section-{label}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="data-layout-selected u-clearfix u-expanded-width u-layout-custom-sm u-layout-custom-xs u-layout-wrap u-layout-wrap-1">
          <div class="u-layout">
            <div class="u-layout-row">
              <div class="u-container-style u-layout-cell u-size-1-sm u-size-1-xs u-size-10-lg u-size-10-md u-size-10-xl u-layout-cell-1">
                <div class="u-container-layout u-container-layout-1">
                  <img class="u-hidden-sm u-hidden-xs u-image u-image-default u-preserve-proportions u-image-1" src="images/{logo}" alt="{html.escape(logo_alt)}" data-image-width="560" data-image-height="310"{logo_link}>
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-47-lg u-size-47-md u-size-47-xl u-size-52-xs u-size-54-sm u-layout-cell-2">
                <div class="u-container-layout u-container-layout-2">
                  <p class="u-custom-font u-font-oswald u-text u-text-default u-text-1">
                    {title_html}
                  </p>
                  <p class="u-text u-text-2">{render_authors(authors)}<br>{venue_html}{render_materials(materials)}
                  </p>
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-3-lg u-size-3-md u-size-3-xl u-size-5-sm u-size-7-xs u-layout-cell-3">
                <div class="u-container-layout u-valign-top u-container-layout-3">
                  <p class="u-align-center u-custom-font u-font-oswald u-text u-text-default u-text-3">[{label}]</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="u-clearfix u-section-line" id="section-line-{label}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="u-align-center u-border-3 u-border-palette-2-base u-line u-line-horizontal u-line-1"></div>
      </div>
    </section>
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
        venue = f"{journal}, {ask('Year: ')}"
        url = full_url(ask('DOI or IEEE Xplore link: '))
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
        conference = ask('Conference full name (e.g., 64th IEEE Conference on Decision and Control (CDC)): ')
        venue = f"{conference}, {ask('Year: ')}"
        url = full_url(ask('IEEE Xplore (or publisher) link: '))
        logo_href = full_url(ask('Conference homepage URL (logo link, blank for none): '))
        logo_alt = ask('Short conference name for the logo (e.g., IEEE CDC 2025): ')
        logo = ask('Logo filename in images/ (e.g., CDC25.jpg): ')

    file_base = ask('Base filename of the PDFs (e.g., "CDC25 - NN" for "CDC25 - NN - Manuscript.pdf"): ')
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

    entry = render_paper(label, title, url, authors, venue, links, logo, logo_alt, logo_href or None)
    PUB_FILE.write_text(content[:header.end()] + entry + content[header.end():], encoding='utf-8')

    print(f'Paper added as [{label}].')
    print('Remember: update the "Last update" footer and add the new PDFs to sitemap.xml.')


if __name__ == '__main__':
    add_paper()
