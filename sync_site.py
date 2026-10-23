"""Refresh generated homepage publications and news, asset versions, "Last update" and sitemap.xml.

Publications.html is the source for titles, authors, links and BibTeX.
News.html is the news archive: the homepage shows its NEWS_ON_HOME most recent items.
Run `python sync_site.py` after editing any page, site.css or site.js.
Only SELECTED chooses which papers appear on the homepage; no paper metadata
needs to be maintained twice. The footer date and the sitemap dates come from
the last git commit of each file (today for files changed since).
Uses the Python standard library only.
"""

import datetime
import hashlib
import html
from pathlib import Path
import re
import struct
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
SITE_URL = 'https://diegodeplano.github.io/'
SELECTED = ('J15', 'J11', 'J10', 'J07', 'A02')
NEWS_ON_HOME = 6
PAGES = ('index.html', 'Biography.html', 'Publications.html', 'Teachings.html', 'News.html')
VENUES = {'TASE': 'IEEE T-ASE', 'TAC': 'IEEE TAC', 'L-CSS': 'IEEE L-CSS'}
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December')


def last_changes():
    """Return a function giving the date (YYYY-MM-DD) of the last change of a file."""
    today = datetime.date.today().isoformat()
    dates = {}
    try:
        def git(*args):
            return subprocess.run(['git', '-c', 'core.quotePath=false', *args], cwd=ROOT, check=True,
                                  capture_output=True, text=True, encoding='utf-8').stdout
        date = None
        for line in git('log', '--format=@%cs', '--name-only').splitlines():
            if line.startswith('@'):
                date = line[1:]
            elif line and line not in dates:  # newest commits come first
                dates[line] = date
        for line in git('status', '--porcelain', '--untracked-files=all').splitlines():
            dates[line[3:].split(' -> ')[-1].strip('"')] = today
    except (OSError, subprocess.CalledProcessError):  # no git: fall back to the file dates
        pass

    def changed(path):
        if path in dates:
            return dates[path]
        return datetime.date.fromtimestamp((ROOT / path).stat().st_mtime).isoformat()
    return changed


def render_sitemap(pages, page_dates, changed):
    """The four pages, then every file they link to, in order of appearance."""
    urls = [(SITE_URL + ('' if name == 'index.html' else name), page_dates[name]) for name in PAGES]
    seen = set()
    for name in PAGES:
        for href in re.findall(r'href="(files/[^"#?]+)"', pages[name]):
            if href not in seen:
                seen.add(href)
                urls.append((SITE_URL + href, changed(unquote(html.unescape(href)))))
    rows = ''.join(f'  <url><loc>{html.escape(loc)}</loc><lastmod>{date}</lastmod></url>\n' for loc, date in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n')


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
    archive = required(r'<ul class="news-list is-archive">\s*(.*?)\s*</ul>', pages['News.html'], 'News.html')[1]
    latest_news = re.findall(r'<li>.*?</li>', archive, re.S)[:NEWS_ON_HOME]
    home, count = re.subn(r'(<ul class="news-list">).*?(</ul>)', lambda m: m[1] + '\n' +
                         '          <!-- Generated from News.html by sync_site.py: the most recent items -->\n' +
                         ''.join('          ' + item + '\n' for item in latest_news) + '        ' + m[2],
                         home, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Homepage news list not found')
    pages['index.html'] = home
    for asset in ('site.css', 'site.js'):
        # Normalize line endings so repeated runs on Windows remain stable.
        content = (ROOT / asset).read_text(encoding='utf-8').encode('utf-8')
        version = hashlib.sha256(content).hexdigest()[:12]
        for name in pages:
            pages[name] = re.sub(re.escape(asset) + r'\?v=[a-f0-9]+',
                                 asset + '?v=' + version, pages[name])
    changed = last_changes()
    today = datetime.date.today().isoformat()
    page_dates = {name: today if pages[name] != (ROOT / name).read_text(encoding='utf-8') else changed(name)
                  for name in PAGES}
    latest = datetime.date.fromisoformat(max(page_dates.values()))
    for name in pages:
        pages[name] = re.sub(r'Last update: [A-Za-z]+ \d{4}',
                             f'Last update: {MONTHS[latest.month - 1]} {latest.year}', pages[name])
    for name, text in pages.items():
        if text != (ROOT / name).read_text(encoding='utf-8'):
            with (ROOT / name).open('w', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    sitemap = render_sitemap(pages, page_dates, changed)
    if sitemap != (ROOT / 'sitemap.xml').read_text(encoding='utf-8'):
        with (ROOT / 'sitemap.xml').open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(sitemap)


if __name__ == '__main__':
    sync_site()
    print('Homepage publications, asset versions, "Last update" and sitemap.xml synchronized.')
