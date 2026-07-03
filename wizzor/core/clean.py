import os
import shutil

from paths import CACHE_DIR, human_size, size_of
from utils import ok, info


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

    size = size_of(CACHE_DIR)
    shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR)
    ok(f"Cache cleared ({len(files)} files, {human_size(size)} freed)")
