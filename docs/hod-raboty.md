# Ход работы

## 1. Python, менеджер пакетов, виртуальное окружение

Вместо связки `pip` + `virtualenv` использован [uv](https://docs.astral.sh/uv/) — он создаёт виртуальное окружение,
ставит пакеты и пишет lock-файл. Версия Python закреплена в `.python-version`.

```console
$ python --version
Python 3.14.7
$ uv --version
uv 0.13.1 (62faed335 2026-10-13 x86_64-pc-windows-msvc)
$ uv init --bare --name ssg-report --python 3.12 ssg-report
$ cd ssg-report && uv python pin 3.12
$ uv add mkdocs-material "mkdocs>=1.6" pymdown-extensions mkdocs-git-revision-date-localized-plugin
$ uv add --group dev codespell linkchecker
```

`uv` сам создаёт `.venv/` и использует его в `uv run …`, явная активация окружения не нужна
(при необходимости — `.venv\Scripts\activate` или `source .venv/bin/activate`).

## 2. Зависимости и `.gitignore`

Версии зафиксированы дважды: точные `==` в `pyproject.toml` и полный граф с хешами в `uv.lock`.
В CI используется `uv sync --locked` — сборка падает, если lock-файл не соответствует `pyproject.toml`.

```toml title="pyproject.toml (фрагмент)"
--8<-- "pyproject.toml:9:20"
```

```gitignore title=".gitignore"
--8<-- ".gitignore"
```

## 3. Каркас сайта MkDocs

Структура репозитория:

```text
ssg-report/
├── docs/                       # Markdown-страницы и ассеты сайта
│   ├── assets/fonts/           # Roboto, Roboto Mono (только кириллица+латиница)
│   ├── assets/vendor/mathjax/  # MathJax 3.2.2 — не с CDN
│   └── *.md
├── overrides/main.html         # переопределение шаблона Material (метка версии, <meta>)
├── hooks/build_info.py         # хук MkDocs: коммит, ветка, дата, площадка
├── scripts/check_no_external.py# проверка «нет ресурсов со сторонних CDN»
├── vendor-cache/privacy/       # кэш privacy-плагина (герметичная сборка)
├── bench/                      # стенд сравнения генераторов для T1
├── mkdocs.yml
├── pyproject.toml, uv.lock, .python-version
└── .github/workflows/site.yml
```

Ключевые решения в `mkdocs.yml`:

- `strict: true` и раздел `validation` — битые ссылки, якоря и неизвестные страницы становятся ошибками;
- `theme.custom_dir: overrides` — частичное переопределение шаблона без форка темы (блоки `extrahead` и `footer`);
- `hooks: [hooks/build_info.py]` — метаданные сборки без отдельного плагина;
- `theme.font: false` + собственный `fonts.css`, MathJax из репозитория, плагин `privacy` для остальных внешних
  ресурсов — страница не делает ни одного запроса к сторонним хостам (см. п. 9);
- `search: lang: [ru, en]` — стемминг русского языка в поиске.

## 4. Локальная сборка

```console
$ uv run mkdocs serve          # предпросмотр на http://127.0.0.1:8000/
$ uv run mkdocs build --strict
INFO    -  Documentation built in 4.55 seconds
```

Режим `--strict` дал первую же реальную ошибку — предупреждение плагина дат при отсутствии коммитов, см. [Отладка, E1](otladka.md#e1).

## 5. Репозиторий на GitHub

```console
$ git init -b main
$ git remote add origin https://github.com/troublegale/ssg-report.git
$ git push -u origin main
```

Pages переключены на источник «GitHub Actions» (Settings → Pages → Source), то же через API:
`gh api -X POST repos/troublegale/ssg-report/pages -f build_type=workflow`.

## 6. GitHub Actions: два способа публикации на Pages

| | `peaceiris/actions-gh-pages` (push в ветку `gh-pages`) | `actions/upload-pages-artifact` + `actions/deploy-pages` |
|---|---|---|
| Источник Pages | ветка `gh-pages` | «GitHub Actions» |
| Что делает | коммитит собранный `site/` в ветку и пушит её | упаковывает `site/` в tar-артефакт, отдельный job разворачивает его |
| Права токена | `contents: write` — запись в **любую** ветку репозитория | `pages: write` + `id-token: write` (OIDC), **без** записи в код |
| История выкладок | коммиты в `gh-pages`, откат — `git revert` | environment `github-pages`, откат — перезапуск старого workflow |
| Защита | нет специальной, только защита веток | правила environment (ветки, ревьюеры), артефакт привязан к запуску |
| Минусы | рост репозитория, сторонний action с правом записи | нельзя посмотреть содержимое выкладки в git |

Стартовый шаблон GitHub «Static HTML» (Settings → Pages → GitHub Actions) — это та же официальная связка
`configure-pages` + `upload-pages-artifact` + `deploy-pages`; job `deploy-pages` этого сайта построен по нему, а `deploy-helios` —
его аналог для отечественной площадки: тот же артефакт сборки, но доставка по SSH.

Выбрана официальная связка: у job публикации нет права менять код, а компрометация стороннего action не даёт
возможности переписать `main`. Собирает сайт отдельный job `build`, публикует — `deploy-pages`.

## 7. Helios ИТМО

Аккаунт `s367293` активен, вход — `ssh -p 2222 s367293@helios.cs.ifmo.ru`, статика раздаётся из `~/public_html` по адресу
`https://se.ifmo.ru/~s367293/`. Сервер: FreeBSD 14.5, OpenSSH 10.0, rsync 3.4.1 — всё нужное для выкладки есть.
Отдельно проверено, что Apache следует симлинкам (тестовый каталог-симлинк в `public_html` отдался с кодом 200) —
на этом построены атомарные релизы (см. [P4](p4.md)).

## 8. Workflow под две площадки

Один workflow, стадии `lint → build (matrix: pages, helios) → deploy-pages | deploy-helios`. Полный текст с комментариями:

??? example "`.github/workflows/site.yml`"
    ```yaml
    --8<-- ".github/workflows/site.yml"
    ```

## 9. Базовый URL

| Параметр | Значение | Зачем |
|---|---|---|
| `site_url` | `!ENV [SITE_URL, "https://troublegale.github.io/ssg-report/"]` | канонические ссылки, `sitemap.xml`; в CI задаётся для каждой площадки и каждого превью |
| `use_directory_urls` | `true` | адреса вида `p4/`; MkDocs пишет **относительные** ссылки (`../t1/`), поэтому один и тот же HTML работает в корне домена и в подкаталоге |
| абсолютные ссылки в Markdown | запрещены (`validation.links.absolute_links: warn` + `strict`) | ссылка `/t1/` вела бы на `troublegale.github.io/t1/` и `se.ifmo.ru/t1/` — мимо сайта на обеих площадках |

Типичная ошибка «работает на Pages, ломается на Helios» возникает от абсолютных путей: сайт на Pages лежит в `/ssg-report/`,
на Helios — в `/~s367293/ssg-report/`, в превью — ещё глубже (`/~s367293/ssg-report/preview/<ветка>/`). Аналогично
`mathjax-config.js` вычисляет путь к MathJax от адреса собственного скрипта, а не от корня сайта.

## 10. Проверка результата не только визуально { #proverka }

После каждой выкладки CI выполняет проверки (в job `deploy-pages` и в action/шаге smoke-теста `deploy-helios`):

| Проверка | Как | Результат (запуск [39170303657](https://github.com/troublegale/ssg-report/actions/runs/39170303657)) |
|---|---|---|
| Код ответа HTTP | `curl -w '%{http_code}'` | 200 на `/`, `/t1/`, `/p4/`, `search/search_index.json`, MathJax |
| Контрольная строка в HTML | ищется SHA коммита из `<meta name="ssg-build-commit">` | найдено с 1-й попытки на обеих площадках |
| Поиск | индекс `search/search_index.json` доступен, `"lang":["ru","en"]` | OK |
| Формулы без CDN | MathJax запрашивается с самой площадки; `scripts/check_no_external.py` — 0 внешних ресурсов | OK |

Пример формулы, которая должна отрисоваться без доступа к CDN — модель времени доставки на Helios из [P4](p4.md):

$$
T_\text{доставки} = n_\text{ssh}\,t_\text{ssh} + \frac{S_\Delta}{B} + t_\text{switch} + t_\text{hc}
\label{eq:delivery}
$$

где $n_\text{ssh}$ — число SSH-сеансов (3), $S_\Delta$ — объём изменённых данных, $B$ — пропускная способность канала.
Из \eqref{eq:delivery} видно, почему при `rsync --link-dest` время почти не зависит от размера сайта: $S_\Delta$ мал.

Независимость от внешней сети проверяется двумя способами: статически — скриптом `scripts/check_no_external.py`
в каждом запуске CI (ищет внешние URL в `<script src>`, `<link href>`, `<img src>` и `url()` всех таблиц стилей),
и в браузере — по списку сетевых запросов опубликованной страницы (см. ниже).

### Вес страницы: CDN против локальных ресурсов { #ves }

Замер по собранному `site/`: HTML страницы + подключённые CSS/JS + шрифты, которые браузер загрузит для русского текста
(Roboto normal, кириллица и латиница); gzip — уровень 6. Вариант «CDN» собран из того же исходника с настройками Material
по умолчанию (Google Fonts) и MathJax с jsDelivr.

| Вариант | Внешних хостов | Без формул (главная), КБ: raw / gzip | С формулами (эта страница), КБ: raw / gzip |
|---|---:|---:|---:|
| CDN: Google Fonts + MathJax с jsDelivr на каждой странице | 2 (+ запросы woff2 с `fonts.gstatic.com`) | 292 / 68 с сайта **+ ≈ 2 120 / 620 со сторонних хостов** | 385 / 81 с сайта **+ ≈ 2 120 / 620 со сторонних** |
| Локально, MathJax на каждой странице (первая версия сайта) | 0 | 2 408 / 802 | 2 450 / 812 |
| **Локально, MathJax только на страницах с формулами (текущая)** | **0** | **360 / 134** | 2 512 / 818 |

Вывод: перенос ресурсов на сайт сам по себе не утяжеляет страницу — те же ≈ 2,1 МБ раньше загружались со сторонних хостов.
Утяжеляло другое: MathJax подключался на всех страницах. После ленивой загрузки страница без формул весит
в 6,7 раза меньше (360 против 2 408 КБ), а страница с формулами — столько же, сколько с CDN, но без внешних запросов.
Цена — 240 КБ шрифтов в репозитории и 2 МБ MathJax, которые надо обновлять вручную.

## 11. Лицензии

Раздельно: текст — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ru), код — MIT (файл `LICENSE`),
подробности и лицензии вендорных ресурсов — на странице [Лицензии](licenses.md).

## 12. Отладка

Семь реальных ошибок с разбором — на странице [Отладка](otladka.md).
