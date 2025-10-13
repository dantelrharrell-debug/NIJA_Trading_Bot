# inspect_coinbase.py
import importlib, pkgutil, inspect, traceback

candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]

for name in candidates:
    try:
        m = importlib.import_module(name)
    except Exception as e:
        print(f"IMPORT FAILED: {name!r}: {e}")
        continue

    print(f"IMPORT OK: {name!r} -> {getattr(m,'__file__',None)}")
    # list Client-like names
    for nm in dir(m):
        try:
            obj = getattr(m, nm)
        except Exception:
            continue
        if inspect.isclass(obj) and nm.lower() == "client":
            print(f" FOUND class: {name}.{nm}")
    # try to find Client in submodules (shallow)
    if hasattr(m, "__path__"):
        for finder, subname, ispkg in pkgutil.iter_modules(m.__path__):
            fullname = f"{name}.{subname}"
            try:
                sub = importlib.import_module(fullname)
            except Exception:
                continue
            for nm in dir(sub):
                try:
                    obj = getattr(sub, nm)
                except Exception:
                    continue
                if inspect.isclass(obj) and nm.lower() == "client":
                    print(f" FOUND class: {fullname}.{nm}")

print("done")
