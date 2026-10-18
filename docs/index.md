# Задание 3. Генераторы статических сайтов для публикации результатов исследований

**Автор:** Кожухин Иван Алексеевич, группа P4155
**Курс:** PythEngin, ИТМО, 2026

Сайт — отчёт по заданию 3. Он сам является результатом работы: собран MkDocs Material в режиме `--strict`,
опубликован конвейером GitHub Actions одновременно на GitHub Pages и на Helios ИТМО.

<div class="grid cards" markdown>

-   :material-github: **GitHub Pages**

    ---

    <https://troublegale.github.io/ssg-report/>

    официальная связка `upload-pages-artifact` + `deploy-pages`

-   :material-server: **Helios ИТМО**

    ---

    <https://se.ifmo.ru/~s367293/ssg-report/>

    rsync по SSH с deploy-ключом, атомарные релизы, healthcheck, откат

-   :material-source-repository: **Репозиторий сайта**

    ---

    [troublegale/ssg-report](https://github.com/troublegale/ssg-report)
    · [workflow](https://github.com/troublegale/ssg-report/blob/main/.github/workflows/site.yml)
    · [запуски](https://github.com/troublegale/ssg-report/actions)

-   :material-puzzle: **GitHub Action для Helios**

    ---

    [troublegale/helios-deploy-action](https://github.com/troublegale/helios-deploy-action)
    — челлендж

</div>

[![site](https://github.com/troublegale/ssg-report/actions/workflows/site.yml/badge.svg)](https://github.com/troublegale/ssg-report/actions/workflows/site.yml)
[![action tests](https://github.com/troublegale/helios-deploy-action/actions/workflows/test.yml/badge.svg)](https://github.com/troublegale/helios-deploy-action/actions/workflows/test.yml)

## Состав отчёта

| Раздел | Содержание |
|---|---|
| [Ход работы](hod-raboty.md) | окружение `uv`, каркас MkDocs, `--strict`, два способа публикации на Pages, Helios, базовый URL, проверка результата, лицензии |
| [T1. Сравнение SSG](t1.md) | исследовательское задание: MkDocs Material, Sphinx + MyST, Pelican, Quarto — матрица, замеры, вывод |
| [P4. Деплой на Helios](p4.md) | практическое задание: deploy-ключ, healthcheck, превью веток, откат, обрыв выкладки, сравнение с Pages |
| [Челлендж](challenge.md) | composite action `helios-deploy-action`: параметры, тесты, версии, Marketplace |
| [Отладка](otladka.md) | семь реальных ошибок: текст, гипотеза, проверка, решение |
| [Вывод](vyvod.md) | рекомендуемый стек и условия, при которых рекомендация меняется |
| [Лицензии](licenses.md) | CC BY 4.0 на текст, MIT на код, лицензии вендорных ресурсов |

!!! tip "Метка версии"
    Внизу каждой страницы указаны коммит, ветка, время сборки и площадка (`pages` или `helios`).
    Тот же коммит записан в `<meta name="ssg-build-commit">` — по нему healthcheck проверяет, что опубликована именно новая сборка.
