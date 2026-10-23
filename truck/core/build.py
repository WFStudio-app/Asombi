"""
Truck — сборка бинарников из исходников, скачанных AsomPacket.

Пакеты в индексе AsomPacket — это tarball'ы upstream-репозиториев
(исходники). После распаковки trk пытается собрать бинарники локально:

  1. cargo (Rust)   -> cargo install --path . --root <pkg>/usr
     bat, fd, ripgrep, exa, delta и другие Rust-проекты (Cargo.toml);
  2. go             -> CGO_ENABLED=0 go build -o <pkg>/usr/bin/<name> .
     fzf, lazygit и другие Go-проекты (go.mod);
  3. autotools      -> ./configure && make && make install prefix=<pkg>/usr
     curl, wget, git, jq, tmux, htop, nano, zsh и т.п. (configure.ac);
  4. cmake / make   -> CMakeLists.txt или Makefile.in/Makefile.am;
  5. setup.py       -> python3 -m pip install --prefix <pkg>/usr .
  6. perl           -> Perl-проекты (Build.PL / Makefile.PL):
                       perl Build.PL && ./Build && ./Build install,
                       либо perl Makefile.PL && make && make install;
     для компилируемых пакетов (например Bison) автотools-билд требует
     генератор парсеров — перед ./configure запускается `bison -d` по
     *.y/*.yy исходникам, если bison установлен.

Все инструменты проверяются через shutil.which — если компилятора нет,
выводится понятная подсказка (что поставить), а установка архива при
этом НЕ отменяется: файлы остаются в ~/.asombi/packages/<name>.

Готовые бинарники линкуются в ~/.asombi/bin (должен быть в PATH).
"""

import os
import re
import shutil
import subprocess

from paths import BIN_DIR, ASOMBI_ROOT


def _run(cmd, cwd, log_path):
    """Запуск команды с записью вывода в лог. True при успехе."""
    with open(log_path, "ab") as logf:
        logf.write(("\n$ " + " ".join(cmd) + "\n").encode())
        logf.flush()
        try:
            r = subprocess.run(cmd, cwd=cwd, stdout=logf,
                               stderr=subprocess.STDOUT)
            return r.returncode == 0
        except OSError as e:
            logf.write(("spawn error: " + str(e) + "\n").encode())
            return False


def _find_root(src_dir):
    """GitHub tarball содержит одну корневую папку 'repo-tag/'.
    Возвращает директорию, в которой лежат файлы сборки."""
    markers = ("Cargo.toml", "go.mod", "configure", "configure.ac",
               "autogen.sh", "CMakeLists.txt", "Makefile.am",
               "setup.py", "meson.build", "Build.PL", "Makefile.PL")
    d = src_dir
    for _ in range(3):
        if any(os.path.exists(os.path.join(d, m)) for m in markers):
            return d
        entries = [e.path for e in os.scandir(d) if e.is_dir()]
        # спускаемся только если внутри ровно одна директория (tarball-layout)
        if len(entries) != 1:
            return src_dir
        d = entries[0]
    return src_dir


def _binaries_in(usr_dir):
    """Список имён файлов в usr/bin и usr/sbin (без дубликатов)."""
    found = []
    for sub in ("bin", "sbin"):
        p = os.path.join(usr_dir, sub)
        if os.path.isdir(p):
            for name in sorted(os.listdir(p)):
                fp = os.path.join(p, name)
                if os.path.isfile(fp) and os.access(fp, os.X_OK):
                    found.append((sub, name))
    return found


def _link_binaries(name, usr_dir):
    """Линкует собранные бинарники в ~/.asombi/bin (PATH)."""
    os.makedirs(BIN_DIR, exist_ok=True)
    linked = []
    for sub, bname in _binaries_in(usr_dir):
        src = os.path.realpath(os.path.join(usr_dir, sub, bname))
        dst = os.path.join(BIN_DIR, bname)
        # не перетираем чужие бинарники (trk/os и реальные системные)
        if os.path.lexists(dst) and not os.path.realpath(dst).startswith(
                os.path.join(ASOMBI_ROOT, "packages")):
            continue
        if os.path.lexists(dst):
            os.remove(dst)
        try:
            os.symlink(src, dst)
            linked.append(bname)
        except OSError:
            pass
    return linked


