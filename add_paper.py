import re
import sys

# Path to Publications.html
PUB_FILE = 'Publications.html'

def add_paper():
    print("Welcome to the paper adder script for Diego DePlano's website.")
    print("Answer the questions to add a new paper.")
    print("Supported types: (j)ournal paper, (c)onference paper, (a)rxiv preprint")

    paper_type = input("Is this a (j)ournal paper, (c)onference paper, or (a)rxiv preprint? ").lower().strip()
    if paper_type not in ['j', 'journal', 'c', 'conference', 'a', 'arxiv']:
        print("Invalid type. Exiting.")
        return
    is_journal = paper_type.startswith('j')
    is_arxiv = paper_type.startswith('a')
    is_conference = paper_type.startswith('c')

    paper_title = input("Paper title: ").strip().upper()
    authors = input("Authors (e.g., D. Deplano, M. Franceschelli): ").strip()
    # Underline "D. Deplano" as per C1-C16 style
    authors = authors.replace("D. Deplano", '<span style="text-decoration: underline !important;">D. Deplano</span>')
    if is_journal:
        journal_name = input("Journal name: ").strip()
        year = input("Year: ").strip()
        journal_info = f"{journal_name}, {year}"
        doi_link = input("DOI or IEEE Xplore link: ").strip()
        journal_url = input("Journal homepage URL (for image link): ").strip()
        img_src = input("Image filename (without .jpg, e.g., tacon): ").strip()
    elif is_arxiv:
        journal_name = input("Journal/conference name: ").strip()
        round_num = input("Review round number (1, 2, 3, etc.) or blank if new: ").strip()
        year = input("Year: ").strip()
        if round_num:
            # Convert number to ordinal (1->1st, 2->2nd, 3->3rd, etc.)
            n = int(round_num)
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            arxiv_info = f"Under review at {journal_name} ({round_num}{suffix} round), {year}"
        else:
            arxiv_info = f"Under review at {journal_name}, {year}"
        doi_link = input("arXiv link or DOI: ").strip()
        journal_url = "arxiv.org"  # default arXiv link for image
        img_src = "ARXIV"  # assume there's an arxiv.jpg image
    else:
        # Conference
        conf_name = input("Conference full name: ").strip()
        year = input("Year: ").strip()
        conf_info = f"{conf_name}, {year}"
        conf_url = input("Conference homepage URL: ").strip()
        doi_link = input("IEEE Xplore link: ").strip()
        img_src = input("Image filename (without .jpg, e.g., case24): ").strip()

    file_base = input("Base filename (e.g., 2025_TAC): ").strip()

    has_slides = input("Do you have slides? (y/n): ").lower().startswith('y')
    has_poster = input("Do you have poster? (y/n): ").lower().startswith('y')
    video_link = None
    if input("Do you have video link? (y/n): ").lower().startswith('y'):
        video_link = input("Video link (e.g., https://youtu.be/...): ").strip()

    # Build material links in order: Manuscript (always) -> Slides -> Poster -> Video
    material_links = []
    # Manuscript (always present)
    material_links.append(f'<a href="files/{file_base} - Manuscript.pdf" class="u-active-none u-border-none u-btn u-button-link u-button-style u-file-link u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-2" target="_blank">Manuscript</a>')
    # Slides
    if has_slides:
        material_links.append(f'<span style="font-style: italic;"> &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; <a href="files/{file_base} - Slides.pdf" class="u-active-none u-border-none u-btn u-button-link u-button-style u-file-link u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-3" target="_blank">Slides</a></span>')
    # Poster
    if has_poster:
        material_links.append(f'<span style="font-style: italic;"> &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; <a href="files/{file_base} - Poster.pdf" class="u-active-none u-border-none u-btn u-button-link u-button-style u-file-link u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-4" target="_blank">Poster</a></span>')
    # Video
    if video_link:
        material_links.append(f'<span style="font-style: italic;"> &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; <a href="{video_link}" class="u-active-none u-border-none u-btn u-button-link u-button-style u-hover-none u-none u-text-body-color u-text-hover-palette-2-base u-btn-5" target="_blank">Video</a></span>')
    
    materials_html = "".join(material_links)

    # Read the file
    with open(PUB_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find section
    if is_journal:
        section_pattern = re.compile(r'<section class="u-clearfix u-palette-2-base u-section-category" id="section-category-j">.*?<h1.*?JOURNAL ARTICLES</h1>.*?</section>', re.DOTALL)
        section_match = section_pattern.search(content)
        if not section_match:
            print("Journal section not found.")
            return
        insert_pos = section_match.end()

        # Find next number for J
        # Find all [JX] in journal section
        journal_section = content[section_match.start():]
        j_nums = re.findall(r'\[J(\d+)\]', journal_section)
        if j_nums:
            max_num = max(int(n) for n in j_nums)
            new_num = max_num + 1
        else:
            new_num = 1  # Though unlikely

        # Generate HTML
        html = f'''    <section class="u-clearfix u-section-paper" id="section-J{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="data-layout-selected u-clearfix u-expanded-width u-layout-custom-sm u-layout-custom-xs u-layout-wrap u-layout-wrap-1">
          <div class="u-layout">
            <div class="u-layout-row">
              <div class="u-container-style u-layout-cell u-size-1-sm u-size-1-xs u-size-10-lg u-size-10-md u-size-10-xl u-layout-cell-1">
                <div class="u-container-layout u-container-layout-1">
                  <img class="u-hidden-sm u-hidden-xs u-image u-image-default u-preserve-proportions u-image-1" src="images/{img_src}.jpg" alt="" data-image-width="560" data-image-height="310" data-href="https://{journal_url}" data-target="_blank">
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-47-lg u-size-47-md u-size-47-xl u-size-52-xs u-size-54-sm u-layout-cell-2">
                <div class="u-container-layout u-container-layout-2">
                  <p class="u-custom-font u-font-oswald u-text u-text-default u-text-1">
                    <a href="https://{doi_link}" class="u-active-none u-border-none u-btn u-button-link u-button-style u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-1" target="_blank">{paper_title}</a>
                    <br>
                  </p>
                  <p class="u-text u-text-2">{authors}<br>{journal_info}<br>Material links:&nbsp; &nbsp; &nbsp; {materials_html}
                  </p>
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-3-lg u-size-3-md u-size-3-xl u-size-5-sm u-size-7-xs u-layout-cell-3">
                <div class="u-container-layout u-valign-top u-container-layout-3">
                  <p class="u-align-center u-custom-font u-font-oswald u-text u-text-default u-text-3">[J{new_num}]</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="u-clearfix u-section-line" id="section-line-J{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="u-align-center u-border-3 u-border-palette-2-base u-line u-line-horizontal u-line-1"></div>
      </div>
    </section>'''

        # Insert
        new_content = content[:insert_pos] + html + content[insert_pos:]

    elif is_arxiv:
        # ArXiv preprint - uses journal format but adds to ARXIV PREPRINTS section
        section_pattern = re.compile(r'<section class="u-clearfix u-palette-2-base u-section-category" id="section-category-arxiv">.*?<h1.*?ARXIV PREPRINTS</h1>.*?</section>', re.DOTALL)
        section_match = section_pattern.search(content)
        if not section_match:
            print("ArXiv section not found. Please ensure ARXIV PREPRINTS section exists in Publications.html")
            return
        insert_pos = section_match.end()

        # Find next number for A
        # Find all [AX] in arxiv section
        arxiv_section = content[section_match.start():]
        a_nums = re.findall(r'\[A(\d+)\]', arxiv_section)
        if a_nums:
            max_num = max(int(n) for n in a_nums)
            new_num = max_num + 1
        else:
            new_num = 1  # First arXiv paper

        # Generate HTML using journal paper format
        html = f'''    <section class="u-clearfix u-section-paper" id="section-A{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="data-layout-selected u-clearfix u-expanded-width u-layout-custom-sm u-layout-custom-xs u-layout-wrap u-layout-wrap-1">
          <div class="u-layout">
            <div class="u-layout-row">
              <div class="u-container-style u-layout-cell u-size-1-sm u-size-1-xs u-size-10-lg u-size-10-md u-size-10-xl u-layout-cell-1">
                <div class="u-container-layout u-container-layout-1">
                  <img class="u-hidden-sm u-hidden-xs u-image u-image-default u-preserve-proportions u-image-1" src="images/{img_src}.jpg" alt="" data-image-width="560" data-image-height="310" data-href="https://{journal_url}" data-target="_blank">
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-47-lg u-size-47-md u-size-47-xl u-size-52-xs u-size-54-sm u-layout-cell-2">
                <div class="u-container-layout u-container-layout-2">
                  <p class="u-custom-font u-font-oswald u-text u-text-default u-text-1">
                    <a href="{doi_link}" class="u-active-none u-border-none u-btn u-button-link u-button-style u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-1" target="_blank">{paper_title}</a>
                    <br>
                  </p>
                  <p class="u-text u-text-2">{authors}<br>{arxiv_info}<br>Material links:&nbsp; &nbsp; &nbsp; {materials_html}
                  </p>
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-3-lg u-size-3-md u-size-3-xl u-size-5-sm u-size-7-xs u-layout-cell-3">
                <div class="u-container-layout u-valign-top u-container-layout-3">
                  <p class="u-align-center u-custom-font u-font-oswald u-text u-text-default u-text-3">[A{new_num}]</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="u-clearfix u-section-line" id="section-line-A{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="u-align-center u-border-3 u-border-palette-2-base u-line u-line-horizontal u-line-1"></div>
      </div>
    </section>'''

        # Insert
        new_content = content[:insert_pos] + html + content[insert_pos:]

    else:
        # Conference
        section_pattern = re.compile(r'<section class="u-clearfix u-palette-2-base u-section-line-category" id="section-category-c">.*?<h1.*?CONFERENCE PROCEEDINGS</h1>.*?</section>', re.DOTALL)
        section_match = section_pattern.search(content)
        if not section_match:
            print("Conference section not found.")
            return
        insert_pos = section_match.end()

        # Find max C num
        conf_section = content[section_match.start():]
        c_nums = re.findall(r'\[C(\d+)\]', conf_section)
        if c_nums:
            max_num = max(int(n) for n in c_nums)
            new_num = max_num + 1
        else:
            new_num = 1

        # Generate HTML
        slides_part = f'''<span style="font-style: italic;"> &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; <a href="files/{file_base} - Slides.pdf" class="u-active-none u-border-none u-btn u-button-link u-button-style u-file-link u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-3" target="_blank">Slides</a>
                </span>''' if has_slides else ''

        html = f'''    <section class="u-clearfix u-section-paper" id="section-C{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="data-layout-selected u-clearfix u-expanded-width u-layout-custom-sm u-layout-custom-xs u-layout-wrap u-layout-wrap-1">
          <div class="u-layout">
            <div class="u-layout-row">
              <div class="u-container-style u-layout-cell u-size-1-sm u-size-1-xs u-size-10-lg u-size-10-md u-size-10-xl u-layout-cell-1">
                <div class="u-container-layout u-container-layout-1">
                  <img class="u-hidden-sm u-hidden-xs u-image u-image-default u-preserve-proportions u-image-1" src="images/{img_src}.jpg" alt="" data-image-width="560" data-image-height="310" data-href="{conf_url}">
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-47-lg u-size-47-md u-size-47-xl u-size-52-xs u-size-54-sm u-layout-cell-2">
                <div class="u-container-layout u-container-layout-2">
                  <p class="u-custom-font u-font-oswald u-text u-text-default u-text-1">
                    <a href="{doi_link}" class="u-active-none u-border-none u-btn u-button-link u-button-style u-hover-none u-none u-text-black u-text-hover-palette-2-base u-btn-1" target="_blank">{paper_title}</a>
                    <br>
                  </p>
                  <p class="u-text u-text-2"> {authors}<br>{conf_info}<br>Material links:&nbsp; &nbsp; &nbsp; {materials_html}
                  </p>
                </div>
              </div>
              <div class="u-container-style u-layout-cell u-size-3-lg u-size-3-md u-size-3-xl u-size-5-sm u-size-7-xs u-layout-cell-3">
                <div class="u-container-layout u-valign-top u-container-layout-3">
                  <p class="u-align-center u-custom-font u-font-oswald u-text u-text-default u-text-3">[C{new_num}]</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="u-clearfix u-section-line" id="section-line-C{new_num}">
      <div class="u-clearfix u-sheet u-sheet-1">
        <div class="u-align-center u-border-3 u-border-palette-2-base u-line u-line-horizontal u-line-1"></div>
      </div>
    </section>'''

        new_content = content[:insert_pos] + html + content[insert_pos:]

    # No need to shift numbering since adding newest at top with new number

    with open(PUB_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    paper_code = "J" if is_journal else ("A" if is_arxiv else "C")
    print(f"Paper added successfully as [{paper_code}{new_num}].")
    print("Remember to upload the PDF and image files to the appropriate directories.")
    print("Update sitemap.xml if necessary.")

if __name__ == '__main__':
    add_paper()
