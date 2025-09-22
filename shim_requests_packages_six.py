# shim_requests_packages_six.py
# Temporary compatibility shim to recreate the legacy import path:
# requests.packages.urllib3.packages.six.moves
# so older libraries (like cbpro / old urllib3) keep working under newer Python.
import types
import sys

# Try to import six; if not present, this will raise ImportError later when packages import.
import six as _six

# Build a tiny fake package object structure:
_pkg_requests_packages = types.ModuleType("requests.packages")
_pkg_urllib3 = types.ModuleType("requests.packages.urllib3")
_pkg_urllib3_packages = types.ModuleType("requests.packages.urllib3.packages")
_pkg_urllib3_packages_six = types.ModuleType("requests.packages.urllib3.packages.six")

# Attach the six.moves object directly
_pkg_urllib3_packages_six.moves = _six.moves

# Link up the module objects
_pkg_requests_packages.urllib3 = _pkg_urllib3
_pkg_urllib3.packages = _pkg_urllib3_packages
_pkg_urllib3_packages.six = _pkg_urllib3_packages_six

# Inject into sys.modules so importers find it
sys.modules["requests.packages"] = _pkg_requests_packages
sys.modules["requests.packages.urllib3"] = _pkg_urllib3
sys.modules["requests.packages.urllib3.packages"] = _pkg_urllib3_packages
sys.modules["requests.packages.urllib3.packages.six"] = _pkg_urllib3_packages_six
sys.modules["requests.packages.urllib3.packages.six.moves"] = _six.moves
