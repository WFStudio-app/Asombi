/**
 * Truck (Asombi OS) — index core на TypeScript.
 *
 * Порт критичных частей truck/core/utils.py:
 *   - парсер TOML-индексов (оба формата: [packages.curl] и [packages.curl-8.9.1]);
 *   - ключи/сравнение версий;
 *   - select_version / resolve_package (цепочка: репозитории -> crates.io);
 *   - поиск (search) с fallback на crates.io API.
 *
 * Модуль не имеет рантайм-зависимостей (только Node.js >= 18, глобальный fetch).
 * Используется как библиотека (@asombi/truck-index) и как CLI `trk-ts`.
 */

// ---------------------------------------------------------------------------
// Типы
// ---------------------------------------------------------------------------

export interface PackageEntry {
  name: string;
  version: string;
  url?: string;
  sha256?: string;
  description?: string;
  size?: string;
  license?: string;
  depends?: string[];
  post_install?: string;
  /** "crates.io" если запись получена из fallback-источника. */
  source?: string;
  [key: string]: string | string[] | undefined;
}

/** Индекс = словарь slug -> запись (как _ALL_PKGS_CACHE в Python-версии). */
export type PackageIndex = Map<string, PackageEntry>;

export interface ResolvedPackage {
  pkg: PackageEntry;
  fromCrates: boolean;
}

// ---------------------------------------------------------------------------
// Константы (синхронизированы с truck/core/utils.py)
// ---------------------------------------------------------------------------

export const DEFAULT_REPOS: readonly string[] = [
  // AsomPacket — основной расширенный индекс (23 пакета x 4260 версий)
  "https://raw.githubusercontent.com/WFStudio-app/AsomPacket/main/index.toml",
  "https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.toml",
];

export const CRATES_API = "https://crates.io/api/v1/crates";
export const CRATES_DL =
  "https://crates.io/api/v1/crates/{}/{}/download";

export const USER_AGENT = "Truck/0.2.00 (ts-index)";

// ---------------------------------------------------------------------------
// Парсер индексов (порт _parse_toml_index)
// ---------------------------------------------------------------------------

function stripQuotes(s: string): string {
  s = s.trim();
  if (s.length >= 2 && s[0] === s[s.length - 1] && (s[0] === '"' || s[0] === "'")) {
    return s.slice(1, -1);
  }
  return s;
}

function parseTomlArray(val: string): string[] {
  const end = val.lastIndexOf("]");
  const inner = end > 0 ? val.slice(1, end) : val.slice(1);
  const out: string[] = [];
  for (const raw of inner.split(",")) {
    const item = stripQuotes(raw);
    if (item) out.push(item);
  }
  return out;
}

/**
 * Мини-парсер TOML-индексов Truck. Поддерживает ровно то же подмножество,
 * что и Python-версия: секции `[packages.<slug>]` и пары key = value /
 * key = ["a", "b"]. Комментариев внутри строк не ожидаем (как в Python).
 */
export function parseTomlIndex(text: string): PackageIndex {
  const result: PackageIndex = new Map();
  let current: string | null = null;

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    if (line.startsWith("[") && line.endsWith("]")) {
      current = line.slice(1, -1).trim();
      if (!result.has(current)) result.set(current, {} as PackageEntry);
      continue;
    }
    if (current === null) continue;

    const eq = line.indexOf("=");
    if (eq < 0) continue;
    const key = line.slice(0, eq).trim();
    const val = line.slice(eq + 1).trim();
    const entry = result.get(current)!;

    if (val.startsWith("[")) {
      (entry as Record<string, unknown>)[key] = parseTomlArray(val);
    } else if (val.length >= 2 && val[0] === val[val.length - 1] &&
               (val[0] === '"' || val[0] === "'")) {
      (entry as Record<string, unknown>)[key] = val.slice(1, -1);
    } else {
      (entry as Record<string, unknown>)[key] = val;
    }
  }
  return result;
}

