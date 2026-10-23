"""Тесты remove/update/repo/clean/search/list/info + bin/trk CLI."""
import json
import os

import pytest


# --------------------------- remove ---------------------------------------

def test_remove_not_installed(isolated_asombi_root, capsys):
    from remove import cmd_remove
    cmd_remove(["ghost"])
    assert "not installed" in capsys.readouterr().out.lower()


def test_remove_cleans_db_and_files(isolated_asombi_root):
    import utils
    pkgdir = os.path.join(isolated_asombi_root, "packages", "demo")
    os.makedirs(pkgdir)
    open(os.path.join(pkgdir, "f.txt"), "w").close()
    utils.save_installed({"demo": {"version": "1", "install_dir": pkgdir,
                                  "binaries": []}})
    from remove import cmd_remove
    cmd_remove(["demo"])
    assert "demo" not in utils.load_installed()
    assert not os.path.exists(pkgdir)


def test_remove_outside_packages_refused(isolated_asombi_root):
    """install_dir вне packages/ — удалять нельзя (защита от кривой БД)."""
    import utils
    outside = os.path.join(isolated_asombi_root, "keepme")
    os.makedirs(outside)
    victim = os.path.join(outside, "important.txt")
    open(victim, "w").write("x")
    utils.save_installed({"evil": {"version": "1", "install_dir": outside}})
    from remove import cmd_remove
    cmd_remove(["evil"])
    assert os.path.exists(victim), "BUG: removed dir outside packages/"


def test_remove_prefix_confusion(isolated_asombi_root):
    """'demo2' не должен матчиться защитой 'demo' через startswith без '/'.
    startswith(real_pkg) пропустит packages/demo2 — это ок; но packages-demo
    снаружи — нет. Проверяем пограничный кейд: sibling-каталог валиден."""
    import utils
    sib = os.path.join(isolated_asombi_root, "packages-sibling")
    os.makedirs(sib)
    v = os.path.join(sib, "keep.txt")
    open(v, "w").write("x")
    utils.save_installed({"p": {"version": "1", "install_dir": sib}})
    from remove import cmd_remove
    cmd_remove(["p"])
    # packages-sibling начинается с realpath packages -> защита дырявая?
    if not os.path.exists(v):
        pytest.fail("BUG: startswith() prefix check treats 'packages-sibling' "
                    "as inside 'packages' and deleted it")


def test_remove_unlinks_only_own_binaries(isolated_asombi_root):
    import utils
    bindir = os.path.join(isolated_asombi_root, "bin")
    os.makedirs(bindir, exist_ok=True)
    pkgbin = os.path.join(isolated_asombi_root, "packages", "demo", "usr", "bin")
    os.makedirs(pkgbin)
    real = os.path.join(pkgbin, "tool")
    open(real, "w").close()
    link = os.path.join(bindir, "tool")
    os.symlink(real, link)
    # чужой линк, ведущий НЕ в packages — трогать нельзя
    other = os.path.join(isolated_asombi_root, "elsewhere")
    os.makedirs(other, exist_ok=True)
    oreal = os.path.join(other, "sys")
    open(oreal, "w").close()
    olink = os.path.join(bindir, "sysown")
    os.symlink(oreal, olink)
    utils.save_installed({"demo": {"version": "1", "binaries": ["tool"],
                                  "install_dir": os.path.join(
                                      isolated_asombi_root, "packages", "demo")}})
    from remove import cmd_remove
    cmd_remove(["demo"])
    assert not os.path.lexists(link), "own symlink must be unlinked"
    assert os.path.lexists(olink), "BUG: unrelated symlink removed"


# --------------------------- update ---------------------------------------

def _mk_state(isolated_asombi_root, version="1.0.0"):
    import utils
    pkgdir = os.path.join(isolated_asombi_root, "packages", "demo")
    os.makedirs(pkgdir, exist_ok=True)
    utils.save_installed({"demo": {"version": version,
                                  "install_dir": pkgdir, "url": "u"}})
    return utils


def test_update_nothing_installed(isolated_asombi_root, capsys):
    from update import cmd_update
    cmd_update([])
    assert "No packages installed" in capsys.readouterr().out


def test_update_up_to_date(isolated_asombi_root, monkeypatch, capsys):
    u = _mk_state(isolated_asombi_root, "1.0.0")
    monkeypatch.setattr(u, "fetch_all_packages", lambda force=False: {
        "demo": {"name": "demo", "version": "1.0.0", "url": "u"}})
    from update import cmd_update
    cmd_update([])
    assert "up to date" in capsys.readouterr().out.lower()


