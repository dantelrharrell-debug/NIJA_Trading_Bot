#!/usr/bin/env python3
# debug_import_coinbase.py
# Probes site-packages and tries common import names for the coinbase-advanced-py distribution.
# If a working import is found, writes the importable module name to /tmp/coinbase_import_name
# and exits with code 0. Otherwise prints diagnostics and exits 2.

import sys, os, pkgutil, traceback

OUTPATH = "/tmp/coinbase_import_name"

def try_import(name):
    try:
        mod = __import__(name)
        path = getattr(mod, "__file__", None)
        print(f"IMPORT SUCCESS: {name} -> {path}")
        return True, name, path
    except Exception as e:
        print(f"IMPORT FAILED: {name}: {e}")
        return False, name, None

def main():
    print("=== PYTHON ===")
    print(sys.executable)
    print("\n=== sys.path ===")
    for p in sys.path:
        print("  ", p)

    sp = [p for p in sys.path if p and "site-packages" in p.lower()]
    print("\n=== site-packages candidates ===")
    for p in sp:
        print("  ", p)

    print("\n=== listing files/dirs in site-packages that contain 'coin' or 'coinbase' ===")
    for p in sp:
        try:
            for name in sorted(os.listdir(p)):
                if 'coin' in name.lower() or 'coinbase' in name.lower():
                    print("  ", os.path.join(p, name))
        except Exception as e:
            print("   (could not list)", p, ":", e)

    print("\n=== pkgutil visible modules containing 'coin' (first 200) ===")
    try:
        mods = [m.name for m in pkgutil.iter_modules() if 'coin' in m.name.lower()][:200]
        print("  ", mods)
    except Exception as e:
        print("  (pkgutil.iter_modules failed):", e)

    # Common candidate import names (expand if you want)
    candidates = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase",
        "coinbase.client",
        "coinbase_advanced_py.client",
        "coinbase_advanced.client",
        "coinbase.client.client",
    ]

    print("\n=== trying candidate imports ===")
    for c in candidates:
        ok, name, path = try_import(c)
        if ok:
            try:
                with open(OUTPATH, "w") as f:
                    f.write(name)
                print(f"\nWROTE detected import name to {OUTPATH}: {name}")
            except Exception as e:
                print("Could not write detection file:", e)
            # still continue listing other info
    print("\n=== pip metadata scan for distributions with 'coin' in name/summary ===")
    try:
        try:
            import importlib.metadata as md
        except Exception:
            import importlib_metadata as md
        found = False
        for dist in md.distributions():
            meta_name = dist.metadata.get("Name","") or ""
            summary = dist.metadata.get("Summary","") or ""
            if 'coin' in meta_name.lower() or 'coin' in summary.lower():
                found = True
                print("\nFound distribution:", meta_name)
                try:
                    files = list(dist.files or [])[:500]
                    print("  files (first 200):")
                    for f in files[:200]:
                        print("   ", f)
                except Exception as e:
                    print("  (could not list dist files):", e)
        if not found:
            print("  (no distributions found with 'coin' in name/summary)")
    except Exception:
        print("  (importlib.metadata scan failed)")
        traceback.print_exc(limit=0)

    print("\n=== done ===")
    # If an import was written, exit 0; else exit 2 so start.sh knows import failure happened.
    if os.path.exists(OUTPATH):
        sys.exit(0)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
