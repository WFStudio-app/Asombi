from utils import err, warn, c, fetch_all_packages, load_installed


def cmd_search(args):
    if not args:
        err("Usage: trk search <query>")
        return

    query = " ".join(args).lower()
    pkgs = fetch_all_packages()

    results = {
        name: pkg for name, pkg in pkgs.items()
        if query in name.lower()
        or query in pkg.get("description", "").lower()
    }

    # Fallback: если в репозиториях ничего не найдено — ищем на crates.io
    if not results:
        info_msg = "[i] Not found in repositories, searching crates.io..."
        print(c("cyan", info_msg))
        data = crates_io_search(query)
        for name, pkg in data.items():
            results[name] = pkg

    if not results:
        warn(f"No packages found for '{query}'")
        return

    print(f"\n{c('bold', 'Search results for:')} {c('cyan', query)}\n")
    installed = load_installed()

    for name, pkg in sorted(results.items()):
        status = c("green", " [installed]") if name in installed else ""
        src = " [crates.io]" if pkg.get("source") == "crates.io" else ""
        ver = pkg.get("version", "?")
        # БАГ 1 ФИКС: незакрытая кавычка была здесь
        print(f"  {c('bold', name)} v{ver}{status}{src}")
        print(f"    {pkg.get('description', 'No description')}\n")


def crates_io_search(query):
    """Search crates.io API, return dict of Truck-style pkg entries."""
    out = {}
    try:
        import urllib.request
        import json as _json
        url = ("https://crates.io/api/v1/crates?page=1&per_page=20"
               "&q=" + urllib.request.quote(query))
        req = urllib.request.Request(
            url, headers={"User-Agent": "Truck/0.2.00"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = _json.loads(r.read().decode())
        for cr in data.get("crates", []):
            name = cr.get("name", "")
            ver = cr.get("newest_version", "?")
            out[name] = {
                "name": name,
                "version": ver,
                "description": cr.get("description") or "",
                "url": ("https://crates.io/api/v1/crates/{}/{}"
                        .format(urllib.request.quote(name),
                               urllib.request.quote(ver))),
                "source": "crates.io",
                "license": cr.get("license") or "unknown",
            }
    except Exception:
        pass
    return out
