// Selected papers: slowly scan an overflowing row, until the visitor interacts.
(function () {
  var row = document.querySelector('.selected-list');
  if (!row) return;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var visible = !('IntersectionObserver' in window);
  var stopped = false;
  var frame = 0, lastTime = 0, position = 0, direction = 1, limit = 0, pauseUntil = 0;
  var speed = 24; // CSS pixels per second.

  function tick(time) {
    frame = 0;
    if (lastTime && time >= pauseUntil) {
      position += direction * speed * Math.min(time - lastTime, 50) / 1000;
      if (position >= limit || position <= 0) {
        position = Math.max(0, Math.min(position, limit));
        direction *= -1;
        pauseUntil = time + 1000;
      }
      row.scrollLeft = position;
    }
    lastTime = time;
    frame = requestAnimationFrame(tick);
  }

  function update() {
    limit = Math.max(0, row.scrollWidth - row.clientWidth);
    if (limit > 1) row.setAttribute('tabindex', '0');
    else row.removeAttribute('tabindex');
    var running = limit > 1 && visible && !stopped && !document.hidden && !reducedMotion.matches;
    if (!running) {
      cancelAnimationFrame(frame);
      frame = 0;
      lastTime = 0;
      row.classList.remove('is-auto-scrolling');
      return;
    }
    if (frame) {
      position = Math.min(position, limit);
      return;
    }
    position = row.scrollLeft;
    pauseUntil = performance.now() + 1200;
    row.classList.add('is-auto-scrolling');
    frame = requestAnimationFrame(tick);
  }

  function stop() {
    stopped = true;
    update();
  }
  var gesture = null;
  var ignoreClick = false;

  function classifyTouch(touch) {
    if (!gesture || gesture.axis || !touch) return;
    var dx = Math.abs(touch.clientX - gesture.x);
    var dy = Math.abs(touch.clientY - gesture.y);
    if (Math.max(dx, dy) < 10) return;
    gesture.axis = dx > dy ? 'horizontal' : 'vertical';
    ignoreClick = true;
    if (gesture.axis === 'horizontal') stop();
  }

  // Wait for the direction of a touch gesture: a vertical page swipe is not a tap.
  row.addEventListener('touchstart', function (event) {
    ignoreClick = false;
    var touch = event.touches.length === 1 && event.touches[0];
    gesture = touch ? { x: touch.clientX, y: touch.clientY, axis: null } : null;
  }, { passive: true });
  row.addEventListener('touchmove', function (event) {
    if (event.touches.length === 1) classifyTouch(event.touches[0]);
    else { gesture = null; ignoreClick = true; }
  }, { passive: true });
  row.addEventListener('touchend', function (event) {
    if (!gesture) return;
    classifyTouch(event.changedTouches[0]);
    if (!gesture.axis) stop();
    gesture = null;
  }, { passive: true });
  row.addEventListener('touchcancel', function () {
    gesture = null;
    ignoreClick = true;
  }, { passive: true });
  row.addEventListener('pointerdown', function (event) {
    if (event.pointerType === 'mouse') { ignoreClick = false; stop(); }
  }, { passive: true });
  row.addEventListener('click', function (event) {
    if (!ignoreClick || event.detail === 0) stop();
  });
  row.addEventListener('wheel', function (event) {
    if (Math.abs(event.deltaX) > Math.max(1, Math.abs(event.deltaY)) ||
        (event.shiftKey && Math.abs(event.deltaY) > 1)) stop();
  }, { passive: true });
  row.addEventListener('focusin', function (event) {
    if (event.target.matches(':focus-visible')) stop();
  });
  row.addEventListener('keydown', stop);
  document.addEventListener('visibilitychange', update);
  reducedMotion.addEventListener('change', update);
  if ('ResizeObserver' in window) new ResizeObserver(update).observe(row);
  else window.addEventListener('resize', update);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      update();
    }, { threshold: 0 }).observe(row);
  }
  update();
})();

