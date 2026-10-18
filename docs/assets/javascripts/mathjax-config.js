// Конфигурация MathJax для pymdownx.arithmatex (generic) и Material instant loading.
window.MathJax = {
  tex: {
    inlineMath: [["\(", "\)"]],
    displayMath: [["\[", "\]"]],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams",
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

if (typeof document$ !== "undefined") {
  document$.subscribe(() => {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.startup.output.clearCache();
      MathJax.typesetClear();
      MathJax.texReset();
      MathJax.typesetPromise();
    }
  });
}
