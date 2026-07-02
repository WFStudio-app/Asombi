from utils import info, c, load_installed


def cmd_list(args):
    installed = load_installed()
    if not installed:
        info("No packages installed.")
        return

    print(f"\n{c('bold', 'Installed packages')} ({len(installed)}):\n")
    for name, meta in sorted(installed.items()):
        ver  = meta.get("version", "?")
        desc = meta.get("description", "")
        print(f"  {c('cyan', name):<30} v{ver}")
        if desc:
            print(f"  {'':<30} {desc}")
    print()
