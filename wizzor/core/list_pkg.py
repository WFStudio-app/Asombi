from utils import *

def cmd_list(args):
    installed = load_installed()
    if not installed:
        info("No packages installed.")
        return

    print(f"\n{c('bold', 'Installed packages')} ({len(installed)}):\n")
    for name, meta in sorted(installed.items()):
        print(f"  {c('cyan', name):<30} v{meta.get('version','?')}")
        if meta.get("description"):
            print(f"  {'':30} {meta['description']}")
    print()
