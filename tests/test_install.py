"""Тесты install.py: сверка хэшей, path traversal, upgrade, зависимости."""
import hashlib
import io
import json
import os
import tarfile
import zipfile

import pytest


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_tar_gz(tmp_path, members):
    """members: {name: bytes}. Возвращает (path, sha256)."""
    p = str(tmp_path / "pkg.tar.gz")
    with tarfile.open(p, "w:gz") as t:
        for name, data in members.items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))
    return p, _sha(p)


def _index_with(url, sha="", **extra):
    base = {
        "name": "demo", "version": "1.0.0",
        "description": "demo pkg", "url": url, "sha256": sha,
    }
    base.update(extra)
    return {"demo": base}


def test_install_ok_flow(isolated_asombi_root, tmp_path, monkeypatch):
    import utils
    archive, sha = _make_tar_gz(
        tmp_path, {"demo-1.0.0/hello.txt": b"hi"})
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: _index_with(
                            "file://" + archive, sha))
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    db = utils.load_installed()
    assert "demo" in db and db["demo"]["version"] == "1.0.0"
    inst = os.path.join(isolated_asombi_root, "packages", "demo")
    found = [f for _, _, fs in os.walk(inst) for f in fs]
    assert "hello.txt" in found


def test_install_sha_mismatch_aborts(isolated_asombi_root, tmp_path, monkeypatch):
    import utils
    archive, _ = _make_tar_gz(tmp_path, {"a.txt": b"x"})
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: _index_with(
                            "file://" + archive, "0" * 64))
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    assert "demo" not in utils.load_installed()
    # мусор в кэше от хэш-мисматча должен быть удалён
    leftovers = os.listdir(os.path.join(isolated_asombi_root, "cache"))
    assert leftovers == [], f"BUG: cache leftovers {leftovers}"


def test_install_corrupt_archive_no_traceback(isolated_asombi_root, tmp_path,
                                              monkeypatch, capsys):
    """Битый 'архив' (gzip magic, но мусор) не должен печатать traceback."""
    import utils
    bad = str(tmp_path / "bad.tar.gz")
    with open(bad, "wb") as f:
        f.write(b"\x1f\x8b" + os.urandom(200))
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: _index_with("file://" + bad))
    from install import cmd_install
    try:
        cmd_install(["demo", "--no-build"])
    except Exception as e:
        pytest.fail(f"BUG: unhandled exception on corrupt archive: {e!r}")
    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert "demo" not in utils.load_installed()


def test_install_traversal_blocked(isolated_asombi_root, tmp_path, monkeypatch):
    """tar с '../evil' НЕ должен писать за пределы packages/demo."""
    import utils
    evil = os.path.join(isolated_asombi_root, "evil_escape.txt")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        ti = tarfile.TarInfo("../evil_escape.txt")
        data = b"PWNED"
        ti.size = len(data)
        t.addfile(ti, io.BytesIO(data))
        # абсолютный путь тоже
        ti2 = tarfile.TarInfo("/tmp/abs_evil.txt")
        ti2.size = 5
        t.addfile(ti2, io.BytesIO(data))
    archive = str(tmp_path / "evil.tar.gz")
    with open(archive, "wb") as f:
        f.write(buf.getvalue())
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: _index_with("file://" + archive))
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    assert not os.path.exists(evil), "BUG: path traversal escaped packages dir!"
    assert not os.path.exists("/tmp/abs_evil.txt"), "BUG: absolute path written!"


def test_install_symlink_member_later_rmtree(isolated_asombi_root, tmp_path,
                                             monkeypatch):
    """tar содержит симлинк ../outside -> при upgrade rmtree пойдёт ПО symlink."""
    import utils
    outside = os.path.join(isolated_asombi_root, "outside_important")
    os.makedirs(outside)
    victim = os.path.join(outside, "data.txt")
    with open(victim, "w") as f:
        f.write("precious")

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        ti = tarfile.TarInfo("link")
        ti.type = tarfile.SYMTYPE
        ti.linkname = "../outside_important"
        t.addfile(ti)
    archive = str(tmp_path / "sym.tar.gz")
    with open(archive, "wb") as f:
        f.write(buf.getvalue())
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: _index_with("file://" + archive))
    from install import cmd_install
    cmd_install(["demo", "--no-build"])   # распакует symlink
    cmd_install(["demo", "--no-build"])   # upgrade: rmtree(install_dir)
    if not os.path.exists(victim):
        pytest.fail("BUG: shutil.rmtree followed symlink and deleted "
                    "files OUTSIDE packages dir")


