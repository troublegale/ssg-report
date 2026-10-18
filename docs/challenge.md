# Челлендж: GitHub Action для Helios ИТМО

**Репозиторий:** [troublegale/helios-deploy-action](https://github.com/troublegale/helios-deploy-action)
· **Marketplace:** [Helios ITMO Static Deploy](https://github.com/marketplace/actions/helios-itmo-static-deploy)
· **Используется в:** [troublegale/ssg-report](https://github.com/troublegale/ssg-report/blob/main/.github/workflows/site.yml) (этот сайт)

[![test](https://github.com/troublegale/helios-deploy-action/actions/workflows/test.yml/badge.svg)](https://github.com/troublegale/helios-deploy-action/actions/workflows/test.yml)

## Требования и их выполнение

| Требование | Реализация |
|---|---|
| composite или Docker-action, корректный `action.yml` | composite (`runs.using: composite`), один шаг `bash deploy.sh`; `inputs` (20), `outputs` (`release`, `previous-release`, `duration`), `description`, `branding` (`upload-cloud`, `blue`) |
| параметры: хост, путь назначения, исходный каталог, ключ, `--delete` | `host` (по умолчанию `helios.cs.ifmo.ru`), `port` (`2222`), `target`, `source`, `ssh-key`, `delete` |
| README с примером и совместимостью | [README](https://github.com/troublegale/helios-deploy-action#readme): примеры выкладки и отката, таблица параметров, совместимость (Linux/macOS-раннеры, FreeBSD/Linux-серверы), безопасность |
| семантическое версионирование, подвижный мажорный тег | теги `v1.0.0` и `v1` (для v1.0.0 поставлен вручную); со следующего релиза `vX.Y.Z` тег `vX` переносит workflow `major-tag.yml` — на v1.0.0 он не сработал, так как событие `release` берёт workflow из коммита тега, а там его ещё не было |
| лицензия, публикация, реальный репозиторий-потребитель | MIT; [Marketplace](https://github.com/marketplace/actions/helios-itmo-static-deploy) (релиз 1.0.0, категория Deployment); используется этим сайтом, закреплён по SHA: `troublegale/helios-deploy-action@c68696c… # v1.0.0` |

## Возможности сверх обязательных

- `strategy: atomic` — релизы и атомарное переключение симлинка, `keep-releases`, `--link-dest` (см. [P4](p4.md#атомарные-релизы));
- `mode: rollback | status | remove`;
- healthcheck с контрольной строкой и автооткатом, `healthcheck-from: remote` на случай недоступности хостинга из сети раннера;
- `shared-dirs` — каталоги, переживающие переключение релизов (на них построены превью веток);
- известный ключ хоста Helios закреплён в action: проверка хоста не отключается, а для чужих хостов `known-hosts` обязателен;
- проверка путей на допустимые символы и отсутствие `..` до подстановки в удалённую команду.

## Тестирование

Workflow [`test.yml`](https://github.com/troublegale/helios-deploy-action/blob/main/.github/workflows/test.yml):
`shellcheck` и интеграционный тест `tests/integration.sh`, который поднимает `sshd` и HTTP-сервер на самом раннере и прогоняет
сценарии. Те же сценарии запускались локально в контейнере `ubuntu:24.04`; на FreeBSD (Helios) action проверен реальными
выкладками этого сайта.

```text
PASS deploy v1 (20261018T213938Z-1111111)
PASS deploy v2 (20261018T213940Z-2222222)
PASS shared dir preview/ сохранился
PASS previous-release = 20261018T213938Z-1111111
PASS link-dest: hardlink
PASS rollback -> 20261018T213938Z-1111111
PASS rollback-to 20261018T213940Z-2222222
PASS healthcheck fail -> автооткат на 20261018T213940Z-2222222
PASS rollback пропускает провалившийся релиз
PASS без known-hosts — отказ
PASS path traversal отклонён
PASS direct --delete
PASS keep-releases=2 (2 релиза)
PASS status показывает активный релиз
PASS remove
все сценарии пройдены
```

Два из этих сценариев появились после реальных ошибок: [E3](otladka.md#e3) и [E4](otladka.md#e4).

## Пример использования

```yaml
- uses: troublegale/helios-deploy-action@v1
  with:
    username: s367293
    ssh-key: ${{ secrets.HELIOS_SSH_KEY }}
    source: site
    target: public_html/my-site
    healthcheck-url: https://se.ifmo.ru/~s367293/my-site/
    healthcheck-contains: ${{ github.sha }}
```

## Исходный код

- [`action.yml`](https://github.com/troublegale/helios-deploy-action/blob/v1.0.0/action.yml) — интерфейс action;
- [`deploy.sh`](https://github.com/troublegale/helios-deploy-action/blob/v1.0.0/deploy.sh) — реализация (bash на раннере, POSIX `sh` на сервере);
- [`tests/integration.sh`](https://github.com/troublegale/helios-deploy-action/blob/v1.0.0/tests/integration.sh) — интеграционный тест.
