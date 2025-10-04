import importlib
import importlib.util
import logging

log = logging.getLogger(__name__)
CLIENT_CLASS = None
CLIENT_MODULE = None

# Candidate modules + attribute names
candidates = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]

def find_likely_client_in_module(m):
    """Return a callable class/function that looks like a client in a module."""
    names = [n for n in dir(m) if not n.startswith("_")]
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    
    # Prefer exact names
    for p in preferred:
        if p in names:
            cand = getattr(m, p)
            if callable(cand):
                return cand, p
    # Fallback: any name containing 'client' or 'wallet'
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(m, n)
            if callable(cand):
                return cand, n
    return None, None

# Try all candidates
for mod_name, attr in candidates:
    try:
        spec = importlib.util.find_spec(mod_name)
        if spec is None:
            log.debug("spec not found for %s", mod_name)
            continue

        m = importlib.import_module(mod_name)
        # Exact attribute available
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            log.info("Found %s in %s", attr, mod_name)
            break

        # Otherwise auto-detect
        cand, cand_name = find_likely_client_in_module(m)
        if cand:
            CLIENT_CLASS = cand
            CLIENT_MODULE = f"{mod_name}.{cand_name}"
            log.info("Auto-selected client-like attribute %s from %s", cand_name, mod_name)
            break
        else:
            log.debug("%s imported but no candidate client attr found", mod_name)
    except Exception as e:
        log.debug("Import attempt failed for %s: %s", mod_name, repr(e))

# Final warning if no client found
if CLIENT_CLASS is None:
    log.warning(
        "No Coinbase client class found among candidates. Running in diagnostic mode. "
        "Check if 'coinbase_advanced_py' is installed."
    )
else:
    log.info(
        "Using Coinbase client %s from module %s",
        getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)),
        CLIENT_MODULE
    )

# Safe instantiation helper
def get_coinbase_client(api_key=None, api_secret=None, **kwargs):
    if CLIENT_CLASS is None:
        raise RuntimeError("No Coinbase client class found. Cannot instantiate.")
    return CLIENT_CLASS(api_key=api_key, api_secret=api_secret, **kwargs)
