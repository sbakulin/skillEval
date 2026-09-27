# skillEval — скиллы NanoCast вместе с их эвалами

Репозиторий — источник истины для корпоративных скиллов. Отсюда агенты ставят
скиллы (Claude Code и Codex), и отсюда же скиллы регулярно переоцениваются.
Одобрение скилла — это коммит сюда; версия — git-тег `<скилл>--v<версия>`.

## Что где лежит

```
.claude-plugin/marketplace.json   маркетплейс Claude Code: один плагин на скилл
catalog.json                      индекс: скилл, версия, статус, последний вердикт, тег релиза
catalog/queries.json              запросы, сгенерированные reach query --adversarial по всему каталогу
reach.toml                        настройки skill-reach (ярусы 0 и 2), пороги гейта
plugins/<скилл>/
  .claude-plugin/plugin.json      манифест плагина (версия, где лежат эвалы)
  skills/<скилл>/SKILL.md         сам скилл — стандарт Agent Skills, один файл для Claude Code и Codex
  evals/cases.json                кейсы автора: запрос, должен ли сработать, ожидания  ← правим здесь
  evals/suite/…                   те же кейсы в формате claude plugin eval (генерируется)
  evals/reach-queries.json        срез catalog/queries.json про этот скилл (генерируется)
  evals/history/                  итоги прошлых прогонов
scripts/
  build_evals.py                  cases.json + catalog/queries.json → suite/ и reach-queries.json
  reeval.sh                       переоценка: ярус 0 lint, ярус 1 со скиллом/без, ярус 2 каталог
  summarize.py                    сводка прогона в Markdown
  install_codex.sh                разложить скиллы туда, где их ищет Codex
.github/workflows/skills.yml      на каждый push — бесплатные проверки; раз в неделю — переоценка
```

Сейчас в каталоге 7 скиллов: 5 опубликованных в NanoCast (`design-system`,
`data-access`, `writing-style`, `orbit-codes`, `orbit-codes-v2`) и 2 заявки
(`add-to-watchlist`, `release-notes`) со статусом `proposed` — они здесь как
примеры с полными эвалами, их последний прогон в NanoCast красный
(см. `evals/history/`).

## Эвалы скилла — три источника

| Файл | Кто написал | Что проверяет |
|---|---|---|
| `evals/cases.json` | автор скилла (агент в чате NanoCast через `propose_skill`) | работает ли скилл: срабатывает ли и что отвечает — судья проверяет каждое ожидание |
| `evals/reach-queries.json` → `should_fire` | `reach query draft` по телу скилла, имя замаскировано | те же вопросы, но сформулированные не автором — ловит «тесты, повторяющие текст скилла» |
| `evals/reach-queries.json` → `should_not_fire` | `reach query draft --adversarial` по описаниям **соседей** | похожие запросы, которые должны уйти другому скиллу — ловит перехват чужого |

`catalog/queries.json` хранит провенанс генерации: модель, дату и дайджест каждого
скилла на момент генерации. Изменился скилл — дайджест разошёлся, и
`reach query draft --sync` перегенерирует запросы только для изменённых.

## Как агент получает скилл

**Claude Code:**
```bash
claude plugin marketplace add sbakulin/skillEval
claude plugin install add-to-watchlist@nanocast
```

**Codex** (своего частного маркетплейса у Codex нет — кладём файлы):
```bash
git clone https://github.com/sbakulin/skillEval && cd skillEval
scripts/install_codex.sh                                      # себе, в ~/.agents/skills
scripts/install_codex.sh /etc/codex/skills add-to-watchlist--v0.1.0   # в образ агента, ровно по тегу
```

## Как переоценить

```bash
export ANTHROPIC_API_KEY=…
scripts/reeval.sh                          # всё: ~$8 на Sonnet
ONLY=add-to-watchlist RUNS=1 scripts/reeval.sh   # один скилл, дёшево
```

Результат — `results/<время>/SUMMARY.md` плюс сырые JSON каждого яруса.
Пороги — те же, что в гейте NanoCast: кейс проходит в ≥ 67 % прогонов со
скиллом, Δ > 0, recall ≥ 90 %, перехват ≤ 5 %.

В GitHub Actions проверки формы (`claude plugin validate`, актуальность
сгенерированных файлов, `reach lint`) идут на каждый push бесплатно.
Переоценка — по понедельникам и вручную (Actions → skills → Run workflow),
только если в секретах репозитория задан `ANTHROPIC_API_KEY`.

## Как меняется скилл

1. Правка `SKILL.md` или `evals/cases.json` → `python3 scripts/build_evals.py`.
2. Если менялось тело или описание — перегенерировать запросы:
   `reach query draft --target <каталог> --sync --adversarial` (см. `scripts/reeval.sh`, как собрать каталог).
3. `ONLY=<скилл> scripts/reeval.sh` → зелёный.
4. Поднять `version` в `plugin.json` и `marketplace.json`, влить, поставить тег
   `claude plugin tag plugins/<скилл>` → `<скилл>--v<версия>`.

Агенты закреплены на теге: новый тег ничего не меняет у работающих агентов,
пока их не перевели на него явно.

## Что уже найдено

`reach lint` на этом каталоге: `release-notes` и `writing-style` конкурируют
за одни слова («release notes»), а у `orbit-codes` и `orbit-codes-v2`
одинаковые описания. Это совпадает с тем, что прогон NanoCast увидел
вживую — оба скилла срабатывают одновременно.
