# План миграции Truck: Python → C++ / Rust / TypeScript

Дата аудита: 2026-10-23. Объект: `truck/core/*.py` (1281 строк) + `bin/trk`.

Truck написан на Python 3, потому что целевая среда — Termux/Android
(python есть из коробки). Но по мере роста (AsomPacket 4260+ версий,
crates.io fallback, локальные сборки) отдельные модули упираются в
ограничения интерпретатора: скорость парсинга больших индексов,
отсутствие нормальных типов, хрупкий самописный TOML-парсер.

## Текущее состояние модулей

| Модуль | Строк | Состояние | Вердикт |
|---|---:|---|---|
| `utils.py` | 354 | Рабочий, но: самописный TOML-парсер (ломается на стандартном TOML), ручной HTTP без ретраев, `_ver_key` не понимает суффиксы (`1.2.3-rc1`) | **Заменить → TypeScript** (готово: `truck/ts`) + позже Rust для скачиваний |
| `paths.py` | 93 | Простой, стабильный | Оставить (Python до конца миграции) |
| `install.py` | 198 | Логика ок; tar/zip распаковка через stdlib, нет параллельных загрузок, magic-bytes определение архива — ручное | **Заменить ядро → Rust** (`trk-core`: reqwest, tar-rs, zip, sha2) |
| `build.py` | 317 | Детект билд-систем через эвристики файлов; subprocess без таймаутов; `--disable-shared` ломает пакеты, нуждающиеся в .so | **Заменить → Rust** (схема как в cargo/benchcraft) или C++ (libarchive + POSIX) |
| `search.py` | 69 | Линейный поиск по 4272 записям — медленно и криво (ищет по slug целиком); дублирует crates-логику из utils | **Заменить → TypeScript** (готово: `searchPackages`, инвертированный индекс — next step) |
| `info.py` | 36 | OK | Заменен TS `resolvePackage` при переключении CLI |
| `update.py` | 58 | Сравнение версий через `!=` вместо числового (`0.9` «больше» `0.24`) — потенциальный баг | **Заменить → TS/Rust** (использует `versionKey`) |
| `remove.py` | 55 | Стабильный | Позже Rust (fs-операции) |
| `repo.py` | 60 | Стабильный | Позже TS (он уже умеет fetchIndexFromUrl) |
| `clean.py` / `list_pkg.py` | 41 | Тривиальные | Не требуют замены |
| `bin/trk` | 100 | Диспетчер команд | Переписать на обёртку над `trk-core` (Rust bin) + `trk-ts` |

## Что уже сделано

* **TypeScript-модуль `truck/ts` (`@asombi/truck-index`)** — порт
  `parseTomlIndex`, `fetchAllPackages`, `versionKey`, `selectVersion`,
  `cratesLookup`, `resolvePackage`, `searchPackages`. 10 unit-тестов,
  включая разбор живого AsomPacket-индекса; эквивалентность Python-ядру
  сверена кросс-запуском (ripgrep→15.2.0, bat→0.26.1, curl@7.85.0 — совпали).
  CLI `trk-ts`: search/info/versions/stats.

## Целевая архитектура

```
┌ trk (тонкий бинарь-диспетчер, Rust) ┐
│  ├─ слой данных/UI: truck/ts (TypeScript)   ← индекс, версии, поиск, future TUI
│  ├─ слой heavy-lifting: trk-core (Rust crate)
│  │    download (reqwest, параллельно, ретраи) → sha256 → unpack (tar/zip)
│  │    build orchestration (cargo/go/meson/cmake) c таймаутами и sandbox
│  └─ совместимость: truck/core (Python) — до полного перехода
└──────────────────────────────────────┘
```

Почему так:
* **Rust** — там, где нужны байты, файловая система, процессы и скорость
  (install/build/download/remove). Один статический бинарь вместо
  зависимости от python в rootfs Alpine/Termux.
* **C++** — альтернатива Rust для build-оркестратора, если потребуется
  линковка с libarchive/openssl из Alpine; решения сейчас нет — Rust
  предпочтительнее (единая экосистема с crates.io fallback).
* **TypeScript** — индекс/резолвинг/поиск и будущий интерфейс
  (TUI через ink / веб-консоль Asombi): быстрая итерация, типы, 0 deps.

## Порядок миграции (предлагаемый)

1. ✅ `truck/ts` — индекс-ядро (готово, покрыто тестами).
2. 🔜 Подключить trk-ts к `trk search|info|versions|repo list`
   (вызывать node из Python-обёртки; если node нет — текущий путь).
3. 🔜 Rust `trk-core`: download+sha256+unpack; замена тела install.py.
4. 🔜 Rust build-оркестратор (замена build.py) + `trk link`.
5. 🔜 `bin/trk` → Rust-диспетчер; Python остаётся legacy-fallback.
6. ❌ Не мигрировать: paths/clean/list (нет смысла до шага 5).

## Известные технические долги (найти/починить при миграции)

* Самописный TOML: переход на `toml` (Rust) / `smol-toml` (TS planned).
* `_ver_key` игнорирует пре-релизы (`-rc`, `-beta`).
* Нет ретраев/зеркал при скачивании; таймаут 15/120 c захардкожен.
* `update.py`: сравнение `current != latest` вместо `isNewer`.
* Кэш индексов отсутствует на диске (каждый вызов = сеть).
