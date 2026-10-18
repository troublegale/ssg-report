"""Проверка собранного сайта: страницы не должны загружать ресурсы со сторонних хостов.

Ищет внешние URL в <script src>, <link rel=stylesheet|preload|icon href>, <img src>
во всех HTML и в url(...) / @import во всех CSS. Ссылки <a href> и <link rel=canonical> не проверяются.
Код возврата 1, если найден хотя бы один внешний ресурс.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HTML_RES = re.compile(
    r"<(?:script[^>]*\ssrc|img[^>]*\ssrc|link(?=[^>]*rel=\"?(?:stylesheet|preload|icon|modulepreload))[^>]*\shref)=\"(https?:)?//([^\"/]+)",
    re.I,
)
CSS_RES = re.compile(r"(?:url\(\s*['\"]?|@import\s+['\"])(https?:)?//([^'\")/]+)", re.I)
STYLESHEET = re.compile(r"<link[^>]*rel=\"?stylesheet[^>]*href=\"([^\"#?]+)", re.I)


def main(site: Path) -> int:
    found: list[str] = []
    css_files = set(site.rglob("*.css"))
    for f in site.rglob("*.html"):
        html = f.read_text(encoding="utf-8", errors="replace")
        for m in HTML_RES.finditer(html):
            found.append(f"{f.relative_to(site)}: {m.group(2)}")
        # таблицы стилей без расширения .css (так их иногда сохраняет privacy-плагин)
        for href in STYLESHEET.findall(html):
            if "//" not in href and (f.parent / href).is_file():
                css_files.add((f.parent / href).resolve())
    for f in sorted(css_files):
        for m in CSS_RES.finditer(f.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{f.resolve().relative_to(site.resolve())}: {m.group(2)}")
    for line in sorted(set(found)):
        print(f"external resource: {line}")
    print(f"checked {site}: {len(set(found))} external resource reference(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "site")))
