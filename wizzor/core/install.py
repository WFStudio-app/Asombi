import os
import tarfile
import zipfile
import shutil

from utils import (
    c, ok, err, info, warn,
    fetch_all_packages, load_installed, save_installed,
    ensure_dirs, download_file, sha256,
    CACHE_DIR, WIZ_DIR
)


def cmd_install(args):
    if not args:
        err("Usage: wiz install <package> [package2 ...]")
        return

    pkgs = fetch_all_packages()
    if not pkgs:
        err("No packages found. Check your internet or repositories.")
        return

    installed = load_installed()

    for name in args:
        _install_one(name, pkgs, installed)


def _install_one(name, pkgs, installed):
    print(f"\n{c('bold', 'Package:')} {c('cyan', name)}")

    if name not in pkgs:
        err(f"Package '{name}' not found in any repository.")
        return

    pkg = pkgs[name]
    version = pkg.get("version", "?")

    if name in installed:
        inst_ver = installed[name].get("version", "?")
        if inst_ver == version:
            warn(f"'{name}' is already installed (v{version})")
            return
        else:
            info(f"Upgrading {name}: {inst_ver} -> {version}")

    info(f"Version:  {version}")
    info(f"Size:     {pkg.get('size', 'unknown')}")
    info(f"Desc:     {pkg.get('description', 'No description')}")

    # Зависимости
    deps = pkg.get("depends", [])
    if deps:
        info(f"Deps:     {', '.join(deps)}")
        for dep in deps:
            if dep not in installed:
                info(f"Installing dependency: {dep}")
                _install_one(dep, pkgs, installed)
                # Перечитываем installed после установки зависимости
                installed.update(load_installed())

    url = pkg.get("url")
    if not url:
        err(f"No download URL for '{name}'")
        return

    ensure_dirs()
    filename = os.path.basename(url)
    if not filename:
        err(f"Cannot determine filename from URL: {url}")
        return

    cache_path = os.path.join(CACHE_DIR, filename)

    info("Downloading...")
    if not download_file(url, cache_path):
        return

    # SHA256 проверка
    expected_hash = pkg.get("sha256", "")
    if expected_hash:
        info("Verifying checksum...")
        actual_hash = sha256(cache_path)
        if actual_hash != expected_hash:
            err(f"SHA256 mismatch!\n  expected: {expected_hash}\n  got:      {actual_hash}")
            os.remove(cache_path)
            return
        ok("Checksum verified")

    # Папка установки
    packages_dir = os.path.join(WIZ_DIR, "packages")
    install_dir = os.path.join(packages_dir, name)
    os.makedirs(install_dir, exist_ok=True)

    # Распаковка
    info("Extracting...")
    try:
        if filename.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2")):
            with tarfile.open(cache_path) as tar:
                # Защита от path traversal
                safe_members = []
                for member in tar.getmembers():
                    member_path = os.path.realpath(os.path.join(install_dir, member.name))
                    if member_path.startswith(os.path.realpath(install_dir)):
                        safe_members.append(member)
                    else:
                        warn(f"Skipping unsafe path: {member.name}")
                tar.extractall(install_dir, members=safe_members)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(cache_path) as z:
                # Защита от path traversal в zip
                for member in z.namelist():
                    member_path = os.path.realpath(os.path.join(install_dir, member))
                    if member_path.startswith(os.path.realpath(install_dir)):
                        z.extract(member, install_dir)
                    else:
                        warn(f"Skipping unsafe zip path: {member}")
        elif filename.endswith(".sh"):
            dest = os.path.join(install_dir, filename)
            shutil.copy(cache_path, dest)
            os.chmod(dest, 0o755)
    except Exception as e:
        err(f"Extraction failed: {e}")
        return

    # post_install скрипт
    post = pkg.get("post_install", "")
    if post:
        post_path = os.path.realpath(os.path.join(install_dir, post))
        # Проверяем что скрипт внутри install_dir (защита от traversal)
        if post_path.startswith(os.path.realpath(install_dir)) and os.path.isfile(post_path):
            info("Running post-install script...")
            os.system(f"sh {post_path}")
        else:
            warn(f"post_install script not found or unsafe: {post}")

    installed[name] = {
        "version": version,
        "install_dir": install_dir,
        "url": url,
        "description": pkg.get("description", ""),
    }
    save_installed(installed)
    ok(f"'{name}' installed successfully (v{version})")
