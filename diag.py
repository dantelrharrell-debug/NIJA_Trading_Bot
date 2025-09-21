# diag.py — safe diagnostic, prints files & env then exits
import os, sys
print("=== DIAG START ===")
print("cwd:", os.getcwd())
try:
    print("listing top-level files:", os.listdir("."))
except Exception as e:
    print("list error:", e)
print("sys.path:", sys.path)
print("ENV NIJA_LIVE:", os.getenv("NIJA_LIVE"))
print("ENV STARTING WITH PROCFILE? SHOWING PROCFILE CONTENT IF EXISTS:")
try:
    if os.path.exists("Procfile"):
        print("--- Procfile ---")
        print(open("Procfile","r").read())
    else:
        print("Procfile not found")
except Exception as e:
    print("procfile read error:", e)
print("=== DIAG END ===")
# exit so the process stops (we only want log output)
sys.exit(0)
