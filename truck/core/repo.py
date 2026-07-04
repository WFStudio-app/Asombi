from utils import (
    ok, err, info, warn, c,
    load_sources, save_sources, fetch_text, _parse_toml_index
)


def cmd_repo(args):
    if not args:
        print("Usage: trk repo [add|remove|list] [url]")
        return

    sub = args[0]
    sources = load_sources()

    if sub == "list":
        print(f"\n{c('bold', 'Repositories')} ({len(sources)}):\n")
        for s in sources:
            print(f"  {c('cyan', s)}")
        print()

    elif sub == "add":
        if len(args) < 2:
            err("Usage: trk repo add <url>")
            return
        url = args[1]
        if url in sources:
            warn("Repository already added.")
            return
        info(f"Checking repository: {url}")
        text = fetch_text(url)
        if not text:
            err("Could not reach repository. Not added.")
            return
        # Проверяем что это валидный TOML индекс
        try:
            toml = _parse_toml_index(text)
            pkg_count = sum(
                1 for k in toml if k.startswith("packages."))
            info(f"Found {pkg_count} package(s) in repository")
        except Exception as e:
            err(f"Invalid repository format: {e}")
            return
        sources.append(url)
        save_sources(sources)
        ok(f"Repository added: {url}")

    elif sub == "remove":
        if len(args) < 2:
            err("Usage: trk repo remove <url>")
            return
        url = args[1]
        if url not in sources:
            warn("Repository not found.")
            return
        sources.remove(url)
        save_sources(sources)
        ok(f"Repository removed: {url}")

    else:
        err(f"Unknown repo subcommand: '{sub}'")
