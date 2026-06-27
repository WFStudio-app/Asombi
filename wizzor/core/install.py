import os
import tarfile
import zipfile
from utils import *

def cmd_install(args):
    if not args:
        err("Usage: wiz install <package> [package2 ...]")
        return

    pkgs = fetch_all_packages()
    if not pkgs:
        err("No packages found. Check your internet connection or repositories.")
        return

    installed = load_installed()

    for name in args:
        print(f"\n{c('bold', 'Package:')} {c('cyan', name)}")

        if name not in pkgs:
            err(f"Package '{name}' not found in any repository.")
            continue

        pkg = pkgs[name]
        version = pkg.get("version", "?")

        if name in installed:
            inst_ver = installed[name].get("version", "?")
            if inst_ver == version:
                warn(f"'{name}' is already installed (v{version})")
                continue
            else:
                info(f"Upgrading {name}: {inst_ver} → {version}")

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
                    cmd_install([dep])

        # Скачивание
        url = pkg.get("url")
        if not url:
            err(f"No download URL for '{name}'")
            continue

        ensure_dirs()
        filename = url.split("/")[-1]
        cache_path = os.path.join(CACHE_DIR, filename)

        info(f"Downloading...")
        if not download_file(url, cache_path):
            continue

        # Проверка хэша
        expected_hash = pkg.get("sha256")
        if expected_hash:
            actual_hash = sha256(cache_path)
            if actual_hash != expected_hash:
                err("SHA256 mismatch! File may be corrupted.")
                os.remove(cache_path)
                continue
            ok("Checksum verified")

        # Установка
        install_dir = os.path.expanduser(f"~/.wizzor/packages/{name}")
        os.makedirs(install_dir, exist_ok=True)

        try:
            if filename.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2")):
                with tarfile.open(cache_path) as tar:
                    tar.extractall(install_dir)
            elif filename.endswith(".zip"):
                with zipfile.ZipFile(cache_path) as z:
                    z.extractall(install_dir)
            elif filename.endswith(".sh"):
                dest = os.path.join(install_dir, filename)
                import shutil
                shutil.copy(cache_path, dest)
                os.chmod(dest, 0o755)
        except Exception as e:
            err(f"Extraction failed: {e}")
            continue

        # Запуск post-install скрипта если есть
        post = pkg.get("post_install")
        if post:
            info("Running post-install script...")
            os.system(f"bash {os.path.join(install_dir, post)}")

        # Запись в БД
        installed[name] = {
            "version": version,
            "install_dir": install_dir,
            "url": url,
            "description": pkg.get("description", ""),
        }
        save_installed(installed)
        ok(f"'{name}' installed successfully (v{version})")
