# ssg-report

[![site](https://github.com/troublegale/ssg-report/actions/workflows/site.yml/badge.svg)](https://github.com/troublegale/ssg-report/actions/workflows/site.yml)

Отчёт по заданию 3 «Генераторы статических сайтов для публикации результатов исследований» (PythEngin, ИТМО).
Автор: Кожухин Иван Алексеевич, P4155.

- GitHub Pages: <https://troublegale.github.io/ssg-report/>
- Helios ИТМО: <https://se.ifmo.ru/~s367293/ssg-report/>
- Action для Helios: <https://github.com/troublegale/helios-deploy-action>

## Сборка

```bash
uv sync
uv run mkdocs serve            # предпросмотр
uv run mkdocs build --strict   # как в CI
uv run python scripts/check_no_external.py site
```

## Публикация

`.github/workflows/site.yml`: `lint → build (pages, helios) → deploy-pages (main) | deploy-helios (все ветки)`.
Ветка `X` публикуется на Helios в `…/ssg-report/preview/X/`. Ручные действия: `Actions → site → Run workflow`
(`deploy`, `rollback`, `status`).

Секреты и переменные: `HELIOS_SSH_KEY` (secret, deploy-ключ), `HELIOS_KNOWN_HOSTS` (variable).

## Лицензии

Текст — CC BY 4.0 (`LICENSE-CONTENT`), код — MIT (`LICENSE`).