# ---------------------------------------------------------------------------
# Билд-системы
# ---------------------------------------------------------------------------

def _try_cargo(src, usr, log, jobs):
    if not shutil.which("cargo"):
        return None  # инструмент недоступен
    cmd = ["cargo", "install", "--path", ".", "--root", usr,
           "--jobs", str(jobs)]
    if os.path.exists(os.path.join(src, "Cargo.lock")):
        cmd.append("--locked")
    return _run(cmd, src, log)


def _try_go(src, usr, log, jobs, pkg_name):
    if not shutil.which("go"):
        return None
    exe = os.path.join(usr, "bin", pkg_name)
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    # CGO_ENABLED=0 -> статический бинарник (важно для Android/proot),
    # GOCACHE — локально внутри пакета, чтобы не зависеть от HOME
    with open(log, "ab") as logf:
        logf.write(b"\n$ CGO_ENABLED=0 go build -trimpath -o <pkg>/usr/bin/<name> .\n")
        logf.flush()
        try:
            r = subprocess.run(["go", "build", "-trimpath", "-o", exe, "."],
                               cwd=src, stdout=logf, stderr=subprocess.STDOUT,
                               env=dict(os.environ, CGO_ENABLED="0",
                                        GOCACHE=os.path.join(usr, ".gocache")))
            return r.returncode == 0
        except OSError as e:
            logf.write(("spawn error: " + str(e) + "\n").encode())
            return False


def _prebuild_bison(src, log):
    """Генерирует C/C++-парсеры из Bison-грамматик (*.y / *.yy).

    Вызывается перед ./configure: git-tarball'ы часто не содержат
    готовых parser.c/parser.h. Если bison не установлен — молча
    пропускаем (make всё равно может найти готовые .c в архиве).
    Возвращает число сгенерированных файлов.
    """
    if not shutil.which("bison"):
        return 0
    generated = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in ("_asombi_build", ".git")]
        for f in files:
            if f.endswith((".y", ".yy")):
                if _run(["bison", "-d", f], root, log):
                    generated += 1
    return generated


def _try_autotools(src, usr, log, jobs):
    if not (shutil.which("make") and shutil.which("cc")):
        return None
    # Bison-грамматики (*.y/*.yy): из git-tarball'ов .c-парсеры не поставлены —
    # генерируем их до ./configure, если bison доступен в системе.
    _prebuild_bison(src, log)
    conf = os.path.join(src, "configure")
    # tarball'ы релизов обычно содержат готовый configure; git-теги — нет,
    # тогда генерируем его autoreconf'ом.
    if not os.path.exists(conf) and shutil.which("autoreconf"):
        for g in ("autogen.sh", "configure.ac", "configure.in"):
            gp = os.path.join(src, g)
            if g == "autogen.sh" and os.path.exists(gp):
                _run(["sh", "autogen.sh"], src, log)  # best-effort
                break
            if os.path.exists(gp):
                _run(["autoreconf", "--install", "--force"], src, log)
                break
    if not os.path.exists(conf):
        return None
    cc = shutil.which("cc") or shutil.which("gcc")
    env_note = "$ CC={} ./configure --prefix={} --disable-shared\n".format(cc, usr)
    with open(log, "ab") as f:
        f.write(env_note.encode())
    ok = _run([conf, "--prefix=" + usr, "--disable-shared", "--enable-static"],
              src, log)
    if not ok:
        return False
    if not _run(["make", "-j" + str(jobs)], src, log):
        return False
    return _run(["make", "install"], src, log)


