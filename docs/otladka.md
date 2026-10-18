# Отладка

Ниже — все реальные ошибки, возникшие при выполнении работы, в порядке появления. Для каждой: текст ошибки, гипотеза,
способ проверки и решение. Ошибки E4–E7 найдены благодаря проверкам, которые требует задание (healthcheck, откат,
проверка внешних ресурсов), — без них они остались бы незамеченными.

| # | Где | Кратко | Обнаружено |
|---|---|---|---|
| [E1](#e1) | локальная сборка | `--strict` падает из-за плагина дат без git-истории | `mkdocs build --strict` |
| [E2](#e2) | Helios | сервер закрывает соединения, затем блокирует IP на всех портах | `ssh -v`, `curl` |
| [E3](#e3) | action | `rsync --link-dest` не создаёт жёстких ссылок | интеграционный тест |
| [E4](#e4) | action | ручной откат возвращает релиз, проваливший healthcheck | демонстрация отката |
| [E5](#e5) | workflow | удаление двух веток одним push убирает только одно превью | `gh run list -e delete` |
| [E6](#e6) | CI | плавающий таймаут загрузки шрифта валит `--strict` | красный запуск `main` |
| [E7](#e7) | сайт | шрифты снова грузятся с `fonts.gstatic.com` (регрессия после E6) | замер веса страницы |

## E1. Плагин дат без git-истории { #e1 }

**Текст ошибки** (первая локальная сборка):

```text
WARNING -  mkdocs_git_revision_date_localized_plugin: Unable to read git logs of
'C:\Users\User\Home\itmo-python\task3\ssg-report\docs'. Is git log readable?
Option 'fallback_to_build_date' set to 'true': Falling back to build date
Aborted with 1 warnings in strict mode!
```

**Гипотеза.** Плагин берёт дату изменения страницы из `git log`; репозиторий только что создан (`git init`), коммитов нет.
Предупреждение безобидно, но `--strict` превращает его в ошибку.

**Проверка.** `git log` → `fatal: your current branch 'main' does not have any commits yet`.

**Решение.** Первый коммит — и сборка проходит. В CI та же проблема возникла бы при поверхностном клоне
(`actions/checkout` по умолчанию делает `fetch-depth: 1` — все страницы получили бы дату последнего коммита),
поэтому в workflow указано `fetch-depth: 0`.

## E2. Helios блокирует IP { #e2 }

**Текст ошибки.** После нескольких `ssh-keyscan` и серии SSH-команд подряд:

```text
$ ssh -v -p 2222 s367293@helios.cs.ifmo.ru 'echo ok'
debug1: Connecting to helios.cs.ifmo.ru [77.234.196.4] port 2222.
debug1: Connection established.
debug1: Local version string SSH-2.0-OpenSSH_10.3
kex_exchange_identification: Connection closed by remote host
```

а затем и `curl https://se.ifmo.ru/~s367293/` → `schannel: failed to receive handshake, SSL/TLS connection failed`.

**Гипотеза 1.** `PerSourcePenalties` в OpenSSH ≥ 9.8 (на сервере OpenSSH 10.0): `ssh-keyscan` открывает соединения без
аутентификации (по одному на тип ключа, трижды по три), sshd штрафует источник. **Опровергнута:** штраф sshd не мог
бы закрыть HTTPS — порт 443 обслуживает другой процесс.

**Гипотеза 2.** Сетевая защита от перебора на уровне хоста (вида sshguard/blacklistd + пакетный фильтр) заблокировала IP
на всех портах. **Проверка:** тот же URL с телефона через мобильный интернет (другой IP) открывается; с раннеров GitHub
выкладка и healthcheck проходят; с исходного IP блок держится больше часа на SSH и на HTTPS.

**Решение.** Для работы — продолжать через CI (раннеры имеют другие адреса) и не опрашивать сервер циклом: каждая
попытка соединения во время блокировки может его продлевать. Для пайплайна — выводы:

- `ssh-keyscan` к Helios выполнять один раз и сохранять результат в переменную репозитория, а не в каждом запуске;
- action делает ровно 3 SSH-сеанса на выкладку и не повторяет неудачные соединения в цикле;
- healthcheck можно перенести на сервер (`healthcheck-from: remote`), если хостинг недоступен из сети раннера.

## E3. `rsync --link-dest` не создаёт жёстких ссылок { #e3 }

**Текст ошибки.** Интеграционный тест action (Ubuntu 24.04 в Docker):

```text
PASS previous-release = 20261018T210424Z-1111111
FAIL link-dest
```

проверка `stat -c %h releases/<R2>/sub/a.txt` вернула `1` — файл скопирован, а не связан с предыдущим релизом.

**Гипотеза.** С флагом `-t` rsync при `--link-dest` считает файлы одинаковыми, только если совпадают и размер,
и **время изменения**. Тест (как и `mkdocs build`) каждый раз пересоздаёт все файлы — время всегда новое.

**Проверка.** Убрал `-t` и включил сравнение по контрольной сумме (`-c`) — тот же тест: `PASS link-dest: hardlink`.

**Решение.** В режиме `atomic` — `rsync -rlzc` (без сохранения времени, сравнение по содержимому). Бонус: `--link-dest`
одновременно служит базой для дельта-передачи — при повторной выкладке передаются килобайты (см. [P4](p4.md#атомарные-релизы)).

## E4. Откат вернул провалившийся релиз { #e4 }

**Текст ошибки.** После демонстрации провала healthcheck (запуск
[39168536318](https://github.com/troublegale/ssg-report/actions/runs/39168536318), автооткат на `…213306Z-bff9053`)
ручной откат ([39168691545](https://github.com/troublegale/ssg-report/actions/runs/39168691545)) показал:

```text
##[notice]откат: 20261018T213306Z-bff9053 -> 20261018T213647Z-bff9053
```

`213647Z` — тот самый релиз, который не прошёл healthcheck.

**Гипотеза.** Откат выбирает «последний релиз из журнала активаций, отличный от текущего». Провалившийся релиз был
активирован (healthcheck выполняется **после** переключения), попал в журнал, его каталог остался на диске.

**Проверка.** `action: status`, журнал активаций: `…213306Z`, `…213647Z`, `…213306Z` — гипотеза подтвердилась.
Ущерба не было (оба релиза собраны из одного коммита, «сломана» была только ожидаемая строка), но в реальном сценарии
откат вернул бы сломанный сайт.

**Решение.** При автооткате каталог провалившегося релиза удаляется; откат пропускает релизы без каталога. В
интеграционный тест добавлен сценарий «ручной откат после автоотката» (`PASS rollback пропускает провалившийся релиз`).
Заодно исправлена очистка: старые релизы отбираются только среди каталогов с меткой времени, служебные `legacy-*` не сбивают счёт.

## E5. Удаление двух веток — одно превью осталось { #e5 }

**Текст ошибки.** `git push origin --delete demo/interrupt demo/broken-link`, затем:

```text
$ gh run list -e delete
completed  success    site  main  delete  39170103166
completed  cancelled  site  main  delete  39170102952
```

Отменённый запуск относился к `demo/interrupt` — его превью осталось на сервере.

**Гипотеза.** Для события `delete` `github.ref` — это ветка по умолчанию, поэтому concurrency-группа
`site-${{ github.event_name == 'delete' && 'delete' || github.ref }}` одна для всех удалений, а `cancel-in-progress: true`
отменяет предыдущий запуск.

**Проверка.** В логах двух запусков `BRANCH: demo/interrupt` (cancelled) и `BRANCH: demo/broken-link` (success).

**Решение.** Группа `site-delete-<удаляемая ветка>`: `format('delete-{0}', github.event.ref)`. Повторное удаление
`demo/interrupt` ([39170183467](https://github.com/troublegale/ssg-report/actions/runs/39170183467)) превью убрало.

## E6. Плавающий таймаут загрузки шрифта { #e6 }

**Текст ошибки** (запуск [39170153650](https://github.com/troublegale/ssg-report/actions/runs/39170153650), job `lint`;
предыдущие восемь запусков были зелёными):

```text
WARNING -  Couldn't retrieve https://fonts.gstatic.com/s/robotomono/v31/L0x5DF4xlVMF-BfR8bXMIjhLq38.woff2:
HTTPSConnectionPool(host='fonts.gstatic.com', port=443): Read timed out. (read timeout=5)
Aborted with 1 warnings in strict mode!
```

**Гипотеза.** Privacy-плагин при каждой сборке скачивает ~30 файлов шрифтов с таймаутом 5 с. В job `lint` кэш
`.cache` не восстанавливался (он был только в `build`), поэтому каждая проверка зависела от внешней сети.

**Проверка.** В логе — серия `Downloading external file: …` перед ошибкой; в job `build` с кэшем этих строк нет.

**Решение.** Сделать сборку **герметичной**: кэш плагина перенесён в репозиторий (`privacy.cache_dir: vendor-cache/privacy`),
шаг `actions/cache` удалён. Локальная сборка с пустым `.cache` больше не скачивает шрифты. Это решение породило E7.

## E7. Шрифты снова с `fonts.gstatic.com` { #e7 }

**Текст ошибки.** При подсчёте веса страницы выяснилось, что файл стилей шрифтов в собранном сайте лежит **без расширения**
и ссылается на внешний хост — и так же на опубликованном Pages:

```text
$ grep -o "url([^)]*)" site/assets/external/fonts.googleapis.com/css.49ea35f2 | head -1
url(https://fonts.gstatic.com/s/roboto/v51/KFO5CnqEu92Fr1Mu53ZEC9_Vu3r1gIhOszmkC3kaWzU.woff2)
```

**Гипотеза.** Регрессия после E6. В артефакте запуска до переноса кэша
([39169837011](https://github.com/troublegale/ssg-report/actions/runs/39169837011)) файл назывался `css.49ea35f2.css`
и содержал `url(../fonts.gstatic.com/…)` — то есть всё работало. Кэш в репозиторий я положил с Windows.

**Проверка.** Код плагина (`material/plugins/privacy/plugin.py`): для URL без расширения (`…/css?family=…`) файл
сохраняется с расширением по Content-Type, а рядом создаётся **симлинк** без расширения (`os.symlink`), на Windows создание
симлинка не удаётся. В закоммиченном кэше симлинка нет → на CI файл определяется без расширения → `_parse_media()`
пропускает его (расширения нет в `assets_expr_map`) → `url()` внутри не переписываются.

**Решение.**

1. Шрифты подключены вручную: `theme.font: false` и `docs/assets/stylesheets/fonts.css` с `@font-face` для 8 вариативных
   woff2 (Roboto и Roboto Mono, обычное и курсив, только кириллица и латиница) — 240 КБ вместо 4,3 МБ всех поднаборов.
   В кэше privacy-плагина остались только `.js`-файлы, которым симлинки не нужны.
2. **Регрессионная проверка** `scripts/check_no_external.py` в job `lint`: на сломанном артефакте
   ([39170303657](https://github.com/troublegale/ssg-report/actions/runs/39170303657)) она находит
   `assets/external/fonts.googleapis.com/css.49ea35f2: fonts.gstatic.com`, на текущей сборке — 0 внешних ресурсов.
