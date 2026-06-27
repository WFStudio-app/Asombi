from utils import *

def cmd_search(args):
    if not args:
        err("Usage: wiz search <query>")
        return

    query = " ".join(args).lower()
    pkgs = fetch_all_packages()

    results = {
        name: pkg for name, pkg in pkgs.items()
        if query in name.lower() or query in pkg.get("description", "").lower()
    }

    if not results:
        warn(f"No packages found for '{query}'")
        return

    print(f"\n{c('bold', 'Search results for:')} {c('cyan', query)}\n")
    installed = load_installed()

    for name, pkg in sorted(results.items()):
        status = c("green", " [installed]") if name in installed else ""
        print(f"  {c('bold', name)} v{pkg.get('version','?')}{status}")
        print(f"    {pkg.get('description', 'No description')}\n")
