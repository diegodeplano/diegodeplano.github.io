# Diego Deplano's website

Static HTML, CSS and JavaScript, published from `main` through GitHub Pages.

## Update publications

`Publications.html` is the source for publication titles, authors, official links,
manuscripts and BibTeX. The homepage's five selected publications are generated
from these entries; edit their metadata only in `Publications.html`.

After editing any page or `site.css` / `site.js`, run:

```powershell
python sync_site.py
```

This refreshes the selected cards and the CSS/JavaScript version URLs in all four
pages, so visitors receive updated assets. It also sets the "Last update" footer
and rewrites `sitemap.xml` (the four pages and every file they link to), dating
each entry by its last git commit, or today if it changed since. The site remains
fully static, and the generated cards are also available without JavaScript.

The homepage "News" list is written by hand in `index.html` (newest first, about
six items).

To choose different selected publications, change `SELECTED` in `sync_site.py`.
Each selected entry needs a first-page PNG in `images/selected/`, and its
thumbnail licence attribution must be kept in the homepage credits.

`python add_paper.py` adds a publication interactively and synchronizes the home
automatically. `python add_paper.py --relink` updates co-author links from
`coauthors.json` and synchronizes the home as well.

## Update paper thumbnails

`python generate_paper_previews.py` renders the selected first pages using
PyMuPDF and synchronizes the home. Publisher PDFs belong in the ignored
`files/published/` directory; public manuscript links remain separate from
the PDF sources used for thumbnails.

## Local preview

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Before pushing, run `python sync_site.py` and review
the changed pages and publication dialogs in a browser.