def test_install_already_installed_message(isolated_asombi_root, tmp_path,
                                           monkeypatch, capsys):
    import utils
    archive, sha = _make_tar_gz(tmp_path, {"f": b"1"})
    idx = _index_with("file://" + archive, sha)
    monkeypatch.setattr(utils, "fetch_all_packages",
                        lambda force=False: idx)
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    capsys.readouterr()
    cmd_install(["demo", "--no-build"])
    out = capsys.readouterr().out
    assert "already installed" in out


def test_install_upgrade_replaces_files(isolated_asombi_root, tmp_path,
                                        monkeypatch):
    """При upgrade старые файлы не должны оставаться."""
    import utils
    a1, s1 = _make_tar_gz(tmp_path, {"old_only.txt": b"1"})
    # переименуем, чтобы имена кэш-файлов совпадали для одного url-имени
    idx = _index_with("file://" + a1, s1)
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx)
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    inst = os.path.join(isolated_asombi_root, "packages", "demo")
    assert any("old_only" in f for _, _, fs in os.walk(inst) for f in fs)
    # новая версия
    a2, s2 = _make_tar_gz(tmp_path, {"new_only.txt": b"2"})
    idx2 = _index_with("file://" + a2, s2)
    idx2["demo"]["version"] = "2.0.0"
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx2)
    cmd_install(["demo", "--no-build"])
    files = [f for _, _, fs in os.walk(inst) for f in fs]
    assert "new_only.txt" in files
    assert "old_only.txt" not in files, \
        "BUG: stale files survived upgrade"
    assert utils.load_installed()["demo"]["version"] == "2.0.0"


def test_install_zip_flow(isolated_asombi_root, tmp_path, monkeypatch):
    import utils
    p = str(tmp_path / "pkg.zip")
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("zipfile.txt", "Z")
    idx = _index_with("file://" + p, _sha(p))
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx)
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    inst = os.path.join(isolated_asombi_root, "packages", "demo")
    assert any("zipfile.txt" in f for _, _, fs in os.walk(inst) for f in fs)


def test_install_unknown_package(isolated_asombi_root, monkeypatch, capsys):
    import utils
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: {})
    from install import cmd_install
    cmd_install(["nonexistent"])
    out = capsys.readouterr().out
    assert "No packages found" in out or "not found" in out


def test_install_dependency_cycle_no_hang(isolated_asombi_root, tmp_path,
                                          monkeypatch):
    """A зависит от B, B зависит от A — рекурсия не должна зациклиться."""
    import utils
    archive, sha = _make_tar_gz(tmp_path, {"f": b"1"})
    url = "file://" + archive
    idx = {
        "a": {"name": "a", "version": "1.0", "url": url, "sha256": sha,
              "depends": ["b"]},
        "b": {"name": "b", "version": "1.0", "url": url, "sha256": sha,
              "depends": ["a"]},
    }
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx)
    import signal

    def _timeout(sig, frm):
        raise RuntimeError("HANG: infinite dependency recursion")
    old = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(10)
    try:
        from install import cmd_install
        cmd_install(["a", "--no-build"])
    except RuntimeError as e:
        pytest.fail(f"BUG: {e}")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def test_install_url_no_filename(isolated_asombi_root, monkeypatch, capsys):
    """URL без имени файла -> 'Cannot determine filename', не краш."""
    import utils
    idx = {"demo": {"name": "demo", "version": "1", "url": ""}}
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx)
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    out = capsys.readouterr().out
    assert "No download URL" in out


def test_post_install_runs_from_pkg_dir_only(isolated_asombi_root, tmp_path,
                                             monkeypatch):
    """post_install='../../escape.sh' не должен выполниться."""
    import utils
    marker = os.path.join(isolated_asombi_root, "pwned.marker")
    escape = os.path.join(isolated_asombi_root, "escape.sh")
    with open(escape, "w") as f:
        f.write(f"touch {marker}\n")
    archive, sha = _make_tar_gz(tmp_path, {"script.sh": b"echo legit\n"})
    idx = _index_with("file://" + archive, sha,
                      post_install="../../escape.sh")
    monkeypatch.setattr(utils, "fetch_all_packages", lambda force=False: idx)
    from install import cmd_install
    cmd_install(["demo", "--no-build"])
    assert not os.path.exists(marker), "BUG: post_install escaped package dir"
