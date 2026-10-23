"""Кросс-языковой fuzz: Python utils.py vs TypeScript index.ts.

Генерирует случайные индексы, парсит их обеими реализациями и сверяет:
  - набор секций/ключей/значений;
  - select_version (голый/версионный форматы, явные версии);
  - порядок версий (_ver_key vs versionKey).
Требуется node >= 18 и собранный truck/ts/dist.
"""
import json
import os
import random
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS_DIST = os.path.join(REPO, "truck", "ts", "dist", "index.js")

sys.path.insert(0, os.path.join(REPO, "truck", "core"))

NODE_DRIVER = r"""
const m = require(process.argv[2]);
const input = JSON.parse(require("fs").readFileSync(process.argv[3], "utf8"));
const idx = m.normalizeIndexSections(m.parseTomlIndex(input.text));
const out = { sections: {}, select: {} };
for (const [k, v] of idx) out.sections[k] = v;
for (const q of input.queries) {
  const [slug, pkg] = m.selectVersion(new Map(Object.entries(idx)), q.name, q.version ?? null);
  out.select[q.id] = [slug, pkg ? pkg.version : null];
}
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def node():
    if not os.environ.get("NODE_BIN"):
        for cand in ("node",):
            try:
                subprocess.run([cand, "-v"], capture_output=True, check=True)
                return cand
            except Exception:
                pass
        pytest.skip("node not available")
    return os.environ["NODE_BIN"]


@pytest.fixture(scope="module")
def ts_bundle(tmp_path_factory):
    if not os.path.exists(TS_DIST):
        pytest.skip("truck/ts/dist not built (run npm run build)")
    drv = tmp_path_factory.mktemp("drv") / "driver.js"
    drv.write_text(NODE_DRIVER)
    return str(drv)


WORDS = ["curl", "bat", "fd", "ripgrep", "exa", "delta", "lib", "libfoo",
         "py-game", "z", "a-b-c", "get", "wget"]


def rand_version(rng):
    style = rng.random()
    if style < 0.7:
        return "{}.{}.{}".format(rng.randint(0, 30), rng.randint(0, 30),
                                 rng.randint(0, 20))
    if style < 0.85:
        return "{}.{}".format(rng.randint(0, 9), rng.randint(0, 99))
    return "{}.{}.{}-rc{}".format(rng.randint(0, 5), rng.randint(0, 9),
                                  rng.randint(0, 5), rng.randint(0, 3))


def gen_index(rng):
    lines = ["# generated", "[repo]", 'name = "fuzz"', ""]
    entries = {}
    n = rng.randint(3, 40)
    for _ in range(n):
        name = rng.choice(WORDS)
        ver = rand_version(rng)
        bare = rng.random() < 0.3
        slug = name if bare else f"{name}-{ver}"
        if slug in entries:
            continue
        body = {"name": name, "version": ver,
                "url": f"https://x/{slug}.tar.gz"}
        if rng.random() < 0.4:
            body["depends"] = rng.sample(WORDS, rng.randint(0, 3))
        entries[slug] = body
        lines.append(f"[packages.{slug}]")
        for k, v in body.items():
            if isinstance(v, list):
                lines.append(k + " = [" +
                             ", ".join(f'"{i}"' for i in v) + "]")
            else:
                lines.append(f'{k} = "{v}"')
        lines.append("")
    return "\n".join(lines), entries


def run_ts(node, driver, text, queries):
    inp = {"text": text, "queries": queries}
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(inp, f)
        path = f.name
    try:
        r = subprocess.run([node, driver, TS_DIST, path],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"node driver failed: {r.stderr[:2000]}"
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


@pytest.mark.parametrize("seed", [1, 7, 42, 123, 999])
def test_parser_equivalence(seed, node, ts_bundle):
    rng = random.Random(seed)
    text, entries = gen_index(rng)
    from utils import _parse_toml_index

    py_raw = _parse_toml_index(text)
    queries = [{"id": f"q{i}", "name": n, "version": v}
               for i, (n, v) in enumerate(
                   [(rng.choice(WORDS),
                     rng.choice([None, rand_version(rng)])) for _ in range(8)])]
    ts = run_ts(node, ts_bundle, text, queries)

    # 1. Парсер: одинаковые секции и значения
    py_sections = {k: dict(v) for k, v in py_raw.items()}
    assert ts["sections"] == py_sections, \
        f"BUG: parser divergence seed={seed}"

    # 2. select_version эквивалентен
    from utils import select_version
    py_norm = {k[len("packages."):]: v
               for k, v in py_raw.items() if k.startswith("packages.")}
    for q in queries:
        pslug, ppkg = select_version(py_norm, q["name"], q["version"])
        tslug, tver = ts["select"][q["id"]]
        pver = ppkg["version"] if ppkg else None
        assert (pslug, pver) == (tslug, tver), (
            f"BUG: select_version divergence seed={seed} query={q}: "
            f"py=({pslug},{pver}) ts=({tslug},{tver})")


@pytest.mark.parametrize("v", ["0.9.0", "0.24.0", "1.2", "1.2.3-rc1", "",
                               "30.30.20", "x.y.z"])
def test_ver_key_equivalence(v, node, ts_bundle):
    from utils import _ver_key
    drv = ("const m=require(process.argv[2]);"
           "console.log(JSON.stringify(m.versionKey(process.argv[3])));")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(drv)
        path = f.name
    try:
        r = subprocess.run([node, path, TS_DIST, v], capture_output=True,
                           text=True, timeout=30)
        assert r.returncode == 0, r.stderr
        ts_key = json.loads(r.stdout)
    finally:
        os.unlink(path)
    # Python padляет до 4 сегментов; TS тоже. Пустая строка: py [-1]*? сверяем лениво
    py = _ver_key(v)
    assert len(ts_key) >= len(py)
    effective = py + [-1] * (len(ts_key) - len(py))
    assert effective == ts_key or py == ts_key[:len(py)], (
        f"BUG: versionKey divergence for {v!r}: py={py} ts={ts_key}")


def test_real_asompacket_index_equivalence(node, ts_bundle):
    """Живой большой индекс AsomPacket — оба парсера дают один результат."""
    idx_path = os.path.join(REPO, "AsomPacket", "index.toml")
    if not os.path.exists(idx_path):
        pytest.skip("AsomPacket/index.toml missing")
    text = open(idx_path).read()
    from utils import _parse_toml_index, select_version
    py_raw = _parse_toml_index(text)
    py_norm = {k[len("packages."):]: v
               for k, v in py_raw.items() if k.startswith("packages.")}
    assert len(py_norm) >= 4260, f"BUG? only {len(py_norm)} entries parsed"
    names = sorted({v.get("name") for v in py_norm.values() if v.get("name")})
    queries = [{"id": n, "name": n, "version": None} for n in names]
    ts = run_ts(node, ts_bundle, text, queries)
    assert ts["sections"] == {k: dict(v) for k, v in py_norm.items()}, \
        "BUG: real index parse divergence"
    for n in names:
        pslug, ppkg = select_version(py_norm, n)
        tslug, tver = ts["select"][n]
        assert (pslug, ppkg["version"]) == (tslug, tver), (
            f"BUG: real-index select_version divergence for {n}: "
            f"py={pslug}/{ppkg['version']} ts={tslug}/{tver}")
