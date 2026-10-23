"""Юнит-тесты utils.py: парсер индексов, версии, select_version, sources."""
import json
import os

import pytest


# ---------------------------------------------------------------------------
# _parse_toml_index
# ---------------------------------------------------------------------------

def test_parse_basic_sections():
    from utils import _parse_toml_index
    text = '''
[packages.curl]
name = "curl"
version = "8.9.1"
url = "https://example.com/curl.tar.gz"
sha256 = "abc123"
depends = ["openssl", "zlib"]
'''
    idx = _parse_toml_index(text)
    p = idx["packages.curl"]
    assert p["name"] == "curl"
    assert p["version"] == "8.9.1"
    assert p["depends"] == ["openssl", "zlib"]


def test_parse_empty_array_and_numbers():
    from utils import _parse_toml_index
    idx = _parse_toml_index('[packages.a]\nname = "a"\ndepends = []\nsize = 42\n')
    assert idx["packages.a"]["depends"] == []
    # числа сохраняются как строки — это ок для нас; проверим только non-crash
    assert idx["packages.a"]["size"] == "42"


def test_parse_comments_and_blank_lines():
    from utils import _parse_toml_index
    idx = _parse_toml_index("# comment\n\n[packages.x]\nname = 'x'\n")
    assert idx["packages.x"]["name"] == "x"


def test_parse_line_without_section_ignored():
    from utils import _parse_toml_index
    idx = _parse_toml_index('name = "orphan"\n[packages.x]\nname = "x"')
    assert idx == {"packages.x": {"name": "x"}}


@pytest.mark.parametrize("bad", [
    "[packages.\nname = 1",        # битая секция
    "][[\n",                        # мусор
    "\x00\x01\xff[packages.a]\nname=\"a\"\n",  # бинарные байты (после decode)
])
def test_parse_malformed_no_crash(bad):
    from utils import _parse_toml_index
    _parse_toml_index(bad)  # не должно бросать


# ---------------------------------------------------------------------------
# _ver_key / select_version
# ---------------------------------------------------------------------------

def test_ver_key_numeric():
    from utils import _ver_key
    assert _ver_key("0.24.0") > _ver_key("0.9.0")
    assert _ver_key("1.0.0") > _ver_key("0.99.99")
    assert _ver_key("") == [-1]


def test_ver_key_prefixes():
    """'1.2.3-rc1' должен сравниваться по числовым префиксам сегментов."""
    from utils import _ver_key
    assert _ver_key("1.2.3-rc1")[2] == 3


def _mkidx(entries):
    return {k: dict(v, name=v.get("name", k.split("-")[0]))
            for k, v in entries.items()}


def test_select_version_bare_format():
    from utils import select_version
    pkgs = _mkidx({"curl": {"version": "8.9.1"}})
    slug, pkg = select_version(pkgs, "curl")
    assert slug == "curl" and pkg["version"] == "8.9.1"


def test_select_version_max_of_versions():
    from utils import select_version
    pkgs = _mkidx({
        "curl-8.9.1": {"version": "8.9.1", "name": "curl"},
        "curl-7.88.1": {"version": "7.88.1", "name": "curl"},
        "curl-8.10.0": {"version": "8.10.0", "name": "curl"},
    })
    slug, pkg = select_version(pkgs, "curl")
    assert pkg["version"] == "8.10.0", f"BUG? got {pkg}"


def test_select_version_explicit():
    from utils import select_version
    pkgs = _mkidx({"curl-8.9.1": {"version": "8.9.1", "name": "curl"},
                   "curl-8.10.0": {"version": "8.10.0", "name": "curl"}})
    slug, pkg = select_version(pkgs, "curl", "8.9.1")
    assert slug == "curl-8.9.1"
    s2, p2 = select_version(pkgs, "curl", "9.9.9")
    assert s2 is None and p2 is None