/** Приводит индекс вида "packages.<slug>" -> "<slug>" (как fetch_all_packages). */
export function normalizeIndexSections(index: PackageIndex): PackageIndex {
  const out: PackageIndex = new Map();
  for (const [section, values] of index) {
    if (section.startsWith("packages.")) {
      const name = section.slice("packages.".length);
      if (name) out.set(name, values);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Версии (порт _ver_key)
// ---------------------------------------------------------------------------

/**
 * Ключ сортировки версий: числовые префиксы сегментов.
 * 0.24.0 > 0.9.0; отсутствующий/нечисловой сегмент = -1.
 */
export function versionKey(v: string | undefined): number[] {
  const parts: number[] = [];
  for (const p of String(v ?? "").split(".").slice(0, 4)) {
    const m = /^(\d+)/.exec(p);
    parts.push(m ? parseInt(m[1], 10) : -1);
  }
  return parts;
}

export function compareVersionKeys(a: number[], b: number[]): number {
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i++) {
    const x = a[i] ?? -1;
    const y = b[i] ?? -1;
    if (x !== y) return x < y ? -1 : 1;
  }
  return 0;
}

export function isNewer(candidate: string, than: string): boolean {
  return compareVersionKeys(versionKey(candidate), versionKey(than)) > 0;
}

// ---------------------------------------------------------------------------
// Селектор версий (порт select_version)
// ---------------------------------------------------------------------------

/**
 * Выбор версии пакета из словаря индекса. Индексы бывают двух форматов:
 * "голые" секции [packages.curl] (Asombi) и версионные [packages.curl-8.9.1]
 * (AsomPacket). Порядок: явная версия "name-<version>" -> максимум среди
 * "<name>-*" -> точное имя. Возвращает [slug, entry] или [null, null].
 */
export function selectVersion(
  pkgs: PackageIndex,
  name: string,
  version?: string | null,
): [string, PackageEntry] | [null, null] {
  let bestKey: [string, PackageEntry] | null = null;
  let bestVer: number[] | null = null;

  // 1. Точное совпадение (Asombi index: [packages.curl])
  if (pkgs.has(name)) {
    const e = pkgs.get(name)!;
    bestKey = [name, e];
    bestVer = versionKey(e.version);
  }

  // 2. Явная версия: curl@8.9.1 -> slug "curl-8.9.1"
  if (version) {
    const slug = `${name}-${version}`;
    if (pkgs.has(slug)) return [slug, pkgs.get(slug)!];
    const prefix = slug + "-"; // коллизии вида 8.9.1-2
    let cands: [string, PackageEntry][] = [];
    for (const [k, v] of pkgs) {
      if (k.startsWith(prefix)) cands.push([k, v]);
    }
    if (cands.length) {
      cands.sort((a, b) =>
        compareVersionKeys(versionKey(a[1].version), versionKey(b[1].version)));
      return cands[cands.length - 1];
    }
    return [null, null];
  }

  // 3. Все версии пакета: максимум среди "<name>-*"
  const pref = name + "-";
  const named: [string, PackageEntry][] = [];
  const loose: [string, PackageEntry][] = [];
  for (const [k, v] of pkgs) {
    if (!k.startsWith(pref)) continue;
    if (v.name === name) named.push([k, v]);
    else loose.push([k, v]);
  }
  const cands = named.length ? named : loose;
  for (const pair of cands) {
    const vk = versionKey(pair[1].version);
    if (bestVer === null || compareVersionKeys(vk, bestVer) > 0) {
      bestKey = pair;
      bestVer = vk;
    }
  }
  return bestKey ?? [null, null];
}

// ---------------------------------------------------------------------------
// crates.io fallback (порт crates_lookup / resolve_package)
// ---------------------------------------------------------------------------

async function fetchJson(url: string): Promise<any | null> {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Запись в формате Truck для последней опубликованной версии crate. */
export async function cratesLookup(name: string): Promise<PackageEntry | null> {
  const data = await fetchJson(`${CRATES_API}/${encodeURIComponent(name)}`);
  const cinfo = data?.crate;
  if (!cinfo) return null;
  const ver: string | undefined =
    cinfo.newest_version || cinfo.max_stable_version;
  if (!ver) return null;

  const vdata = await fetchJson(
    `${CRATES_API}/${encodeURIComponent(name)}/${encodeURIComponent(ver)}`,
  );
  let checksum = "";
  let size = "unknown";
  if (vdata?.version) {
    checksum = String(vdata.version.checksum ?? "").toLowerCase();
    const bytes = vdata.version.crate_size;
    if (bytes) size = `${Math.round((bytes / 1024) * 10) / 10} KB`;
  }
  return {
    name: `${name}-${ver}`,
    version: ver,
    description: cinfo.description || "Rust crate from crates.io",
    url: CRATES_DL.replace("{}", encodeURIComponent(name))
                  .replace("{}", encodeURIComponent(ver)),
    sha256: checksum,
    size,
    license: cinfo.license || "unknown",
    source: "crates.io",
  };
}

/** Поиск пакетов на crates.io (порт crates_io_search из search.py). */
export async function cratesIoSearch(query: string): Promise<PackageIndex> {
  const out: PackageIndex = new Map();
  const data = await fetchJson(
    `${CRATES_API}?page=1&per_page=20&q=${encodeURIComponent(query)}`,
  );
  for (const cr of data?.crates ?? []) {
    const name: string = cr.name ?? "";
    if (!name) continue;
    const ver: string = cr.newest_version ?? "?";
    out.set(name, {
      name,
      version: ver,
      description: cr.description ?? "",
      url: CRATES_DL.replace("{}", encodeURIComponent(name))
                    .replace("{}", encodeURIComponent(ver)),
      source: "crates.io",
      license: cr.license ?? "unknown",
    });
  }
  return out;
}

/**
 * Разрешение пакета: индексы репозиториев -> crates.io fallback.
 * Синхронно с resolve_package() из utils.py.
 */
export async function resolvePackage(
  pkgs: PackageIndex,
  name: string,
  version?: string | null,
): Promise<ResolvedPackage | null> {
  const [, pkg] = selectVersion(pkgs, name, version);
  if (pkg) return { pkg, fromCrates: false };
  const crate = await cratesLookup(name);
  if (crate) return { pkg: crate, fromCrates: true };
  return null;
}

// ---------------------------------------------------------------------------
// Загрузка индексов по сети
// ---------------------------------------------------------------------------

export interface FetchOptions {
  repos?: string[];
  timeoutMs?: number;
}

/** Скачивание и парсинг одного индекс-URL. */
export async function fetchIndexFromUrl(
  url: string,
  timeoutMs = 15000,
): Promise<PackageIndex> {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) return new Map();
    return normalizeIndexSections(parseTomlIndex(await res.text()));
  } catch {
    return new Map();
  }
}

/**
 * Загрузка всех подключённых репозиториев (порт fetch_all_packages).
 * При конфликте slug'ов later-source выигрывает только если версия новее —
 * так richer-индекс AsomPacket остаётся основным.
 */
export async function fetchAllPackages(opts: FetchOptions = {}): Promise<PackageIndex> {
  const repos = opts.repos ?? DEFAULT_REPOS;
  const all: PackageIndex = new Map();
  for (const url of repos) {
    const idx = await fetchIndexFromUrl(url, opts.timeoutMs);
    for (const [slug, entry] of idx) {
      const prev = all.get(slug);
      if (!prev || isNewer(entry.version ?? "", prev.version ?? "")) {
        all.set(slug, entry);
      }
    }
  }
  return all;
}

// ---------------------------------------------------------------------------
// Публичный API поиска/вывода (для CLI trk-ts и будущего TUI)
// ---------------------------------------------------------------------------

export interface SearchResult {
  slug: string;
  entry: PackageEntry;
}

/** Поиск по имени/описанию с crates.io fallback (порт cmd_search). */
export async function searchPackages(
  pkgs: PackageIndex,
  query: string,
): Promise<SearchResult[]> {
  const q = query.toLowerCase();
  let hits = [...pkgs.entries()].filter(
    ([slug, e]) =>
      slug.toLowerCase().includes(q) ||
      (e.description ?? "").toLowerCase().includes(q),
  );
  if (!hits.length) {
    const crates = await cratesIoSearch(query);
    hits = [...crates.entries()];
  }
  hits.sort((a, b) => a[0].localeCompare(b[0]));
  return hits.map(([slug, entry]) => ({ slug, entry }));
}