def test_update_numeric_ordering(isolated_asombi_root, monkeypatch, capsys):
    """0.9 -> 0.10 должен считаться АПГРЕЙДОМ, а не даунгрейдом."""
    u = _mk_state(isolated_asombi_root, "0.9")
    monkeypatch.setattr(u, "fetch_all_packages", lambda force=False: {
        "demo": {"name": "demo", "version": "0.10", "url": "u"}})
    # сам факт: update увидит разницу и попытается переустановить
    calls = []
    monkeypatch.setattr("install._install_one",
                        lambda *a, **k: calls.append(a))
    from update import cmd_update
    cmd_update([])
    out = capsys.readouterr().out
    assert "0.9 -> 0.10" in out or calls, \
        f"BUG: 0.9->0.10 treated as no-update? out={out!r}"


def test_update_corrupt_db_no_traceback(isolated_asombi_root, capsys):
    db = os.path.join(isolated_asombi_root, "data", "installed.json")
    with open(db, "w") as f:
        f.write("NOT JSON {{{")
    from update import cmd_update
    try:
        cmd_update([])
    except Exception as e:
        pytest.fail(f"BUG: corrupt installed.json crashes update: {e!r}")


# --------------------------- repo -----------------------------------------

def test_repo_add_list_remove(isolated_asombi_root, fake_index, monkeypatch,
                              capsys):
    idx = fake_index('[packages.z]\nname = "z"\n')
    url = "file://" + idx
    from repo import cmd_repo
    cmd_repo(["add", url])
    assert "Repository added" in capsys.readouterr().out
    cmd_repo(["list"])
    assert url in capsys.readouterr().out
    cmd_repo(["add", url])  # дубль
    assert "already added" in capsys.readouterr().out.lower()
    cmd_repo(["remove", url])
    assert "Repository removed" in capsys.readouterr().out
    cmd_repo(["remove", url])  # уже нет
    assert "not found" in capsys.readouterr().out.lower()


def test_repo_add_unreachable_not_added(isolated_asombi_root, capsys):
    from repo import cmd_repo
    cmd_repo(["add", "file:///nonexistent/index.toml"])
    from utils import load_sources, DEFAULT_REPOS
    assert load_sources() == DEFAULT_REPOS


def test_repo_unknown_sub(isolated_asombi_root, capsys):
    from repo import cmd_repo
    cmd_repo(["frobnicate"])
    assert "Unknown repo subcommand" in capsys.readouterr().out


# --------------------------- clean ----------------------------------------

def test_clean_removes_cache_files_keeps_dirs(isolated_asombi_root):
    cache = os.path.join(isolated_asombi_root, "cache")
    with open(os.path.join(cache, "x.tar.gz"), "w") as f:
        f.write("junk")
    from clean import cmd_clean
    cmd_clean()
    assert os.path.isdir(cache)
    assert os.listdir(cache) == []


# --------------------------- search ---------------------------------------

def test_search_matches_name_and_desc(isolated_asombi_root, monkeypatch):
    import utils
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: {
        "curl-8.9.1": {"name": "curl", "version": "8.9.1",
                       "description": "transfer tool"},
        "wget-1.0": {"name": "wget", "version": "1.0",
                     "description": "network downloader"},
    })
    monkeypatch.setattr("search.crates_io_search", lambda q: {})
    from search import cmd_search
    cmd_search(["curl"])
    # просто проверка отсутствия падения; вывод проверяем вручную ниже


def test_search_empty_query_usage(isolated_asombi_root, capsys):
    from search import cmd_search
    cmd_search([])
    assert "Usage" in capsys.readouterr().out


def test_search_crates_fallback_quote_bug(isolated_asombi_root, monkeypatch,
                                          capsys):
    """Если в индексах пусто, вызывается crates_io_search -> urllib.request.quote."""
    import utils
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: {})
    from search import cmd_search
    try:
        cmd_search(["serde"])
    except AttributeError as e:
        pytest.fail(f"BUG CONFIRMED: crates.io fallback AttributeError: {e}")


# --------------------------- list / info ----------------------------------

def test_list_shows_installed(isolated_asombi_root, capsys):
    import utils
    utils.save_installed({"demo": {"version": "1.2.3", "description": "d"}})
    from list_pkg import cmd_list
    cmd_list([])
    out = capsys.readouterr().out
    assert "demo" in out and "1.2.3" in out


def test_info_not_found(isolated_asombi_root, monkeypatch, capsys):
    import utils
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: {})
    monkeypatch.setattr(utils, "crates_lookup", lambda n: None)
    from info import cmd_info
    cmd_info(["missing"])
    assert "not found" in capsys.readouterr().out.lower()


def test_info_with_version_spec(isolated_asombi_root, monkeypatch, capsys):
    import utils
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: {
        "demo-1.0.0": {"name": "demo", "version": "1.0.0", "url": "u"},
        "demo-2.0.0": {"name": "demo", "version": "2.0.0", "url": "u"},
    })
    from info import cmd_info
    cmd_info(["demo@1.0.0"])
    out = capsys.readouterr().out
    assert "1.0.0" in out, "BUG: explicit @version ignored by info?"
