# shim_requests_packages_six.py
# Compatibility shim: make requests.packages.urllib3.* point to real urllib3 module
# and expose requests.packages.urllib3.packages.six.moves to six.moves
#
# This is a temporary workaround for old libs that import:
#   requests.packages.urllib3.exceptions
#   requests.packages.urllib3.packages.six.moves
#
import sys
import types

# try to import the modern modules
try:
    import urllib3 as _urllib3
except Exception:
    _urllib3 = None

try:
    import six as _six
except Exception:
    _six = None

# If urllib3 is available, alias requests.packages.urllib3 -> urllib3
if _urllib3 is not None:
    # ensure requests.packages exists as a module
    pkg_requests_packages = sys.modules.get("requests.packages")
    if pkg_requests_packages is None:
        pkg_requests_packages = types.ModuleType("requests.packages")
        sys.modules["requests.packages"] = pkg_requests_packages

    # map requests.packages.urllib3 to the real urllib3 module
    sys.modules["requests.packages.urllib3"] = _urllib3

    # map exceptions module path if urllib3 has it
    if hasattr(_urllib3, "exceptions"):
        sys.modules["requests.packages.urllib3.exceptions"] = _urllib3.exceptions

    # ensure nested packages module exists for 'packages'
    pkg_urllib3_packages = sys.modules.get("requests.packages.urllib3.packages")
    if pkg_urllib3_packages is None:
        pkg_urllib3_packages = types.ModuleType("requests.packages.urllib3.packages")
        sys.modules["requests.packages.urllib3.packages"] = pkg_urllib3_packages

    # If six is available, attach six.moves to the legacy path
    if _six is not None:
        # create a module object for requests.packages.urllib3.packages.six
        mod_six = types.ModuleType("requests.packages.urllib3.packages.six")
        mod_six.moves = _six.moves
        sys.modules["requests.packages.urllib3.packages.six"] = mod_six
        sys.modules["requests.packages.urllib3.packages.six.moves"] = _six.moves

# Fallback: if urllib3 not available, create minimal modules to avoid ImportError
else:
    # create requests.packages and nested structure to avoid "not a package" errors
    pkg_requests_packages = sys.modules.get("requests.packages")
    if pkg_requests_packages is None:
        pkg_requests_packages = types.ModuleType("requests.packages")
        sys.modules["requests.packages"] = pkg_requests_packages

    mod_urllib3 = types.ModuleType("requests.packages.urllib3")
    sys.modules["requests.packages.urllib3"] = mod_urllib3

    mod_excs = types.ModuleType("requests.packages.urllib3.exceptions")
    # create a placeholder DependencyWarning so 'from ... import DependencyWarning' won't fail
    class DependencyWarning(Warning):
        pass
    mod_excs.DependencyWarning = DependencyWarning
    sys.modules["requests.packages.urllib3.exceptions"] = mod_excs

    pkg_urllib3_packages = types.ModuleType("requests.packages.urllib3.packages")
    sys.modules["requests.packages.urllib3.packages"] = pkg_urllib3_packages

    # attach six.moves placeholder if six exists
    if _six is not None:
        mod_six = types.ModuleType("requests.packages.urllib3.packages.six")
        mod_six.moves = _six.moves
        sys.modules["requests.packages.urllib3.packages.six"] = mod_six
        sys.modules["requests.packages.urllib3.packages.six.moves"] = _six.moves
