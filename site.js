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
