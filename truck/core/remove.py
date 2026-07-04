import os
import shutil

from paths import PACKAGES_DIR
from utils import ok, err, warn, load_installed, save_installed


def cmd_remove(args):
    if not args:
        err("Usage: trk remove <package> [package2 ...]")
        return

    installed = load_installed()

    for name in args:
        if name not in installed:
            warn(f"'{name}' is not installed.")
            continue

        install_dir = installed[name].get("install_dir", "")

        # Проверяем что путь реально внутри PACKAGES_DIR (защита)
        if install_dir:
            real_dir = os.path.realpath(install_dir)
            real_pkg = os.path.realpath(PACKAGES_DIR)
            if real_dir.startswith(real_pkg) and os.path.exists(install_dir):
                shutil.rmtree(install_dir)
                ok(f"Removed files: {install_dir}")
            elif os.path.exists(install_dir):
                warn(f"Skipping removal of {install_dir} — outside packages dir")

        del installed[name]
        save_installed(installed)
        ok(f"'{name}' removed.")
