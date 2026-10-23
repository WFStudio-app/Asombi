import os
import tarfile
import zipfile
import shutil

from paths import CACHE_DIR, PACKAGES_DIR, ensure_dirs
from utils import (
    c, ok, err, info, warn,
    fetch_all_packages, load_installed, save_installed,
    download_file, sha256, resolve_package
)


def cmd_install(args):
    no_build = "--no-build" in args
    args = [a for a in args if a != "--no-build"]
    if not args:
        err("Usage: trk install <package>[@version] [package2 ...] [--no-build]")
        return

    pkgs = fetch_all_packages()
    if not pkgs:
        err("No packages found. Check your internet or repositories.")
        return

    installed = load_installed()
    for spec in args:
        name, _, want_ver = spec.partition("@")
        _install_one(name, pkgs, installed, want_ver or None,
                     no_build=no_build)


def _install_one(name, pkgs, installed, want_version=None, no_build=False):
    print(f"\n{c('bold', 'Package:')} {c('cyan', name)}")

    # Ищем в подключённых репозиториях (AsomPacket и др.),
    # при отсутствии — fallback на crates.io.
    # Индексы хранят версии как секции "<имя>-<версия>", поэтому
    # без явной версии выбирается максимальная.
    from_crates = False
    pkg = None
    if name in pkgs and (not want_version or pkgs[name].get("version") == want_version):
        pkg = pkgs[name]
    if pkg is None:
        pkg, from_crates = resolve_package(name, pkgs, want_version)
        if pkg is None:
            err(f"Package '{name}' not found in any repository or on crates.io.")
            return
        pkgs.setdefault(name, pkg)

    version = pkg.get("version", "?")

    if name in installed:
        inst_ver = installed[name].get("version", "?")
        if inst_ver == version:
            warn(f"'{name}' is already installed (v{version})")
            return
        info(f"Upgrading {name}: {inst_ver} -> {version}")

    info(f"Version:  {version}")
    info(f"Size:     {pkg.get('size', 'unknown')}")
    info(f"Desc:     {pkg.get('description', 'No description')}")

    deps = pkg.get("depends", [])
    if deps:
        info(f"Deps:     {', '.join(deps)}")
        for dep in deps:
            if dep not in installed:
                info(f"Installing dependency: {dep}")
                _install_one(dep, pkgs, installed)
                # если рекурсия не установила (нет в индексе/ошибка) — не блокируем
                if dep not in load_installed():
                    warn(f"Dependency '{dep}' could not be installed; continuing with '{name}'.")
                installed.update(load_installed())

    url = pkg.get("url", "")
    if not url:
        err(f"No download URL for '{name}'")
        return

    ensure_dirs()
    if from_crates:
        # crates.io отдаёт .crate (gzip tar) — сохраняем с понятным именем
        filename = "{}-{}.crate".format(name, version)
    else:
        filename = os.path.basename(url.rstrip("/"))
    if not filename:
        err(f"Cannot determine filename from URL: {url}")
        return

    cache_path = os.path.join(CACHE_DIR, filename)

    info("Downloading...")
    if not download_file(url, cache_path):
        return

    expected_hash = pkg.get("sha256", "")
    if expected_hash:
        info("Verifying checksum...")
        actual_hash = sha256(cache_path)
        if actual_hash != expected_hash:
            err(f"SHA256 mismatch!\n  expected: {expected_hash}\n  got:      {actual_hash}")
            os.remove(cache_path)
            return
        ok("Checksum verified")

    # Определяем реальный тип архива по magic bytes: URL-окончание
    # не всегда содержит расширение (codeload tar.gz отдаётся как ".../3.3.0").
    with open(cache_path, "rb") as f:
        magic = f.read(4)
    ext = ""
    if magic[:2] == b"\x1f\x8b":
        ext = ".tar.gz"          # gzip (включая .crate)
    elif magic[:6] in (b"\xfd7zXZ", b"ustar\x00"):
        ext = ".tar"
    elif magic[:3] == b"BZh":
        ext = ".tar.bz2"
    elif magic[:6] == b"PK\x03\x04":
        ext = ".zip"
    if ext and not filename.endswith(ext) and not filename.endswith(".crate"):
        real_name = filename + ext
        real_path = os.path.join(CACHE_DIR, real_name)
        if os.path.exists(real_path):
            os.remove(real_path)
        os.rename(cache_path, real_path)
        cache_path, filename = real_path, real_name

    # Путь установки теперь строго внутри ASOMBI_ROOT/packages/
    install_dir = os.path.join(PACKAGES_DIR, name)
    # чистим старые файлы при upgrade/reinstall (иначе tar-перекрывает не всё)
    if os.path.isdir(install_dir):
        shutil.rmtree(install_dir)
    os.makedirs(install_dir, exist_ok=True)

    info("Extracting...")
    try:
        is_archive = filename.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2",
                                        ".crate", ".tar")) or \
            (magic[:2] == b"\x1f\x8b" and not ext)
        if is_archive:
            # tarfile сам разберёт gzip/bzip2/xz по содержимому
            with tarfile.open(cache_path) as tar:
                safe = []
                for m in tar.getmembers():
                    mp = os.path.realpath(os.path.join(install_dir, m.name))
                    if mp.startswith(os.path.realpath(install_dir)):
                        safe.append(m)
                    else:
                        warn(f"Skipping unsafe path: {m.name}")
                tar.extractall(install_dir, members=safe)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(cache_path) as z:
                for member in z.namelist():
                    mp = os.path.realpath(os.path.join(install_dir, member))
                    if mp.startswith(os.path.realpath(install_dir)):
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

    post = pkg.get("post_install", "")
    if post:
        post_path = os.path.realpath(os.path.join(install_dir, post))
        if (post_path.startswith(os.path.realpath(install_dir))
                and os.path.isfile(post_path)):
            info("Running post-install script...")
            os.system(f"sh {post_path}")
        else:
            warn(f"post_install script not found or unsafe: {post}")

    # Сборка бинарников из исходников (AsomPacket отдаёт upstream tarball'ы).
    # Ошибка сборки НЕ отменяет установку — исходники остаются в packages/.
    binaries = []
    if not no_build:
        try:
            from build import build_package
            binaries = build_package(name, install_dir) or []
        except Exception as e:
            warn(f"Build step skipped: {e}")

    installed[name] = {
        "version": version,
        "install_dir": install_dir,
        "url": url,
        "description": pkg.get("description", ""),
        "binaries": binaries,
    }
    save_installed(installed)
    ok(f"'{name}' installed successfully (v{version})")
    if binaries:
        from paths import BIN_DIR
        ok(f"Binaries ready in PATH: {' '.join(binaries)}  ({BIN_DIR})")
