"""Бенчмарк SSG для T1: одинаковый контент (N страниц) → MkDocs Material, Sphinx+MyST, Pelican, Quarto.

Замеряется: холодная сборка (чистый каталог вывода и кэш), инкрементальная сборка (изменён 1 файл),
объём и число файлов результата. Каждая сборка повторяется REPEAT раз, берётся медиана.
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent / "work"
N = int(os.environ.get("BENCH_PAGES", "30"))
REPEAT = int(os.environ.get("BENCH_REPEAT", "3"))

PAGE = """# Эксперимент {i}

Регрессионный анализ результатов серии {i}. Измерения проводились на стенде с
фиксированной температурой; оценка параметров выполнена методом наименьших квадратов.

## Модель

$$
\\hat\\beta = (X^\\top X)^{{-1}} X^\\top y
$$

Ошибка оценивается как $\\sigma^2 = \\frac{{1}}{{n-p}}\\sum_i (y_i - \\hat y_i)^2$.

## Результаты

| Серия | n | R² | RMSE |
|-------|---|----|------|
| {i}.1 | 120 | 0.93 | 1.12 |
| {i}.2 | 240 | 0.95 | 0.98 |
| {i}.3 | 480 | 0.96 | 0.91 |

## Код

```python
import numpy as np

def fit(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]
```

Сноска к результату[^1].

[^1]: Данные серии {i} доступны в репозитории.
"""


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def pages() -> dict[str, str]:
    d = {f"exp{i:02d}.md": PAGE.format(i=i) for i in range(1, N + 1)}
    d["index.md"] = "# Результаты экспериментов\n\n" + "\n".join(
        f"- [Эксперимент {i}](exp{i:02d}.md)" for i in range(1, N + 1)
    ) + "\n"
    return d


def setup_mkdocs(base: Path) -> None:
    for name, text in pages().items():
        write(base / "docs" / name, text)
    write(base / "mkdocs.yml", """site_name: Bench
theme:
  name: material
  language: ru
plugins:
  - search:
      lang: [ru, en]
markdown_extensions:
  - footnotes
  - tables
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.highlight
  - pymdownx.superfences
""")


def setup_sphinx(base: Path) -> None:
    for name, text in pages().items():
        if name == "index.md":
            text += "\n```{toctree}\n:hidden:\n" + "\n".join(
                f"exp{i:02d}" for i in range(1, N + 1)) + "\n```\n"
        write(base / "src" / name, text)
    write(base / "src" / "conf.py", """project = "Bench"
language = "ru"
extensions = ["myst_parser", "sphinx.ext.mathjax"]
myst_enable_extensions = ["dollarmath", "amsmath"]
html_theme = "furo"
""")


def setup_pelican(base: Path) -> None:
    for name, text in pages().items():
        title = text.splitlines()[0].lstrip("# ")
        body = "\n".join(text.splitlines()[1:])
        slug = name.removesuffix(".md")
        write(base / "content" / "pages" / name, f"Title: {title}\nSlug: {slug}\n{body}")
    write(base / "content" / "post.md", "Title: Пост\nDate: 2026-10-01\n\nТекст.\n")
    write(base / "pelicanconf.py", """SITENAME = "Bench"
PATH = "content"
TIMEZONE = "Europe/Moscow"
DEFAULT_LANG = "ru"
MARKDOWN = {"extension_configs": {"markdown.extensions.extra": {}, "markdown.extensions.codehilite": {}}}
""")


def setup_quarto(base: Path) -> None:
    for name, text in pages().items():
        write(base / name.replace(".md", ".qmd"), text.replace(".md)", ".qmd)"))
    write(base / "_quarto.yml", """project:
  type: website
  output-dir: _site
website:
  title: Bench
  search: true
lang: ru
format:
  html:
    theme: cosmo
""")


ENV = {**os.environ, "PYTHONUTF8": "1"}
BIN = Path(sys.executable).parent

GENERATORS = {
    "MkDocs Material": dict(
        setup=setup_mkdocs, out="site", clean=["site"],
        cmd=[str(BIN / "mkdocs"), "build", "-q"], touch="docs/exp01.md"),
    "Sphinx + MyST": dict(
        setup=setup_sphinx, out="_build/html", clean=["_build"],
        cmd=[str(BIN / "sphinx-build"), "-q", "-b", "html", "src", "_build/html"], touch="src/exp01.md"),
    "Pelican": dict(
        setup=setup_pelican, out="output", clean=["output", "__pycache__"],
        cmd=[str(BIN / "pelican"), "-q", "content", "-o", "output", "-s", "pelicanconf.py"],
        touch="content/pages/exp01.md"),
    "Quarto": dict(
        setup=setup_quarto, out="_site", clean=["_site", ".quarto"],
        cmd=[str(BIN / "quarto"), "render", "--quiet"], touch="exp01.qmd"),
}


def run(cmd: list[str], cwd: Path) -> float:
    t = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.perf_counter() - t
    if r.returncode:
        raise RuntimeError(f"{cmd} failed:\n{r.stdout}\n{r.stderr}")
    return dt


def du(p: Path) -> tuple[int, int]:
    files = [f for f in p.rglob("*") if f.is_file()]
    return sum(f.stat().st_size for f in files), len(files)


def main() -> None:
    results = {}
    for name, g in GENERATORS.items():
        if name in os.environ.get("BENCH_SKIP", ""):
            continue
        base = ROOT / name.split()[0].lower()
        shutil.rmtree(base, ignore_errors=True)
        g["setup"](base)
        cold, inc = [], []
        for _ in range(REPEAT):
            for c in g["clean"]:
                shutil.rmtree(base / c, ignore_errors=True)
            cold.append(run(g["cmd"], base))
        for _ in range(REPEAT):
            f = base / g["touch"]
            f.write_text(f.read_text(encoding="utf-8") + "\nИзменение.\n", encoding="utf-8")
            inc.append(run(g["cmd"], base))
        size, count = du(base / g["out"])
        results[name] = {
            "cold_s": round(statistics.median(cold), 2),
            "incremental_s": round(statistics.median(inc), 2),
            "size_kb": round(size / 1024),
            "files": count,
        }
        print(name, results[name], flush=True)
    (Path(__file__).parent / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
