function addDocumentationLink() {
  const returnLink = document.createElement('a');
  returnLink.className = 'xverse-return';
  returnLink.textContent = '← X-Verse documentation';
  const referenceIndex = location.pathname.indexOf('/reference/python/');
  returnLink.href = location.pathname.slice(0, referenceIndex) + '/docs/reference/';
  document.body.prepend(returnLink);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addDocumentationLink, { once: true });
} else {
  addDocumentationLink();
}
