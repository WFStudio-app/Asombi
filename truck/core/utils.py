import os
import json
import urllib.request
import urllib.error
import hashlib
import sys
import time

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
    return COLORS.get(color, "") + str(text) + COLORS["reset"]


def ok(msg):
    print(c("green", "[OK] ") + str(msg))


def err(msg):
    print(c("red", "[ERR] ") + str(msg))


def info(msg):
    print(c("cyan", "[i] ") + str(msg))


def warn(msg):
    print(c("yellow", "[!] ") + str(msg))


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
        f.write("# Truck sources.list\n")
        for s in sources:
            f.write(s + "\n")


def fetch_text(url):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Truck/0.2.00"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        err("HTTP " + str(e.code) + ": " + url)
    except Exception as e:
        err("Failed to fetch " + url + ": " + str(e))
    return None


def fetch_json(url):
    text = fetch_text(url)
    if text is None:
        return None
    try:
        return json.loads(text)
    except Exception as e:
        err("JSON parse error: " + str(e))
    return None


def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _parse_toml_index(text):
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
        if val.startswith("["):
            end = val.rfind("]")
            inner = val[1:end] if end > 0 else val[1:]
            arr = []
            for item in inner.split(","):
                item = _strip_quotes(item)
                if item:
                    arr.append(item)
            result[current][key] = arr
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            result[current][key] = val[1:-1]
        else:
            result[current][key] = val
    return result


def download_file(url, dest, package_name=""):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Truck/0.2.00"})
        with urllib.request.urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()
            label = package_name if package_name else "packages"

            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    elapsed = time.time() - start_time

                    if total > 0 and downloaded > 0:
                        pct = min(int(downloaded * 100 / total), 100)
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        rem = (total - downloaded) / speed if speed > 0 else 0
                        h  = int(rem // 3600)
                        mn = int((rem % 3600) // 60)
                        sc = int(rem % 60)
                        time_str = (
                            str(h).zfill(2) + " h "
                            + str(mn).zfill(2) + " min "
                            + str(sc).zfill(2) + " sec"
                        )
                        line_out = (
                            "\r  [" + str(pct).zfill(3) + "%]"
                            " Downloading " + label + "..."
                            " " + time_str + "   "
                        )
                    else:
                        done_mb = downloaded / (1024 * 1024)
                        line_out = (
                            "\r  [---] Downloading " + label + "..."
                            " " + "{:.1f}".format(done_mb) + " MB   "
                        )

                    sys.stdout.write(line_out)
                    sys.stdout.flush()

        sys.stdout.write(
            "\r  [100%] Downloaded " + label
            + "                                    \n")
        sys.stdout.flush()
        return True

    except Exception as e:
        sys.stdout.write("\n")
        err("Download failed: " + str(e))
        return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_all_packages():
    sources = load_sources()
    all_pkgs = {}
    for url in sources:
        info("Fetching index: " + url)
        text = fetch_text(url)
        if not text:
            continue
        try:
            toml = _parse_toml_index(text)
        except Exception as e:
            warn("Failed to parse " + url + ": " + str(e))
            continue
        for section, values in toml.items():
            if section.startswith("packages."):
                name = section[len("packages."):]
                if name:
                    all_pkgs[name] = values
    return all_pkgs
