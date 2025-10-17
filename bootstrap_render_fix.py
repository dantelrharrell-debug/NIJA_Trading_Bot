# bootstrap_render_fix.py
# SAFE diagnostics + runtime reinstall for Render (non-destructive)
# Place this file in repo root and import it at top of trading_worker_live.py

import sys, os, importlib, subprocess, traceback

def print_div(msg):
    print("\n" + "="*8 + " " + msg + " " + "="*8)

print_div("BOOTSTRAP DIAGNOSTICS START")
print("python executable:", sys.executable)
print("python version:", sys.version.replace("\n"," "))
print("sys.path (first 12):")
for p in sys.path[:12]:
    print("  ", p)

site_pkgs = [p for p in sys.path if p and ('site-packages' in p or 'dist-packages' in p)]
print("\nDetected site-packages candidates:")
for sp in site_pkgs:
    print("  ", sp, "exists?", os.path.isdir(sp))

found = []
for sp in site_pkgs:
    try:
        for nm in os.listdir(sp):
            if nm.lower().startswith("coinbase"):
                found.append((sp, nm))
    except Exception:
        pass

print("\nsite-packages coinbase* entries (if any):")
if found:
    for sp,nm in found:
        print("  ", sp + "/" + nm)
else:
    print("  NONE FOUND")

candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase_advanced_api"]
print("\nAttempting imports of common module names:")
for cand in candidates:
    try:
        m = importlib.import_module(cand)
        print("IMPORT OK:", cand, "->", getattr(m, "__file__", getattr(m, "__path__", "package-no-file")))
    except Exception as e:
        print("IMPORT FAIL:", cand, type(e).__name__, str(e))

try:
    print_div("PIP SHOW coinbase-advanced-py")
    subprocess.run([sys.executable, "-m", "pip", "show", "coinbase-advanced-py"], check=False)
except Exception as e:
    print("pip show failed:", e)

print_div("RUNTIME pip reinstall (force) attempt")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", "--force-reinstall", "coinbase-advanced-py==1.8.2"])
    print("RUNTIME INSTALL: pip install completed")
except subprocess.CalledProcessError as e:
    print("RUNTIME INSTALL: pip install failed:", e)
except Exception as e:
    print("RUNTIME INSTALL: unexpected error:", type(e).__name__, e)

print("\nAttempting import again after runtime reinstall:")
for cand in candidates:
    try:
        m = importlib.import_module(cand)
        print("POST-REINSTALL IMPORT OK:", cand, "->", getattr(m, "__file__", getattr(m, "__path__", "package-no-file")))
    except Exception as e:
        print("POST-REINSTALL IMPORT FAIL:", cand, type(e).__name__, str(e))

print_div("BOOTSTRAP DIAGNOSTICS END")
