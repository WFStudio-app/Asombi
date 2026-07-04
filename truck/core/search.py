from utils import err, warn, c, fetch_all_packages, load_installed


def cmd_search(args):
    if not args:
        err("Usage: trk search <query>")
        return

    query = " ".join(args).lower()
    pkgs = fetch_all_packages()

    if not pkgs:
        warn("No packages available. Check your repositories.")
        return

    results = {
        name: pkg for name, pkg in pkgs.items()
        if query in name.lower()
        or query in pkg.get("description", "").lower()
    }

    if not results:
        warn(f"No packages found for '{query}'")
        return

    print(f"\n{c('bold', 'Search results for:')} {c('cyan', query)}\n")
    installed = load_installed()

    for name, pkg in sorted(results.items()):
        status = c("green", " [installed]") if name in installed else ""
        ver = pkg.get("version", "?")
        # БАГ 1 ФИКС: незакрытая кавычка была здесь
        print(f"  {c('bold', name)} v{ver}{status}")
        print(f"    {pkg.get('description', 'No description')}\n")
