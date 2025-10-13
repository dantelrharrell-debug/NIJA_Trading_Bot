import sys
import pkgutil
import importlib
import traceback

print("=== PYTHON ===")
print(sys.executable)

print("\n=== SYS.PATH ===")
for p in sys.path:
    print(" ", p)

print("\n=== MODULES CONTAINING 'coin' ===")
mods = [m.name for m in pkgutil.iter_modules() if 'coin' in m.name.lower()]
for m in mods:
    print(" ", m)

print("\n=== TRY IMPORT coinbase_advanced_py ===")
try:
    import coinbase_advanced_py as cb
    print("IMPORT OK:", getattr(cb, '__file__', None))
except Exception:
    traceback.print_exc()
    print("IMPORT FAILED")
    exit(1)
