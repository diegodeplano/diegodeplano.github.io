"""Render first-page thumbnails for the five selected papers (requires PyMuPDF).

Run from any directory: python generate_paper_previews.py
Place the publisher PDFs at files/published/J15.pdf, J11.pdf, J10.pdf, J07.pdf.
Missing publisher PDFs are left as explicit placeholders; author manuscripts
are never substituted for the publisher versions. This prepares local previews;
All four selected publisher PDFs were verified on IEEE Xplore as CC BY 4.0.
Attribution and licence links are retained in index.html.
A02's arXiv version is CC BY 4.0: https://arxiv.org/abs/2506.17990
"""

from pathlib import Path

import fitz
from sync_site import sync_site


ROOT = Path(__file__).resolve().parent
PREVIEWS = {
    "j15": "published/J15.pdf",
    "j11": "published/J11.pdf",
    "j10": "published/J10.pdf",
    "j07": "published/J07.pdf",
    "a02": "ARXIV - ENRICHED - Manuscript.pdf",
}


def main():
    output = ROOT / "images" / "selected"
    output.mkdir(parents=True, exist_ok=True)
    for key, filename in PREVIEWS.items():
        source = ROOT / "files" / filename
        if not source.exists():
            print(f"{key.upper()}: waiting for {source.relative_to(ROOT)}")
            continue
        with fitz.open(source) as document:
            page = document[0]
            if key != "a02":
                text = page.get_text().lower()
                provisional = ("generic colorized journal", "journal of latex class files",
                               "author's version", "vol. xx")
                if any(marker in text for marker in provisional):
                    raise ValueError(f"{filename} is an author manuscript, not the published version")
            scale = 440 / page.rect.width
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            target = output / f"{key}.png"
            pixmap.save(target)
            print(f"{target.relative_to(ROOT)}: {pixmap.width} x {pixmap.height}")
    sync_site()


if __name__ == "__main__":
    main()
