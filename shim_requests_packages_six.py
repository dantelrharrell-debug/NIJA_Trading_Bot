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
