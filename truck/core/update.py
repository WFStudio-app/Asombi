from utils import (
    ok, err, info, warn, c,
    load_installed, fetch_all_packages, _ver_key
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
        latest_pkg = None
        # 1) точная секция (Asombi index), 2) выбор максимальной версии из
        # индексов вида "<name>-<ver>", 3) crates.io fallback
        if name in pkgs:
            latest_pkg = pkgs[name]
        else:
            from utils import select_version
            _slug, sel = select_version(pkgs, name)
            if sel is not None:
                latest_pkg = sel
                pkgs[name] = sel
        if latest_pkg is None:
            from utils import resolve_package
            latest_pkg, _fc = resolve_package(name, pkgs)
            if latest_pkg is None:
                warn(f"'{name}' not found in repos or crates.io, skipping.")
                continue
            pkgs[name] = latest_pkg
        current = installed[name].get("version", "0")
        latest = latest_pkg.get("version", "0")
        if current == latest:
            continue
        # Числовое сравнение версий: 0.9 -> 0.10 это АПГРЕЙД,
        # 1.2.3 -> 1.2.2 — даунгрейд (пропускаем, если не запрошен явно).
        cur_key, lat_key = _ver_key(current), _ver_key(latest)
        if lat_key <= cur_key:
            if args:  # явное указание пакета — разрешаем переустановку
                updates.append(name)
                info(f"{name}: {current} -> {latest} (reinstall)")
            continue
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
