const xverseBack = document.createElement('a');
xverseBack.className = 'xverse-return';
xverseBack.textContent = '← X-Verse documentation';
const cppIndex = location.pathname.indexOf('/reference/cpp/');
xverseBack.href = location.pathname.slice(0, cppIndex) + '/docs/reference/';
document.body.prepend(xverseBack);
