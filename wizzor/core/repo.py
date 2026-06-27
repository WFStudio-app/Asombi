from utils import *

def cmd_repo(args):
    if not args:
        print("Usage: wiz repo [add|remove|list] [url]")
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
            err("Usage: wiz repo add <url>")
            return
        url = args[1]
        if url in sources:
            warn("Repository already added.")
            return
        # Проверка доступности
        info(f"Checking repository: {url}")
        data = fetch_json(url)
        if data is None:
            err("Could not reach repository. Not added.")
            return
        sources.append(url)
        save_sources(sources)
        ok(f"Repository added: {url}")

    elif sub == "remove":
        if len(args) < 2:
            err("Usage: wiz repo remove <url>")
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
