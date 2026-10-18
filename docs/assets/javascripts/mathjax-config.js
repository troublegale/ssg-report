// MathJax для pymdownx.arithmatex (generic). Библиотека лежит на сайте (assets/vendor/mathjax),
// а не на CDN, и загружается только на страницах, где есть формулы (элементы .arithmatex):
// страницы без формул экономят ~2 МБ (≈560 КБ gzip).
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams",
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

(function () {
  // каталог assets/javascripts/ этого скрипта → assets/vendor/mathjax/tex-svg.js
  var src = document.currentScript.src.replace(
    /javascripts\/mathjax-config\.js.*$/,
    "vendor/mathjax/tex-svg.js"
  );
  var requested = false;

  function typeset() {
    if (!document.querySelector(".arithmatex")) return;
    if (window.MathJax.typesetPromise) {
      MathJax.startup.output.clearCache();
      MathJax.typesetClear();
      MathJax.texReset();
      MathJax.typesetPromise();
    } else if (!requested) {
      requested = true;
      var s = document.createElement("script");
      s.src = src;
      s.async = true;
      document.head.appendChild(s);
    }
  }

  // document$ — поток Material, срабатывает при каждой загрузке страницы (в т. ч. instant loading)
  if (typeof document$ !== "undefined") {
    document$.subscribe(typeset);
  } else {
    document.addEventListener("DOMContentLoaded", typeset);
  }
})();