def _try_cmake(src, usr, log, jobs):
    if not (shutil.which("cmake") and shutil.which("make")):
        return None
    bdir = os.path.join(src, "_asombi_build")
    os.makedirs(bdir, exist_ok=True)
    if not _run(["cmake", "-DCMAKE_INSTALL_PREFIX=" + usr, ".."], bdir, log):
        return False
    if not _run(["make", "-j" + str(jobs)], bdir, log):
        return False
    return _run(["make", "install"], bdir, log)


def _try_meson(src, usr, log, jobs):
    if not shutil.which("meson"):
        return None
    bdir = os.path.join(src, "_asombi_build")
    if not _run(["meson", "setup", bdir, "--prefix=" + usr], src, log):
        return False
    if not _run(["meson", "install", "-C", bdir], src, log):
        return False
    return True


def _try_make(src, usr, log, jobs):
    mk = os.path.join(src, "Makefile")
    if not (os.path.exists(mk) and shutil.which("make")):
        return None
    if not _run(["make", "-j" + str(jobs), "PREFIX=" + usr], src, log):
        return False
    return _run(["make", "install", "PREFIX=" + usr], src, log)


def _try_python(src, usr, log, jobs):
    py = shutil.which("python3")
    if not py:
        return None
    if not (os.path.exists(os.path.join(src, "setup.py"))
            or os.path.exists(os.path.join(src, "pyproject.toml"))):
        return None
    target = os.path.join(usr, "lib", "python", "site-packages")
    os.makedirs(target, exist_ok=True)
    if _run([py, "-m", "pip", "install", "--no-build-isolation",
             "--prefix", usr, "."], src, log):
        return True
    # pip может отсутствовать — fallback на setup.py
    return _run([py, "setup.py", "install",
                 "--install-lib=" + target,
                 "--install-scripts=" + os.path.join(usr, "bin")], src, log)


def _try_perl(src, usr, log, jobs):
    """Perl-модули: Module::Build (Build.PL) или ExtUtils::MakeMaker (Makefile.PL)."""
    perl = shutil.which("perl")
    if not perl:
        return None
    bindir = os.path.join(usr, "bin")
    libdir = os.path.join(usr, "lib", "perl5", "site_perl")
    os.makedirs(bindir, exist_ok=True)
    os.makedirs(libdir, exist_ok=True)
    # 1) Module::Build
    if os.path.exists(os.path.join(src, "Build.PL")):
        if not _run([perl, "Build.PL", "--install_base=" + usr], src, log):
            return False
        build = os.path.join(src, "Build")
        if not os.path.exists(build):
            return False
        if not _run([build, "build"], src, log):
            return False
        return _run([build, "install"], src, log)
    # 2) ExtUtils::MakeMaker
    if os.path.exists(os.path.join(src, "Makefile.PL")):
        if not _run([perl, "Makefile.PL",
                     "INSTALLSITESCRIPT=" + bindir,
                     "INSTALLSITEARCH=" + libdir,
                     "INSTALLBIN=" + bindir,
                     "INSTALLDIRS=site"], src, log):
            return False
        if not _run(["make", "-j" + str(jobs)], src, log):
            return False
        return _run(["make", "install"], src, log)
    return None


def _detect_system(src):
    if os.path.exists(os.path.join(src, "Cargo.toml")):
        return "cargo"
    if os.path.exists(os.path.join(src, "go.mod")):
        return "go"
    if (os.path.exists(os.path.join(src, "configure"))
            or os.path.exists(os.path.join(src, "configure.ac"))
            or os.path.exists(os.path.join(src, "autogen.sh"))):
        return "autotools"
    if os.path.exists(os.path.join(src, "CMakeLists.txt")):
        return "cmake"
    if os.path.exists(os.path.join(src, "meson.build")):
        return "meson"
    if os.path.exists(os.path.join(src, "setup.py")) or os.path.exists(
            os.path.join(src, "pyproject.toml")):
        return "python"
    if os.path.exists(os.path.join(src, "Build.PL")) or os.path.exists(
            os.path.join(src, "Makefile.PL")):
        return "perl"
    if os.path.exists(os.path.join(src, "Makefile")) or os.path.exists(
            os.path.join(src, "Makefile.in")) or os.path.exists(
            os.path.join(src, "Makefile.am")):
        return "make"
    return None


