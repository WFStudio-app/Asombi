from utils import (
    ok, err, info, warn, c,
    load_installed, fetch_all_packages
)
from install import _install_one


def cmd_update(args):
    installed = load_installed()
    if not installed:
        info("No packages installed.")
        return

    pkgs = fetch_all_packages()
    if not pkgs:
        err("Could not fetch package index.")
        return

    targets = args if args else list(installed.keys())
    updates = []

    for name in targets:
        if name not in installed:
            warn(f"'{name}' not installed, skipping.")
            continue
        if name not in pkgs:
            warn(f"'{name}' not found in repos, skipping.")
            continue
        current = installed[name].get("version", "0")
        latest  = pkgs[name].get("version", "0")
        if current != latest:
            updates.append(name)
            info(f"{name}: {current} -> {latest}")

    if not updates:
        ok("All packages are up to date.")
        return

    print(f"\n{c('bold', str(len(updates)))} package(s) to update.")
    for name in updates:
        _install_one(name, pkgs, installed)
        updated = load_installed()
        installed.update(updated)