// Mobile menu: the navigation slides in from the left below 992px.
(function () {
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('site-nav');
  var overlay = document.querySelector('.nav-overlay');
  if (!toggle || !nav) return;

  function setOpen(open) {
    document.body.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  toggle.addEventListener('click', function () { setOpen(true); });
  nav.querySelector('.menu-close').addEventListener('click', function () { setOpen(false); });
  if (overlay) overlay.addEventListener('click', function () { setOpen(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
})();

// Popups (BibTeX, PDF viewer) also close when the dark area around them is clicked.
function closeOnBackdrop(dialog) {
  dialog.addEventListener('click', function (e) {
    if (e.target !== dialog) return;
    var r = dialog.getBoundingClientRect();  // clicks on the dialog's own padding also target it
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  });
}

// BibTeX buttons: open a popup with the entry stored in the publication's <template class="bib">
// and copy it to the clipboard right away.
(function () {
  var buttons = document.querySelectorAll('.bib-btn');
  if (!buttons.length) return;

  var dialog = document.createElement('dialog');
  dialog.className = 'bib-dialog';
  dialog.innerHTML = '<div class="bib-dialog-head"><h2>BibTeX citation</h2>' +
    '<button type="button" class="bib-close" aria-label="Close">&times;</button></div>' +
    '<pre tabindex="-1" autofocus></pre><button type="button" class="bib-copy">Copy BibTeX</button>';
  document.body.appendChild(dialog);
  var pre = dialog.querySelector('pre');
  var copyBtn = dialog.querySelector('.bib-copy');
  var resetTimer;

  function copy(text) {
    function done() {
      copyBtn.textContent = 'Copied ✓';
      clearTimeout(resetTimer);
      resetTimer = setTimeout(function () { copyBtn.textContent = 'Copy BibTeX'; }, 2000);
    }
    function fallback() {
      var range = document.createRange();
      range.selectNodeContents(pre);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      try { if (document.execCommand('copy')) done(); } catch (e) {}
      sel.removeAllRanges();
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var tpl = btn.closest('article, section').querySelector('template.bib');
      if (!tpl) return;
      pre.textContent = tpl.content.textContent.trim();
      copyBtn.textContent = 'Copy BibTeX';
      dialog.showModal();
      copy(pre.textContent);
    });
  });

  copyBtn.addEventListener('click', function () { copy(pre.textContent); });
  dialog.querySelector('.bib-close').addEventListener('click', function () { dialog.close(); });
  closeOnBackdrop(dialog);
})();

// Abstract buttons: the abstract stored in the paper's <template class="abstract">, in a popup.
// Each opening counts as a GoatCounter event, e.g. "abstract/J09".
(function () {
  var buttons = document.querySelectorAll('.abs-btn');
  if (!buttons.length) return;

  var dialog = document.createElement('dialog');
  dialog.className = 'bib-dialog abs-dialog';
  dialog.innerHTML = '<div class="bib-dialog-head"><div><span class="abs-label"></span><h2></h2></div>' +
    '<button type="button" class="bib-close" aria-label="Close">&times;</button></div><p tabindex="-1" autofocus></p>';
  document.body.appendChild(dialog);
  var label = dialog.querySelector('.abs-label');
  var heading = dialog.querySelector('h2');
  var text = dialog.querySelector('p');

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var entry = btn.closest('article, section');
      var tpl = entry.querySelector('template.abstract');
      if (!tpl) return;
      var pubLabel = entry.querySelector('.pub-label');  // "[J09]"
      var code = pubLabel ? pubLabel.textContent.replace(/[\[\]\s]/g, '') : '';
      label.textContent = (code ? '[' + code + '] ' : '') + 'Abstract';
      heading.textContent = entry.querySelector('h3').textContent.trim();
      text.textContent = tpl.content.textContent.trim();
      dialog.showModal();
      text.scrollTop = 0;
      if (window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({ path: 'abstract/' + code, title: label.textContent, event: true });
      }
    });
  });

  dialog.querySelector('.bib-close').addEventListener('click', function () { dialog.close(); });
  closeOnBackdrop(dialog);
})();

// Material popup: manuscripts, slides, posters (PDF) and talk videos open over the page instead of a new tab.
// PDFs only where the browser shows them inline and there is a mouse: phones and tablets open the file as before.
// Ctrl/Cmd/Shift-click or middle click still open the link in a new tab.
function isPdf(href) { return /^[^:]+\.pdf$/i.test(href); }  // a PDF of the site, e.g. "files/x.pdf"

