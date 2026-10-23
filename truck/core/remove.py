import os
import shutil

from paths import PACKAGES_DIR, BIN_DIR
from utils import ok, err, warn, load_installed, save_installed


def _is_within_directory(directory, target):
    """Строгая проверка вложенности: '/packages' НЕ префикс '/packages-sibling'.

    startswith() без завершающего '/' дыряв — сравниваем через
    os.path.commonpath, чтобы исключить путаницу с префиксом имени.
    """
    try:
        return os.path.commonpath(
            [os.path.abspath(directory), os.path.abspath(target)]) \
            == os.path.abspath(directory)
    except ValueError:
        # разные диски / несовместимые пути
        return False


def _unlink_binaries(name, entry):
    """Удаляет симлинки пакета из ~/.asombi/bin (только ведущие в packages/)."""
    removed = []
    for bname in entry.get("binaries", []):
        dst = os.path.join(BIN_DIR, bname)
        if os.path.islink(dst):
            target = os.path.realpath(dst)
            if _is_within_directory(os.path.realpath(PACKAGES_DIR), target):
                try:
                    os.remove(dst)
                    removed.append(bname)
                except OSError:
                    pass
    return removed


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

        # сначала убираем симлинки бинарников из PATH
        gone = _unlink_binaries(name, installed[name])
        if gone:
            ok(f"Unlinked from PATH: {', '.join(gone)}")

        # Проверяем что путь реально внутри PACKAGES_DIR (защита)
        if install_dir:
            real_dir = os.path.realpath(install_dir)
            real_pkg = os.path.realpath(PACKAGES_DIR)
            if _is_within_directory(real_pkg, real_dir) \
                    and real_dir != real_pkg and os.path.exists(install_dir):
                shutil.rmtree(install_dir)
                ok(f"Removed files: {install_dir}")
            elif os.path.exists(install_dir):
                warn(f"Skipping removal of {install_dir} — outside packages dir")

        del installed[name]
        save_installed(installed)
        ok(f"'{name}' removed.")
