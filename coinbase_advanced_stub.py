# coinbase_advanced_py.py
# shim so code that does `import coinbase_advanced_py` finds the installed `coinbase` package

try:
    import coinbase as _coinbase_pkg
except Exception as e:
    # re-raise so failures are visible
    raise

# Re-export everything from the coinbase package (so old imports still work)
from coinbase import *  # noqa: F401,F403

# optional: expose __all__ if the wrapped package defines it
__all__ = getattr(_coinbase_pkg, "__all__", [])