(function () {
  var pdfInline = navigator.pdfViewerEnabled && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  function embed(href) {  // address shown in the popup, or null to follow the link as usual
    var m;
    if (isPdf(href)) return pdfInline ? href + '#navpanes=0' : null;  // no thumbnail sidebar
    if ((m = href.match(/^https:\/\/youtu\.be\/([\w-]+)/))) {
      return 'https://www.youtube-nocookie.com/embed/' + m[1] + '?autoplay=1&rel=0';
    }
    if ((m = href.match(/^https:\/\/video\.ethz\.ch\/.*\/v\/([\w-]+)(\?t=\w+)?/))) {  // start time as "?t=40m28s"
      return 'https://video.ethz.ch/~embed/!v/' + m[1] + (m[2] || '');
    }
    return null;
  }
  var links = Array.prototype.filter.call(document.querySelectorAll('.mat a'), function (a) {
    return embed(a.getAttribute('href'));
  });
  if (!links.length) return;

  var dialog = document.createElement('dialog');
  dialog.className = 'pdf-dialog';
  dialog.innerHTML = '<div class="pdf-dialog-head"><h2></h2>' +
    '<a class="pdf-action" target="_blank">Open in new tab</a><a class="pdf-action pdf-download" download>Download</a>' +
    '<button type="button" class="bib-close" aria-label="Close">&times;</button></div>';
  document.body.appendChild(dialog);
  var heading = dialog.querySelector('h2');
  var actions = dialog.querySelectorAll('.pdf-action');
  var download = dialog.querySelector('.pdf-download');
  var frame = null;  // a new frame for every file

  links.forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      var href = link.getAttribute('href');
      var entry = link.closest('article, section');
      var label = entry && entry.querySelector('.pub-label, h2');  // "[J16]", or "PhD Thesis"
      heading.textContent = (label ? label.textContent.trim() + ' · ' : '') + link.textContent.trim();
      actions.forEach(function (a) { a.href = link.href; });
      download.hidden = !isPdf(href);
      dialog.classList.toggle('is-video', !isPdf(href));
      dialog.showModal();
      if (frame) frame.remove();
      frame = dialog.appendChild(document.createElement('iframe'));
      frame.title = link.textContent.trim();
      frame.allow = 'autoplay; fullscreen; picture-in-picture; encrypted-media';
      frame.src = embed(href);
    });
  });

  dialog.querySelector('.bib-close').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('close', function () {  // the event comes late: another file may be open already
    if (frame && !dialog.open) { frame.remove(); frame = null; }
  });
  closeOnBackdrop(dialog);
})();

