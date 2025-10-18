# debug_coinbase_import.py
import importlib, pkgutil, inspect, sys, traceback

candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
found = []

def search_module(mod):
    results = []
    # scan attributes
    for name in dir(mod):
        try:
            obj = getattr(mod, name)
        except Exception:
            continue
        if inspect.isclass(obj) and name.lower() == "client":
            results.append((f"{mod.__name__}.{name}", obj))
    # scan submodules
    for finder, name, ispkg in pkgutil.iter_modules(mod.__path__ if hasattr(mod, "__path__") else []):
        fullname = f"{mod.__name__}.{name}"
        try:
            sub = importlib.import_module(fullname)
            for nm in dir(sub):
                try:
                    o = getattr(sub, nm)
                except Exception:
                    continue
                if inspect.isclass(o) and nm.lower() == "client":
                    results.append((f"{fullname}.{nm}", o))
        except Exception:
            pass
    return results

print("sys.path:", sys.path)
for cand in candidates:
    try:
        m = importlib.import_module(cand)
        print(f"\nFound module: {cand} -> {getattr(m,'__file__',None)}")
        res = search_module(m)
        if res:
            for rname, cls in res:
                print("  -> Client class found at:", rname)
        else:
            print("  -> No Client class discovered directly under", cand)
        found.append(cand)
    except Exception:
        print(f"\nCannot import {cand} (skipping)")

# also search all installed top-level packages containing 'coin'
print("\nScanning top-level modules containing 'coin' in their name (first 200):")
for info in pkgutil.iter_modules():
    if "coin" in (info.name or "").lower():
        print("  candidate:", info.name)
        try:
            m = importlib.import_module(info.name)
            res = search_module(m)
            if res:
                for rname, cls in res:
                    print("    -> Client class found at:", rname)
        except Exception:
            pass
