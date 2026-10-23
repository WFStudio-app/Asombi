/**
 * Тесты TS-модуля Truck. Проверяем эквивалентность Python-ядру
 * (truck/core/utils.py) на тех же данных.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  parseTomlIndex,
  normalizeIndexSections,
  versionKey,
  compareVersionKeys,
  isNewer,
  selectVersion,
  PackageIndex,
  PackageEntry,
} from "./index";

const SAMPLE = `
# comment
[meta]
version = "1"

[packages.curl]
name = "curl"
version = "8.9.1"
description = "transfer URLs"
url = "https://example.com/curl.tar.gz"
depends = ["openssl", "zlib"]

[packages.curl-8.9.1]
name = "curl"
version = "8.9.1"
url = "https://codeload.example/curl-8.9.1"

[packages.curl-7.85.0]
name = "curl"
version = "7.85.0"
url = "https://codeload.example/curl-7.85.0"

[packages.bat-0.24.0]
name = "bat"
version = "0.24.0"
description = "A cat clone"
url = "https://codeload.example/bat-0.24.0"

[packages.bat-0.9.0]
name = "bat"
version = "0.9.0"
url = "x"
`;

function idx(): PackageIndex {
  return normalizeIndexSections(parseTomlIndex(SAMPLE));
}

test("parser: секции и ключи", () => {
  const raw = parseTomlIndex(SAMPLE);
  assert.ok(raw.has("packages.curl"));
  const e = raw.get("packages.curl")!;
  assert.equal(e.name, "curl");
  assert.equal(e.version, "8.9.1");
  assert.deepEqual(e.depends, ["openssl", "zlib"]);
});

test("normalize: срезает префикс packages.", () => {
  const p = idx();
  assert.ok(p.has("curl"));
  assert.ok(p.has("bat-0.24.0"));
  assert.ok(!p.has("packages.curl"));
  assert.ok(!p.has("meta"));
});

test("versionKey: 0.24.0 > 0.9.0 (численное сравнение сегментов)", () => {
  assert.ok(isNewer("0.24.0", "0.9.0"));
  assert.ok(isNewer("8.9.1", "7.85.0"));
  assert.ok(!isNewer("1.2", "1.2.0")); // [1,2,-1,-1] < [1,2,0,0]? нет: -1<0 => не новее
  assert.equal(compareVersionKeys(versionKey("1.0.0"), versionKey("1.0.0")), 0);
});

test("selectVersion: максимум среди name-* (AsomPacket-формат)", () => {
  const [, best] = selectVersion(idx(), "bat");
  assert.ok(best);
  assert.equal(best!.version, "0.24.0");
});

test("selectVersion: явная версия curl@7.85.0", () => {
  const [slug, pkg] = selectVersion(idx(), "curl", "7.85.0");
  assert.equal(slug, "curl-7.85.0");
  assert.equal(pkg!.version, "7.85.0");
});

test("selectVersion: несуществующая версия -> null", () => {
  const [slug, pkg] = selectVersion(idx(), "curl", "9.9.9");
  assert.equal(slug, null);
  assert.equal(pkg, null);
});

test("selectVersion: смешанные форматы — голая секция участвует в сравнении", () => {
  // curl (голая 8.9.1) vs curl-8.9.1 vs curl-7.85.0 -> 8.9.1
  const [slug, pkg] = selectVersion(idx(), "curl");
  assert.equal(pkg!.version, "8.9.1");
  assert.ok(slug === "curl" || slug === "curl-8.9.1");
});

test("selectVersion: неизвестный пакет -> null", () => {
  const [slug, pkg] = selectVersion(idx(), "nope");
  assert.equal(slug, null);
  assert.equal(pkg, null);
});

test("эквивалентность Python: те же slugs, что у _parse_toml_index", () => {
  const p = idx();
  const expected = new Set([
    "curl", "curl-8.9.1", "curl-7.85.0", "bat-0.24.0", "bat-0.9.0",
  ]);
  assert.deepEqual(new Set(p.keys()), expected);
});

// Живой индекс AsomPacket (если есть сеть) — парсим локальный файл репо.
test("реальный AsomPacket index.toml парсится без потерь", async () => {
  const fs = await import("node:fs/promises");
  let text: string;
  try {
    text = await fs.readFile("/workspace/AsomPacket/index.toml", "utf8");
  } catch {
    return; // файл недоступен в окружении теста — пропускаем
  }
  const p = normalizeIndexSections(parseTomlIndex(text));
  assert.ok(p.size >= 4260, `ожидали >=4260 записей, получили ${p.size}`);
  const [, ripgrepBest] = selectVersion(p, "ripgrep");
  assert.ok(ripgrepBest, "ripgrep должен резолвиться");
  // максимальная версия численно не меньше любой другой версии ripgrep
  for (const [k, v] of p) {
    if (v.name === "ripgrep") {
      assert.ok(
        compareVersionKeys(versionKey(v.version), versionKey(ripgrepBest!.version)) <= 0,
        `${k}: ${v.version} оказалась новее выбранной ${ripgrepBest!.version}`,
      );
    }
  }
});
