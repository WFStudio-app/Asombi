import os
import shutil
from utils import *

def cmd_clean():
    if os.path.exists(CACHE_DIR):
        size = sum(
            os.path.getsize(os.path.join(CACHE_DIR, f))
            for f in os.listdir(CACHE_DIR)
            if os.path.isfile(os.path.join(CACHE_DIR, f))
        )
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)
        ok(f"Cache cleared ({size // 1024} KB freed)")
    else:
        info("Cache is already empty.")
