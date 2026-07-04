import os
import json
import urllib.request
import urllib.error
import hashlib
import sys

from paths import (
    ASOMBI_ROOT, CACHE_DIR, DATA_DIR, PACKAGES_DIR,
    INSTALLED_DB, SOURCES_FILE, ensure_dirs
)

WIZ_DIR = ASOMBI_ROOT

DEFAULT_REPOS = [
    "https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.toml"
]

COLORS = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "reset":  "\033[0m",
    "bold":   "\033[1m",
}


def c(color, text):
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def ok(msg):   print(c("green",  f"[\u2713] {msg}"))
def err(msg):  print(c("red",    f"[\u2717] {msg}"))
def info(msg): print(c("cyan",   f"[i] {msg}"))
def warn(msg): print(c("yellow", f"[!] {msg}"))


def load_installed():
    ensure_dirs()
    if not os.path.exists(INSTALLED_DB):
        return {}
    with open(INSTALLED_DB) as f:
        return json.load(f)


def save_installed(db):
    ensure_dirs()
    with open(INSTALLED_DB, "w") as f:
        json.dump(db, f, indent=2)


def load_sources():
    ensure_dirs()
    if not os.path.exists(SOURCES_FILE):
        return list(DEFAULT_REPOS)
    with open(SOURCES_FILE) as f:
        lines = [line.strip() for line in f
                 if line.strip() and not line.startswith("#")]
    return lines or list(DEFAULT_REPOS)


def save_sources(sources):
    ensure_dirs()
    with open(SOURCES_FILE, "w") as f:
        f.write("# Wizzor sources.list\n")
        for s in sources:
            f.write(s + "\n")


def fetch_text(url):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Wizzor/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        err(f"HTTP {e.code}: {url}")
    except Exception as e:
        err(f"Failed to fetch {url}: {e}")
    return None


def fetch_json(url):
    text = fetch_text(url)
    if text is None:
        return None
    try:
        return json.loads(text)
    except Exception as e:
        err(f"JSON parse error: {e}")
    return None


def _parse_toml_index(text):
    """Минимальный TOML парсер для индекса пакетов."""
    result = {}
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current not in result:
                result[current] = {}
            continue
        if "=" not in line or current is None:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        # Массив
        if val.startswith("["):
            end = val.rfind("]")
            inner = val[1:end] if end > 0 else val[1:]
            arr = []
            for item in inner.split(","):
                item = item.strip().strip('"\''')
                if item:
                    arr.append(item)
            result[current][key] = arr
        # БАГ 3 ФИКС: правильная проверка кавычек без синтаксических ошибок
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            result[current][key] = val[1:-1]
        else:
            result[current][key] = val
    return result


def download_file(url, dest):
    """Скачивает файл с прогресс-баром."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Wizzor/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = min(int(downloaded * 20 / total), 20)
                        bar = "\u2588" * pct + "\u2591" * (20 - pct)
                        sys.stdout.write(
                            f"\r  [{bar}] {downloaded * 100 // total}%  ")
                        sys.stdout.flush()
        if total > 0:
            print()
        return True
    except Exception as e:
        print()
        err(f"Download failed: {e}")
        return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_all_packages():
    """Загружает индекс пакетов из всех источников (TOML)."""
    sources = load_sources()
    all_pkgs = {}
    for url in sources:
        info(f"Fetching index: {url}")
        text = fetch_text(url)
        if not text:
            continue
        try:
            toml = _parse_toml_index(text)
        except Exception as e:
            warn(f"Failed to parse {url}: {e}")
            continue
        for section, values in toml.items():
            if section.startswith("packages."):
                name = section[len("packages."):]
                if name:
                    all_pkgs[name] = values
    return all_pkgs
