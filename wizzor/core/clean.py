import os
import shutil

from utils import ok, info, CACHE_DIR


def cmd_clean():
    if not os.path.exists(CACHE_DIR):
        info("Cache is already empty.")
        return

    files = [
        f for f in os.listdir(CACHE_DIR)
        if os.path.isfile(os.path.join(CACHE_DIR, f))
    ]

    if not files:
        info("Cache is already empty.")
        return

    size = sum(
        os.path.getsize(os.path.join(CACHE_DIR, f))
        for f in files
    )
    shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR)
    ok(f"Cache cleared ({len(files)} files, {size // 1024} KB freed)")
