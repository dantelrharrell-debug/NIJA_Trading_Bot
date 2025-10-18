# inspect_coinbase.py
import importlib, pkgutil, inspect, traceback

roots = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]

def scan_module(name):
    try:
        m = importlib.import_module(name)
    except Exception as e:
        print(f"IMPORT FAILED: {name!r}: {e}")
        return
    print(f"\nIMPORT OK: {name!r} -> {getattr(m,'__file__',None)}")
    # direct Client attribute?
    if hasattr(m, "Client"):
        print(f" FOUND: {name}.Client (top-level)")
    # list classes in top-level
    for attr in dir(m):
        try:
            obj = getattr(m, attr)
        except Exception:
            continue
        if inspect.isclass(obj) and attr.lower() == "client":
            print(f" FOUND class at top-level: {name}.{attr}")
    # search submodules (one level)
    if hasattr(m, "__path__"):
        for finder, subname, ispkg in pkgutil.iter_modules(m.__path__):
            fullname = f"{name}.{subname}"
            try:
                sub = importlib.import_module(fullname)
            except Exception:
                continue
            for attr in dir(sub):
                try:
                    obj = getattr(sub, attr)
                except Exception:
                    continue
                if inspect.isclass(obj) and attr.lower() == "client":
                    print(f" FOUND class: {fullname}.{attr}")
            # also show if sub exports Client attr
            if hasattr(sub, "Client"):
                print(f" FOUND: {fullname}.Client")

for root in roots:
    scan_module(root)

print("\nDone scanning.")
