"""
Большой тестовый набор Truck (Asombi OS) — поиск багов.

pytest conftest: изолирует файловую систему (~/.asombi в tmp),
чистит кэш индексов, подменяет пути модуля paths на временные.
"""
import json
import os
import sys

import pytest

TRUCK_CORE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "truck", "core")
sys.path.insert(0, TRUCK_CORE)


@pytest.fixture(autouse=True)
def isolated_asombi_root(tmp_path, monkeypatch):
    """Переносит всё дерево ~/.asombi во временную директорию."""
    root = str(tmp_path / ".asombi")
    import paths
    for name in ("ASOMBI_ROOT", "SYSTEM_DIR", "BIN_DIR", "INSTANCES_DIR",
                 "PACKAGES_DIR", "CACHE_DIR", "LOGS_DIR", "DATA_DIR",
                 "WIZ_DIR"):
        old = getattr(paths, name)
        new = os.path.join(root, old.split(".asombi/", 1)[1]
                           if ".asombi/" in old else "")
        if name == "ASOMBI_ROOT":
            new = root
        monkeypatch.setattr(paths, name, new)
    monkeypatch.setattr(paths, "INSTALLED_DB",
                        os.path.join(root, "data", "installed.json"))
    monkeypatch.setattr(paths, "SOURCES_FILE",
                        os.path.join(root, "data", "sources.list"))
    # модули, импортировавшие константы by-value — тоже правим
    for mod in ("utils", "install", "remove", "build", "clean", "repo"):
        try:
            m = __import__(mod)
        except ImportError:
            continue
        for attr in ("CACHE_DIR", "PACKAGES_DIR", "BIN_DIR", "INSTALLED_DB",
                     "SOURCES_FILE", "ASOMBI_ROOT"):
            if hasattr(m, attr):
                monkeypatch.setattr(m, attr, getattr(paths, attr))
    paths.ensure_dirs()
    # сброс кэша индексов utils + заглушка сети (тесты не должны ходить в net)
    import utils
    monkeypatch.setattr(utils, "_ALL_PKGS_CACHE", None)

    if os.environ.get("TRK_ALLOW_NET") != "1":
        real_fetch = utils.fetch_text  # до monkeypatch, привязка к модулю

        def guarded(url):
            if url.startswith("file://"):
                return real_fetch(url)
            err_msg = "[ERR] Failed to fetch " + str(url)
            return None
        monkeypatch.setattr(utils, "fetch_text", guarded)
    yield root


@pytest.fixture
def installed_db(isolated_asombi_root):
    def _write(data):
        import utils
        utils.save_installed(data)
        return data
    return _write


@pytest.fixture
def fake_index(isolated_asombi_root):
    """Пишет локальный sources.list с file:// индексом из текста."""
    def _write(toml_text):
        idx = os.path.join(isolated_asombi_root, "index.toml")
        with open(idx, "w") as f:
            f.write(toml_text)
        import utils
        utils.save_sources(["file://" + idx])
        return idx
    return _write
