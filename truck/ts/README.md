# Truck — TypeScript index module (`truck/ts`)

`@asombi/truck-index` — вынесенный на **TypeScript** индекс-модуль пакетного
менеджера Truck. Порт самых критичных частей `truck/core/utils.py`:

| Функция Python | Экспорт TS | Назначение |
|---|---|---|
| `_parse_toml_index` | `parseTomlIndex` | парсер TOML-индексов (оба формата секций) |
| `fetch_all_packages` | `fetchAllPackages` | загрузка AsomPacket + Asombi индексов |
| `_ver_key` | `versionKey` / `isNewer` | численное сравнение версий (0.24.0 > 0.9.0) |
| `select_version` | `selectVersion` | выбор версии: `name@ver` → max из `name-*` → голая секция |
| `crates_lookup` / `resolve_package` | `cratesLookup` / `resolvePackage` | fallback на crates.io (с sha256) |
| `cmd_search` + `crates_io_search` | `searchPackages` / `cratesIoSearch` | поиск по индексам и crates.io |

Особенности:
* **0 runtime-зависимостей** — только Node.js ≥ 18 (глобальный `fetch`).
* Строгая типизация (`strict`), публичные `.d.ts`.
* Используется как библиотека (для будущего TUI/веб-фронтенда Asombi)
  и как read-only CLI `trk-ts`.

## Сборка и тесты

```bash
cd truck/ts
npm install          # dev-зависимости: typescript, @types/node
npm run build        # tsc -> dist/
npm test             # node --test: 10 тестов, включая разбор живого
                     # AsomPacket/index.toml (4260+ записей)
```

Эквивалентность Python-ядру проверена кросс-запуском: для `ripgrep`,
`bat`, `ripgrep@14.1.1` обе реализации выбирают один и тот же slug/версию.

## CLI

```bash
node dist/cli.js stats               # размер индексов по репозиториям
node dist/cli.js versions ripgrep    # все версии + выбранная по умолчанию
node dist/cli.js info bat            # инфо (резолвер максимальных версий)
node dist/cli.js info ripgrep@14.1.1 # явная версия
node dist/cli.js info cargo-expand   # crates.io fallback + sha256
node dist/cli.js search "cat clone"  # поиск (+ crates.io если пусто)
```

## Как это связано с планом миграции Truck

См. [docs/truck-migration.md](../../docs/truck-migration.md):
TypeScript закрывает слой «индекс/поиск/резолвинг/UI», C++/Rust —
слои скачивания/распаковки/сборки. Python-ядро остаётся совместимым
до завершения миграции; модуль читает те же форматы индексов, что и trk.