HINTS = {
    "cargo": "Rust package: install Rust toolchain (rustup / apt install cargo rustc)",
    "go": "Go package: install Go toolchain (apt install golang / go.dev)",
    "autotools": "C package: need a C compiler (apt install build-essential autoconf libtool pkg-config)",
    "cmake": "CMake package: apt install cmake build-essential",
    "meson": "Meson package: apt install meson ninja-build gcc",
    "python": "Python package: apt install python3 python3-pip",
    "perl": "Perl package: apt install perl perl-base (Termux: pkg install perl)",
    "make": "Makefile package: apt install build-essential",
    # Bison — генератор парсеров: нужен при сборке C-пакетов из git-tarball'ов
    # с грамматиками *.y/*.yy (например сам GNU Bison, jq, bash и т.п.)
    "bison": "Bison grammar detected: apt install bison (Termux: pkg install bison)",
}


def build_package(name, install_dir):
    """Собирает пакет из исходников в install_dir.

    Возвращает список установленных (прелинкованных) бинарников либо [].
    """
    src = _find_root(install_dir)
    system = _detect_system(src)
    if system is None:
        return []

    from utils import info, ok, warn, err, c  # локальный импорт (цикл путей)

    usr = os.path.join(install_dir, "usr")
    os.makedirs(usr, exist_ok=True)
    os.makedirs(os.path.join(usr, "bin"), exist_ok=True)
    log = os.path.join(install_dir, "build.log")

    jobs = min((os.cpu_count() or 2), 4)
    dispatch = {
        "cargo": lambda: _try_cargo(src, usr, log, jobs),
        "go": lambda: _try_go(src, usr, log, jobs, name),
        "autotools": lambda: _try_autotools(src, usr, log, jobs),
        "cmake": lambda: _try_cmake(src, usr, log, jobs),
        "meson": lambda: _try_meson(src, usr, log, jobs),
        "make": lambda: _try_make(src, usr, log, jobs),
        "python": lambda: _try_python(src, usr, log, jobs),
        "perl": lambda: _try_perl(src, usr, log, jobs),
    }

    info(f"Building binaries ({system})... this may take a while")
    result = dispatch[system]()
    if result is None:
        warn(HINTS.get(system, "No builder available for " + system))
        # C-пакет с Bison-грамматиками без bison — отдельная подсказка
        if system in ("autotools", "make", "cmake") and not shutil.which("bison"):
            grammars = [f for _, _, fs in os.walk(src) for f in fs
                        if f.endswith((".y", ".yy"))]
            if grammars:
                warn(HINTS["bison"])
        warn("Toolchain missing — sources kept at: " + install_dir)
        warn("Build manually, then run: trk link " + name)
        return []
    if result is False:
        err(f"Build failed ({system}). See log: {log}")
        warn("Sources kept at: " + install_dir)
        return []

    linked = _link_binaries(name, usr)
    if linked:
        ok(f"Linked into {BIN_DIR}: " + ", ".join(linked))
    else:
        warn("Build finished but no new binaries found in usr/bin")
    return linked


def cmd_link(args):
    """trk link <package> — прелинковать уже готовые бинарники пакета в PATH."""
    from utils import err, ok, info, warn
    from paths import PACKAGES_DIR
    if not args:
        err("Usage: trk link <package>")
        return
    name = args[0]
    install_dir = os.path.join(PACKAGES_DIR, name)
    if not os.path.isdir(install_dir):
        err(f"Package '{name}' is not installed.")
        return
    usr = os.path.join(install_dir, "usr")
    if not os.path.isdir(usr):
        info("No usr/ dir yet — trying to build first...")
        linked = build_package(name, install_dir)
        if linked:
            return
        return
    linked = _link_binaries(name, usr)
    if linked:
        ok(f"Linked into {BIN_DIR}: " + ", ".join(linked))
    else:
        warn("Nothing to link (already linked or no executables in usr/bin).")
