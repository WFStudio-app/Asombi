import os
import json
import urllib.request
import urllib.error
import shutil
import hashlib

WIZ_DIR = os.path.expanduser("~/.wizzor")
INSTALLED_DB = os.path.join(WIZ_DIR, "installed.json")
CACHE_DIR = os.path.join(WIZ_DIR, "cache")
SOURCES_FILE = os.path.join(WIZ_DIR, "sources.list")

DEFAULT_REPOS = [
    "https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.json"
]

COLORS = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "blue":   "\033[94m",
    "cyan":   "\033[96m",
    "reset":  "\033[0m",
    "bold":   "\033[1m",
}


def c(color, text):
    return f"{COLORS.get(color,'')}{text}{COLORS['reset']}"


def ok(msg):    print(c("green",  f"[✓] {msg}"))
def err(msg):   print(c("red",    f"[✗] {msg}"))
def info(msg):  print(c("cyan",   f"[i] {msg}"))
def warn(msg):  print(c("yellow", f"[!] {msg}"))


def ensure_dirs():
    os.makedirs(WIZ_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


def load_installed():
    if not os.path.exists(INSTALLED_DB):
        return {}
    with open(INSTALLED_DB) as f:
        return json.load(f)


def save_installed(db):
    ensure_dirs()
    with open(INSTALLED_DB, "w") as f:
        json.dump(db, f, indent=2)


def load_sources():
    if not os.path.exists(SOURCES_FILE):
        return list(DEFAULT_REPOS)
    with open(SOURCES_FILE) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    return lines or list(DEFAULT_REPOS)


def save_sources(sources):
    ensure_dirs()
    with open(SOURCES_FILE, "w") as f:
        f.write("# Wizzor sources.list\n")
        for s in sources:
            f.write(s + "\n")


def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Wizzor/0.1"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        err(f"HTTP {e.code}: {url}")
    except Exception as e:
        err(f"Failed to fetch {url}: {e}")
    return None


def download_file(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Wizzor/0.1"})
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        err(f"Download failed: {e}")
        return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_all_packages():
    """Загружает индекс пакетов из всех источников."""
    sources = load_sources()
    all_pkgs = {}
    for url in sources:
        info(f"Fetching index: {url}")
        data = fetch_json(url)
        if data and "packages" in data:
            all_pkgs.update(data["packages"])
    return all_pkgs
