"""Тесты build.py: определение билд-систем, линковка бинарников."""
import os
import stat

import pytest


def _mkpkg(isolated_asombi_root, name, files):
    d = os.path.join(isolated_asombi_root, "packages", name)
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
    return d


def test_find_root_single_wrapping_dir(isolated_asombi_root):
    from build import _find_root
    d = _mkpkg(isolated_asombi_root, "demo",
               {"repo-tag/Cargo.toml": "[package]\nname=\"x\"\n"})
    root = _find_root(d)
    assert root.endswith("repo-tag"), f"BUG? got {root}"


def test_find_root_no_marker_returns_src(isolated_asombi_root):
    from build import _find_root
    d = _mkpkg(isolated_asombi_root, "demo", {"README.md": "hi"})
    assert _find_root(d) == d


def test_find_root_two_dirs_stops(isolated_asombi_root):
    from build import _find_root
    d = _mkpkg(isolated_asombi_root, "demo",
               {"a/x.txt": "1", "b/y.txt": "2"})
    assert _find_root(d) == d


@pytest.mark.parametrize("files,expected", [
    ({"Cargo.toml": ""}, "cargo"),
    ({"go.mod": ""}, "go"),
    ({"configure.ac": ""}, "autotools"),
    ({"CMakeLists.txt": ""}, "cmake"),
    ({"meson.build": ""}, "meson"),
    ({"setup.py": ""}, "python"),
    ({"Makefile.am": ""}, "make"),
    ({}, None),
])
def test_detect_system(isolated_asombi_root, files, expected):
    from build import _detect_system
    d = _mkpkg(isolated_asombi_root, "demo", files)
    assert _detect_system(d) == expected


def test_detect_priority_cargo_over_make(isolated_asombi_root):
    from build import _detect_system
    d = _mkpkg(isolated_asombi_root, "demo",
               {"Cargo.toml": "", "Makefile": ""})
    assert _detect_system(d) == "cargo"


def test_binaries_in_ignores_nonexec_and_dirs(isolated_asombi_root):
    from build import _binaries_in
    usr = os.path.join(isolated_asombi_root, "usr")
    os.makedirs(os.path.join(usr, "bin"))
    os.makedirs(os.path.join(usr, "bin", "subdir"))
    ex = os.path.join(usr, "bin", "tool")
    with open(ex, "w") as f:
        f.write("#!/bin/sh\n")
    os.chmod(ex, 0o755)
    non = os.path.join(usr, "bin", "data.txt")
    open(non, "w").close()
    names = [n for _, n in _binaries_in(usr)]
    assert names == ["tool"], f"BUG? got {names}"


def test_link_binaries_does_not_clobber_foreign(isolated_asombi_root):
    """В ~/.asombi/bin уже есть файл НЕ из packages — перетирать нельзя."""
    from build import _link_binaries
    bindir = os.path.join(isolated_asombi_root, "bin")
    os.makedirs(bindir, exist_ok=True)
    foreign = os.path.join(bindir, "trk")
    with open(foreign, "w") as f:
        f.write("I am the launcher")
    usr = os.path.join(isolated_asombi_root, "packages", "demo", "usr")
    os.makedirs(os.path.join(usr, "bin"))
    mine = os.path.join(usr, "bin", "trk")
    with open(mine, "w") as f:
        f.write("#!/bin/sh\n")
    os.chmod(mine, 0o755)
    linked = _link_binaries("demo", usr)
    assert "trk" not in linked, "BUG: foreign binary in PATH was clobbered!"
    with open(foreign) as f:
        assert f.read() == "I am the launcher"


def test_link_binaries_replaces_own_previous(isolated_asombi_root):
    from build import _link_binaries
    bindir = os.path.join(isolated_asombi_root, "bin")
    pkg = os.path.join(isolated_asombi_root, "packages", "demo")
    usr = os.path.join(pkg, "usr")
    os.makedirs(os.path.join(usr, "bin"))
    b1 = os.path.join(usr, "bin", "tool")
    with open(b1, "w") as f:
        f.write("v1")
    os.chmod(b1, 0o755)
    linked = _link_binaries("demo", usr)
    assert linked == ["tool"]
    # повторный link идемпотентен
    linked2 = _link_binaries("demo", usr)
    assert linked2 == ["tool"], "re-link should update own symlink"


def test_build_package_no_toolchain_returns_empty(isolated_asombi_root,
                                                  monkeypatch):
    """Нет компиляторов в PATH -> [] без исключения (info/warn печатаются)."""
    import shutil as sh
    monkeypatch.setattr(sh, "which", lambda x: None)
    from build import build_package
    d = _mkpkg(isolated_asombi_root, "demo", {"Cargo.toml": "[package]\n"})
    assert build_package("demo", d) == []


def test_build_package_no_system_returns_empty(isolated_asombi_root):
    from build import build_package
    d = _mkpkg(isolated_asombi_root, "demo", {"README.md": "x"})
    assert build_package("demo", d) == []


def test_cmd_link_missing_package(isolated_asombi_root, capsys):
    from build import cmd_link
    cmd_link(["ghost"])
    assert "not installed" in capsys.readouterr().out.lower()


def test_cmd_link_existing_binaries(isolated_asombi_root):
    from build import cmd_link
    d = _mkpkg(isolated_asombi_root, "demo", {})
    ub = os.path.join(d, "usr", "bin")
    os.makedirs(ub)
    tool = os.path.join(ub, "mytool")
    with open(tool, "w") as f:
        f.write("#!/bin/sh\n")
    os.chmod(tool, 0o755)
    cmd_link(["demo"])
    link = os.path.join(isolated_asombi_root, "bin", "mytool")
    assert os.path.islink(link), "BUG: trk link did not create symlink"
