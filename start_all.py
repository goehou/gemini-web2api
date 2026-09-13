"""Start all instances: python start_all.py

.env.anon -> 匿名实例, .env.cookie -> 带cookie实例, Ctrl+C 全停。
"""
import os
import subprocess
import sys

ENVS = [e for e in (".env.anon", ".env.cookie") if os.path.exists(e)]
if not ENVS:
    sys.exit("no .env.anon / .env.cookie found; copy from .env.example first")

procs = [subprocess.Popen([sys.executable, "-u", "-m", "gemini_web2api", "--env-file", e])
         for e in ENVS]
print(f"started {len(procs)} instance(s): {', '.join(ENVS)}")
try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    for p in procs:
        p.terminate()
