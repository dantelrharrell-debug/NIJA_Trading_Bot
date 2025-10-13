import sys
import pkgutil
import importlib
import traceback

print("=== PYTHON ===")
print(sys.executable)

print("\n=== SYS.PATH ===")
for p in sys.path:
    print(p)

print("\n=== MODULES WITH 'coin' ===")
for m in pkgutil.iter_modules():
    if 'coin' in m.name.lower():
        print(m.name)

print("\n=== TRY IMPORT coinbase_advanced_py ===")
try:
    import coinbase_advanced_py as cb
    print("IMPORT OK:", getattr(cb, "__file__", None))
except Exception:
    traceback.print_exc()
    print("IMPORT FAILED")
    exit(1)