// GoatCounter: opening a PDF or a video counts as an event, e.g. "files/x.pdf" titled "[J09] Slides"
// (page views are counted by count.js itself).
(function () {
  function track(e) {
    var link = e.target.closest && e.target.closest('a[href]');
    if (!link || link.closest('dialog') || (e.type === 'auxclick' && e.button !== 1)) return;  // popup: counted already
    var href = link.getAttribute('href');
    if (!(isPdf(href) || /^https:\/\/(youtu\.be|video\.ethz\.ch)\//.test(href))) return;
    if (!window.goatcounter || !window.goatcounter.count) return;
    var entry = link.closest('.pub, .phd, .selected-paper');
    var label = entry && entry.querySelector('.pub-label, h2');
    window.goatcounter.count({
      path: isPdf(href) ? decodeURIComponent(href) : href,
      title: (label ? label.textContent.trim() + ' ' : '') + link.textContent.trim(),
      event: true
    });
  }
  document.addEventListener('click', track);
  document.addEventListener('auxclick', track);  // middle click
})();

// Publication filters: dropdown menus (type, year, venue, co-author) built from the papers on the page.
// Choices in the same menu add up, choices in different menus narrow the list down;
// category banners and dividers are hidden along with their papers.
// A conference entry that points to a journal entry ("published in IEEE L-CSS, see [J08]") is the same
// paper listed twice: it is shown by the filters but left out of every count.
(function () {
  var panel = document.getElementById('pub-filter');
  if (!panel) return;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function countBy(list, key) {  // key may return one value or a list of values
    var counts = {};
    list.forEach(function (x) {
      [].concat(key(x)).forEach(function (k) { if (k) counts[k] = (counts[k] || 0) + 1; });
    });
    return counts;
  }
  function coauthors(node) {  // names before the first line break of the paper info, without D. Deplano
    var info = node.querySelector('.pub-info');
    if (!info) return [];
    var first = document.createElement('div');
    first.innerHTML = info.innerHTML.split(/<br\s*\/?>/i)[0];
    return first.textContent.split(/,|\band\b/).map(function (s) { return s.trim(); })
      .filter(function (s) { return s && !/Deplano/.test(s); });
  }
  function surname(name) { return name.replace(/^([A-Z]\.\s*)+/, ''); }  // "Z.A.Z. Sanai Dashti" -> "Sanai Dashti"
  function surnameFirst(name) {  // "Z.A.Z. Sanai Dashti" -> "Sanai Dashti, Z.A.Z."
    var initials = name.slice(0, name.length - surname(name).length).trim();
    return initials ? surname(name) + ', ' + initials : name;
  }
  function alpha(a, b) { return a.localeCompare(b, undefined, { sensitivity: 'base' }); }
  function searchable(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replace(/multi[\s\-\u2010-\u2015]*agent/g, 'multiagent')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }

  // papers grouped under their category banner, in page order
  var groups = [], papers = [], group = null;
  Array.prototype.forEach.call(panel.parentNode.children, function (node) {
    if (node.classList.contains('banner')) {
      var title = node.textContent.trim();  // e.g. "Journal Articles", shown in the menus as "Journal"
      group = { el: node, id: node.id, label: title, short: title.split(' ')[0], papers: [] };
      groups.push(group);
    } else if (node.classList.contains('pub') && group) {
      var paper = { el: node, group: group, year: node.getAttribute('data-year') || '', venue: node.getAttribute('data-venue') || '',
                    authors: coauthors(node), duplicate: !!node.querySelector('a.xref[href^="#section-J"]'),
                    searchText: searchable(node.querySelector('.pub-title').textContent + ' ' +
                      node.querySelector('.pub-label').textContent + ' ' + (node.getAttribute('data-keywords') || '')) };
      group.papers.push(paper);
      papers.push(paper);
    }
  });
  if (!papers.length) return;

  // menus in alphabetical order (years: newest first; venues: journals, then conferences, as on the page)
  var sortedGroups = groups.slice().sort(function (a, b) { return alpha(a.short, b.short); });
  var dims = [
    { name: 'Type', of: function (p) { return p.group.id; },
      options: sortedGroups.map(function (g) { return { value: g.id, label: g.short }; }) },
    { name: 'Year', of: function (p) { return p.year; },
      options: Object.keys(countBy(papers, function (p) { return p.year; })).sort().reverse()
        .map(function (y) { return { value: y, label: y }; }) },
    { name: 'Published in', of: function (p) { return p.venue; }, options: [] },
    { name: 'Co-author', of: function (p) { return p.authors; }, options: [] }
  ];
  var authorCounts = countBy(papers, function (p) { return p.authors; });  // co-authors by surname
  dims[3].options = Object.keys(authorCounts).sort(function (a, b) {
    return alpha(surname(a), surname(b)) || alpha(a, b);
  }).map(function (name) { return { value: name, label: surnameFirst(name) }; });
  groups.forEach(function (g) {  // venues listed under their category, alphabetically
    var venues = Object.keys(countBy(g.papers, function (p) { return p.venue; })).sort(alpha);
    if (!venues.length) return;
    dims[2].options.push({ heading: g.label });
    venues.forEach(function (v) { dims[2].options.push({ value: v, label: v }); });
  });

  var search = el('div', 'filter-search');
  var searchLabel = search.appendChild(el('label', '', 'Search publications'));
  searchLabel.htmlFor = 'pub-search';
  var searchInput = search.appendChild(el('input'));
  searchInput.id = 'pub-search';
  searchInput.type = 'search';
  searchInput.placeholder = 'Title or keywords, e.g. consensus, multi-agent';
  searchInput.addEventListener('input', update);
  var terms = [];
  var bar = el('div', 'filter-bar');
  bar.appendChild(el('span', 'filter-title', 'Filter publications'));
  dims.forEach(function (dim) {
    dim.dd = el('details', 'filter-dd');
    var summary = dim.dd.appendChild(el('summary'));
    summary.appendChild(el('span', 'filter-name', dim.name + ':'));
    dim.valueEl = summary.appendChild(el('span', 'filter-value'));
    var menu = dim.dd.appendChild(el('div', 'filter-menu'));
    dim.options.forEach(function (opt) {
      if (opt.heading) { menu.appendChild(el('div', 'filter-group', opt.heading)); return; }
      opt.row = menu.appendChild(el('label', 'filter-option'));
      opt.input = opt.row.appendChild(el('input'));
      opt.input.type = 'checkbox';
      opt.input.addEventListener('change', update);
      opt.row.appendChild(el('span', '', opt.label));
      opt.countEl = opt.row.appendChild(el('span', 'count'));
    });
    dim.choices = dim.options.filter(function (opt) { return opt.input; });
    dim.dd.addEventListener('toggle', function () {  // one menu open at a time
      if (dim.dd.open) dims.forEach(function (d) { if (d !== dim) d.dd.open = false; });
    });
    bar.appendChild(dim.dd);
  });
  var status = bar.appendChild(el('div', 'filter-status'));
  var countEl = status.appendChild(el('span', 'filter-count'));
  countEl.setAttribute('aria-live', 'polite');
  countEl.title = 'IEEE L-CSS letters presented at the CDC appear in both lists but are counted once';
  var resetBtn = status.appendChild(el('button', 'filter-reset', 'Reset'));
  resetBtn.type = 'button';
  var empty = el('p', 'filter-empty', 'No publications match your search and filters.');
  var container = panel.querySelector('.container');
  container.appendChild(search);
  container.appendChild(bar);
  container.appendChild(empty);
  panel.hidden = false;

  function selected(dim) {
    return dim.choices.filter(function (o) { return o.input.checked; });
  }
  function has(dim, paper, value) {  // a paper has one type/year/venue but several co-authors
    return [].concat(dim.of(paper)).indexOf(value) >= 0;
  }
  function matches(paper, skip) {
    return terms.every(function (term) { return paper.searchText.indexOf(term) >= 0; }) && dims.every(function (dim) {
      if (dim === skip) return true;
      var sel = selected(dim);
      return !sel.length || sel.some(function (o) { return has(dim, paper, o.value); });
    });
  }

  function counted(list) { return list.filter(function (p) { return !p.duplicate; }).length; }

  function update() {
    var query = searchable(searchInput.value);
    terms = query ? query.split(/\s+/) : [];
    var shown = 0, shownCounted = 0;
    papers.forEach(function (p) {
      p.el.hidden = !matches(p);
      if (!p.el.hidden) { shown++; if (!p.duplicate) shownCounted++; }
    });
    groups.forEach(function (g) {  // a divider only between two visible papers of the same category
      var seen = false;
      g.papers.forEach(function (p) {
        var line = p.el.previousElementSibling;
        if (line && line.classList.contains('pub-sep')) line.hidden = p.el.hidden || !seen;
        if (!p.el.hidden) seen = true;
      });
      g.el.hidden = !seen;
    });
    dims.forEach(function (dim) {  // counts given the other menus' choices
      var pool = papers.filter(function (p) { return matches(p, dim); });
      dim.choices.forEach(function (opt) {
        var hits = pool.filter(function (p) { return has(dim, p, opt.value); });
        opt.countEl.textContent = counted(hits);
        opt.input.disabled = !hits.length && !opt.input.checked;
        opt.row.classList.toggle('is-empty', !hits.length);
      });
      var labels = selected(dim).map(function (o) { return o.label; });
      var text = labels.join(labels.join('').indexOf(',') >= 0 ? '; ' : ', ');  // "Giua, A.; Seatzu, C."
      dim.valueEl.textContent = !labels.length ? 'All' : labels.length > 1 && text.length > 20 ? labels.length + ' selected' : text;
      dim.dd.classList.toggle('is-active', labels.length > 0);
    });
    var active = terms.length > 0 || dims.some(function (dim) { return selected(dim).length; });
    var total = counted(papers);
    countEl.textContent = active ? 'Showing ' + shownCounted + ' of ' + total + ' publications' : total + ' publications';
    resetBtn.hidden = !active;
    empty.hidden = shown > 0;
  }

  function reset() {
    searchInput.value = '';
    dims.forEach(function (dim) { dim.choices.forEach(function (o) { o.input.checked = false; }); });
    update();
  }
  resetBtn.addEventListener('click', reset);

  document.addEventListener('click', function (e) {
    dims.forEach(function (d) { if (d.dd.open && !d.dd.contains(e.target)) d.dd.open = false; });
    // a cross-reference such as "see [C28]" to a hidden paper clears the filters first
    var link = e.target.closest && e.target.closest('a.xref');
    var target = link && document.getElementById(link.getAttribute('href').slice(1));
    if (target && target.hidden) reset();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    dims.forEach(function (d) {
      if (d.dd.open) { d.dd.open = false; d.dd.querySelector('summary').focus(); }
    });
  });

  update();
})();
