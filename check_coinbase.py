import sys
import pkgutil
import importlib
import traceback

print("PYTHON:", sys.executable)
print("---SYS.PATH---")
for p in sys.path:
    print(" ", p)

mods = [m.name for m in pkgutil.iter_modules() if 'coin' in m.name.lower()]
print("---MODULES WITH coin---", mods)

importlib.invalidate_caches()

try:
    import coinbase_advanced_py as cb
    print("IMPORT OK:", getattr(cb, '__file__', None))
except Exception:
    traceback.print_exc()
    print("IMPORT FAILED")