def test_select_version_colon_prefix_collision():
    """'curl-8.9' при явном запросе не должен матчить 'curl-8.9.1' как равную версию...
    но slug 'curl-8.9' точного совпадения нет -> candidates 'curl-8.9-*'."""
    from utils import select_version
    pkgs = _mkidx({"curl-8.9.1": {"version": "8.9.1", "name": "curl"}})
    slug, pkg = select_version(pkgs, "curl", "8.9")
    # ожидаем НЕ найдено (8.9 != 8.9.1); если вернёт 8.9.1 — это спорное поведение
    assert slug is None, f"requested 8.9 but resolved to {slug}"


def test_select_version_dash_in_name():
    from utils import select_version
    pkgs = _mkidx({"py-game-1.0.0": {"version": "1.0.0", "name": "py-game"}})
    slug, pkg = select_version(pkgs, "py-game")
    assert pkg["version"] == "1.0.0"


def test_select_version_loose_prefix_shadowing():
    """Пакет 'lib' и 'libfoo': префикс 'lib-' не должен хватать 'libfoo-*'."""
    from utils import select_version
    pkgs = _mkidx({
        "lib-1.0.0": {"version": "1.0.0", "name": "lib"},
        "libfoo-2.0.0": {"version": "2.0.0", "name": "libfoo"},
    })
    slug, pkg = select_version(pkgs, "lib")
    assert pkg["name"] == "lib"


def test_select_version_missing_version_field():
    from utils import select_version
    pkgs = {"weird": {"name": "weird"}}
    slug, pkg = select_version(pkgs, "weird")
    assert slug == "weird"


# ---------------------------------------------------------------------------
# fetch_text с file:// и load/save sources
# ---------------------------------------------------------------------------

def test_fetch_text_file_url(fake_index):
    from utils import fetch_text
    idx = fake_index('[packages.a]\nname = "a"\n')
    text = fetch_text("file://" + idx)
    assert text is not None and "packages.a" in text


def test_fetch_text_bad_scheme_no_crash():
    from utils import fetch_text
    assert fetch_text("no-scheme-just-text") is None


def test_load_sources_default_when_file_absent():
    from utils import load_sources, DEFAULT_REPOS
    assert load_sources() == DEFAULT_REPOS


def test_load_sources_empty_file_falls_back(isolated_asombi_root):
    from utils import load_sources, save_sources, SOURCES_FILE, DEFAULT_REPOS
    save_sources([])
    assert load_sources() == DEFAULT_REPOS  # пустой список -> дефолты
    with open(SOURCES_FILE, "w") as f:
        f.write("\n\n# only comments\n")
    assert load_sources() == DEFAULT_REPOS


def test_save_installed_corrupt_db_raises(isolated_asombi_root):
    """load_installed на битом JSON — воспроизведение падения install/update."""
    from utils import load_installed, INSTALLED_DB
    with open(INSTALLED_DB, "w") as f:
        f.write("{corrupted")
    with pytest.raises(json.JSONDecodeError):
        load_installed()


# ---------------------------------------------------------------------------
# crates_lookup: URL quote (проверка бага urllib.request.quote)
# ---------------------------------------------------------------------------

def test_crates_lookup_quote_bug():
    """urllib.request.quote не существует в stdlib -> AttributeError внутри
    crates_lookup. Тест фиксирует баг (xfail до фикса)."""
    import utils
    called = {}

    def fake_fetch_json(url):
        called["url"] = url
        return {"crate": {"newest_version": "1.0.0",
                          "description": "d", "license": "MIT"}}
    utils.fetch_json = fake_fetch_json
    try:
        pkg = utils.crates_lookup("serde")
    except AttributeError as e:
        pytest.fail(f"BUG CONFIRMED: urllib.request.quote AttributeError: {e}")
    assert called["url"].startswith(utils.CRATES_API + "/serde")


def test_resolve_package_prefers_index_over_crates(monkeypatch):
    import utils
    monkeypatch.setattr(utils, "crates_lookup",
                        lambda n: pytest.fail("crates.io must not be used"))
    pkgs = {"curl": {"name": "curl", "version": "8.9.1"}}
    pkg, from_crates = utils.resolve_package("curl", pkgs)
    assert pkg["version"] == "8.9.1" and not from_crates
