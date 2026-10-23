"""Интеграционные тесты CLI bin/trk (subprocess, изолированный HOME)."""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRK = os.path.join(REPO, "bin", "trk")


def run_trk(*args, home):
    env = dict(os.environ, HOME=home, PYTHONPATH="")
    return subprocess.run([sys.executable, TRK, *args], capture_output=True,
                          text=True, timeout=60, env=env)


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    return str(h)


def test_help_exit0(home):
    r = run_trk("help", home=home)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_version(home):
    r = run_trk("version", home=home)
    assert r.returncode == 0 and "Truck" in r.stdout


def test_unknown_command_exit1(home):
    r = run_trk("definitely-not-a-command", home=home)
    assert r.returncode == 1
    assert "Unknown command" in r.stdout + r.stderr


def test_no_args_prints_help(home):
    r = run_trk(home=home)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_list_empty(home):
    r = run_trk("list", home=home)
    assert r.returncode == 0, f"BUG: trk list crashed: {r.stderr}"
    assert "No packages installed" in r.stdout


def test_remove_not_installed_no_crash(home):
    r = run_trk("remove", "ghost", home=home)
    assert r.returncode == 0, f"BUG: traceback: {r.stderr}"
    assert "Traceback" not in r.stderr


def test_install_offline_graceful(home, monkeypatch):
    """Без сети install не должен падать с traceback (офлайн-окружение CI)."""
    # блокируем сеть через proxy на закрытый порт?надёжнее: просто проверяем
    # отсутствие Traceback при любом исходе
    r = run_trk("install", "some-package-that-may-not-exist-xyz123", home=home)
    combined = r.stdout + r.stderr
    if "Traceback" in combined:
        pytest.fail(f"BUG: unhandled exception in trk install:\n{combined}")


def test_repo_list_shows_defaults(home):
    r = run_trk("repo", "list", home=home)
    assert r.returncode == 0
    assert "AsomPacket" in r.stdout or "raw.githubusercontent" in r.stdout


def test_clean_twice_no_crash(home):
    r1 = run_trk("clean", home=home)
    r2 = run_trk("clean", home=home)
    for r in (r1, r2):
        assert r.returncode == 0
        assert "Traceback" not in r.stderr
