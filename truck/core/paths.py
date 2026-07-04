"""
Asombi OS — централизованное дерево путей файловой системы.

Всё что принадлежит Asombi живёт внутри ASOMBI_ROOT.
Termux home не загрязняется лишними папками.

Дерево:
  ~/.asombi/
  ├── system/           ← системные файлы (bin копии, конфиги)
  ├── instances/        ← изолированные окружения Alpine
  │   └── <name>/
  │       └── rootfs/   ← реальный Alpine rootfs
  ├── packages/         ← установленные Truck пакеты
  ├── cache/            ← кэш загрузок
  ├── logs/             ← логи операций
  └── data/
      ├── installed.json ← БД установленных пакетов
      └── sources.list   ← список репозиториев
"""

import os

# Корень всей файловой системы Asombi — отдельно от Termux
ASOMBI_ROOT   = os.path.expanduser("~/.asombi")

# Системные директории
SYSTEM_DIR    = os.path.join(ASOMBI_ROOT, "system")
INSTANCES_DIR = os.path.join(ASOMBI_ROOT, "instances")
PACKAGES_DIR  = os.path.join(ASOMBI_ROOT, "packages")
CACHE_DIR     = os.path.join(ASOMBI_ROOT, "cache")
LOGS_DIR      = os.path.join(ASOMBI_ROOT, "logs")
DATA_DIR      = os.path.join(ASOMBI_ROOT, "data")

# Файлы данных
INSTALLED_DB  = os.path.join(DATA_DIR, "installed.json")
SOURCES_FILE  = os.path.join(DATA_DIR, "sources.list")
INSTANCES_FILE = os.path.join(DATA_DIR, "instances.json")

WIZ_DIR = ASOMBI_ROOT


def instance_rootfs(name: str) -> str:
    """Путь к rootfs конкретного инстанса."""
    return os.path.join(INSTANCES_DIR, name, "rootfs")


def instance_dir(name: str) -> str:
    """Путь к директории инстанса."""
    return os.path.join(INSTANCES_DIR, name)


def ensure_dirs():
    """Создаёт всё дерево директорий Asombi."""
    dirs = [
        ASOMBI_ROOT,
        SYSTEM_DIR,
        INSTANCES_DIR,
        PACKAGES_DIR,
        CACHE_DIR,
        LOGS_DIR,
        DATA_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def size_of(path: str) -> int:
    """Возвращает размер директории или файла в байтах."""
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def human_size(n: int) -> str:
    """Человекочитаемый размер."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n // 1024} KB"
    if n < 1024 ** 3:
        return f"{n // (1024 ** 2)} MB"
    return f"{n // (1024 ** 3)} GB"
