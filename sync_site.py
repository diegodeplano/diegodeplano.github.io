"""Refresh generated homepage publications and asset versions.

Publications.html is the source for titles, authors, links and BibTeX.
Run `python sync_site.py` after editing publications or site.css/site.js.
Only SELECTED chooses which papers appear on the homepage; no paper metadata
needs to be maintained twice. Uses the Python standard library only.
"""

import hashlib
import html
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parent
SELECTED = ('J15', 'J11', 'J10', 'J07', 'A02')
PAGES = ('index.html', 'Biography.html', 'Publications.html', 'Teachings.html')
VENUES = {'TASE': 'IEEE T-ASE', 'TAC': 'IEEE TAC', 'L-CSS': 'IEEE L-CSS'}


def plain(markup):
    return html.unescape(re.sub(r'<[^>]+>', '', markup)).strip()


def required(pattern, text, label):
    match = re.search(pattern, text, re.S)
    if not match:
        raise ValueError(f'{label}: required publication field not found')
    return match


def render_selected(source, label):
    match = required(r'<article\b([^>]*\bid="section-' + re.escape(label) +
                     r'"[^>]*)>(.*?)</article>', source, label)
    attrs, article = match.groups()
    title_markup = required(r'<h3 class="pub-title">(.*?)</h3>', article, label)[1]
    title = plain(title_markup)
    bib = required(r'<template class="bib">(.*?)</template>', article, label)[1]
    doi = re.search(r'^\s*doi\s*=\s*\{([^}]+)\}', html.unescape(bib), re.M)
    url = ('https://doi.org/' + doi[1]) if doi else html.unescape(
        required(r'<a\b[^>]*href="([^"]+)"', title_markup, label)[1])
    authors = required(r'<p class="pub-info">(.*?)<br\s*/?>', article, label)[1]
    manuscript = html.unescape(required(
        r'<a\b[^>]*href="([^"]+)"[^>]*>Manuscript</a>', article, label)[1])
    year = required(r'\bdata-year="([^"]+)"', attrs, label)[1]
    venue_match = re.search(r'\bdata-venue="([^"]+)"', attrs)
    venue = VENUES.get(venue_match[1], venue_match[1]) if venue_match else 'arXiv preprint'
    key = label.lower()
    image = ROOT / 'images' / 'selected' / f'{key}.png'
    with image.open('rb') as stream:
        header = stream.read(24)
    if header[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'{image.name}: invalid PNG thumbnail')
    width, height = struct.unpack('>II', header[16:24])
    title, url, manuscript = map(html.escape, (title, url, manuscript))
    destination = 'arXiv' if label.startswith('A') else 'the publisher website'
    return f'''          <article class="selected-paper" aria-labelledby="selected-{key}">
            <span class="pub-label" hidden>[{label}]</span>
            <figure class="paper-preview">
              <a class="paper-thumbnail" href="{url}" target="_blank" rel="noopener" aria-label="Open {title} on {destination}"><!-- thumbnail:{key} --><img src="images/selected/{key}.png" alt="" width="{width}" height="{height}" loading="lazy" decoding="async"><!-- /thumbnail:{key} --></a>
            </figure>
            <div class="selected-paper-body">
              <p class="paper-meta">{html.escape(venue)} &middot; {html.escape(year)}</p>
              <div class="mat paper-actions"><button type="button" class="bib-btn">BibTeX</button><a href="{manuscript}" target="_blank" rel="noopener">Manuscript</a></div>
              <h3 id="selected-{key}"><a href="{url}" target="_blank" rel="noopener" title="{title}">{title}</a></h3>
              <p class="paper-authors">{authors}</p>
            </div>
            <template class="bib">{bib}</template>
          </article>'''


def sync_site():
    source = (ROOT / 'Publications.html').read_text(encoding='utf-8')
    pages = {name: (ROOT / name).read_text(encoding='utf-8') for name in PAGES}
    cards = '\n'.join(render_selected(source, label) for label in SELECTED)
    pattern = r'(<div class="selected-list">)\s*.*?(\s*</div>\s*<details class="thumbnail-credits">)'
    home, count = re.subn(pattern, lambda m: m[1] + '\n' +
                         '          <!-- Generated from Publications.html by sync_site.py -->\n' + cards + m[2],
                         pages['index.html'], count=1, flags=re.S)
    if count != 1:
        raise ValueError('Homepage selected publications container not found')
    pages['index.html'] = home
    for asset in ('site.css', 'site.js'):
        # Normalize line endings so repeated runs on Windows remain stable.
        content = (ROOT / asset).read_text(encoding='utf-8').encode('utf-8')
        version = hashlib.sha256(content).hexdigest()[:12]
        for name in pages:
            pages[name] = re.sub(re.escape(asset) + r'\?v=[a-f0-9]+',
                                 asset + '?v=' + version, pages[name])
    for name, text in pages.items():
        if text != (ROOT / name).read_text(encoding='utf-8'):
            with (ROOT / name).open('w', encoding='utf-8', newline='\n') as stream:
                stream.write(text)


if __name__ == '__main__':
    sync_site()
    print('Homepage publications and asset versions synchronized.')
