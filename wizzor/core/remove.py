import os
import shutil

from utils import ok, err, warn, load_installed, save_installed


def cmd_remove(args):
    if not args:
        err("Usage: wiz remove <package> [package2 ...]")
        return

    installed = load_installed()

    for name in args:
        if name not in installed:
            warn(f"'{name}' is not installed.")
            continue

        install_dir = installed[name].get("install_dir", "")
        if install_dir and os.path.exists(install_dir):
            shutil.rmtree(install_dir)
            ok(f"Removed files: {install_dir}")

        del installed[name]
        save_installed(installed)
        ok(f"'{name}' removed.")
