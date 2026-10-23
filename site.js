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
  dialog.addEventListener('click', function (e) {
    if (e.target !== dialog) return;
    var r = dialog.getBoundingClientRect();  // clicks on the dialog's own padding also target it
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  });
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
  function surname(name) { return name.split(/\s+/).pop(); }

  // papers grouped under their category banner, in page order
  var groups = [], papers = [], group = null;
  Array.prototype.forEach.call(panel.parentNode.children, function (node) {
    if (node.classList.contains('banner')) {
      var title = node.textContent.trim();  // e.g. "Journal Articles", shown in the menus as "Journal"
      group = { el: node, id: node.id, label: title, short: title.split(' ')[0], papers: [] };
      groups.push(group);
    } else if (node.classList.contains('pub') && group) {
      var paper = { el: node, group: group, year: node.getAttribute('data-year') || '', venue: node.getAttribute('data-venue') || '',
                    authors: coauthors(node), duplicate: !!node.querySelector('a.xref[href^="#section-J"]') };
      group.papers.push(paper);
      papers.push(paper);
    }
  });
  if (!papers.length) return;

  var dims = [
    { name: 'Type', of: function (p) { return p.group.id; },
      options: groups.map(function (g) { return { value: g.id, label: g.short }; }) },
    { name: 'Year', of: function (p) { return p.year; },
      options: Object.keys(countBy(papers, function (p) { return p.year; })).sort().reverse()
        .map(function (y) { return { value: y, label: y }; }) },
    { name: 'Published in', of: function (p) { return p.venue; }, options: [] },
    { name: 'Co-author', of: function (p) { return p.authors; }, options: [] }
  ];
  var authorCounts = countBy(papers, function (p) { return p.authors; });  // most frequent co-authors first
  dims[3].options = Object.keys(authorCounts).sort(function (a, b) {
    return authorCounts[b] - authorCounts[a] || surname(a).localeCompare(surname(b));
  }).map(function (name) { return { value: name, label: name }; });
  groups.forEach(function (g) {  // venues listed under their category, most frequent first
    var counts = countBy(g.papers, function (p) { return p.venue; });
    var venues = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a] || a.localeCompare(b); });
    if (!venues.length) return;
    dims[2].options.push({ heading: g.label });
    venues.forEach(function (v) { dims[2].options.push({ value: v, label: v }); });
  });

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
  var empty = el('p', 'filter-empty', 'No publications match the selected filters.');
  var container = panel.querySelector('.container');
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
    return dims.every(function (dim) {
      if (dim === skip) return true;
      var sel = selected(dim);
      return !sel.length || sel.some(function (o) { return has(dim, paper, o.value); });
    });
  }

  function counted(list) { return list.filter(function (p) { return !p.duplicate; }).length; }

  function update() {
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
      var text = labels.join(', ');
      dim.valueEl.textContent = !labels.length ? 'All' : labels.length > 1 && text.length > 20 ? labels.length + ' selected' : text;
      dim.dd.classList.toggle('is-active', labels.length > 0);
    });
    var active = dims.some(function (dim) { return selected(dim).length; });
    var total = counted(papers);
    countEl.textContent = active ? 'Showing ' + shownCounted + ' of ' + total + ' publications' : total + ' publications';
    resetBtn.hidden = !active;
    empty.hidden = shown > 0;
  }

  function reset() {
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
