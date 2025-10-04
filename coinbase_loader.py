# coinbase_loader.py
"""
Robust Coinbase client auto-discovery.
Place this in your project and import `get_coinbase_client_class()`
or `get_coinbase_client()` from it instead of `from coinbase_advanced_py import Client`.
"""

import importlib
import importlib.util
import logging
import os
from typing import Optional, Tuple, Any, Callable

log = logging.getLogger(__name__)

CANDIDATE_MODULES = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]

def _find_likely_client_in_module(module) -> Tuple[Optional[Callable], Optional[str]]:
    """Look for something that looks like a client in module and return (callable, name)."""
    names = [n for n in dir(module) if not n.startswith("_")]
    # prefer explicit common names
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    for p in preferred:
        if p in names:
            cand = getattr(module, p)
            if callable(cand):
                return cand, p
    # fallback: find any callable with 'client' or 'wallet' in its name
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(module, n)
            if callable(cand):
                return cand, n
    return None, None

def get_coinbase_client_class() -> Tuple[Optional[Callable], Optional[str]]:
    """
    Attempts to locate a Coinbase client class/function in a variety of module names.
    Returns (client_class_or_factory, module_path_name) or (None, None) if nothing found.
    """
    for mod_name, attr_name in CANDIDATE_MODULES:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                log.debug("Spec not found for %s", mod_name)
                continue
            m = importlib.import_module(mod_name)
            # prefer explicit attribute if present
            if hasattr(m, attr_name):
                cand = getattr(m, attr_name)
                if callable(cand):
                    log.info("Found Coinbase client attribute %s in %s", attr_name, mod_name)
                    return cand, f"{mod_name}.{attr_name}"
            # attempt to auto-detect a client-like member
            cand, name = _find_likely_client_in_module(m)
            if cand:
                log.info("Auto-selected client-like attribute %s from %s", name, mod_name)
                return cand, f"{mod_name}.{name}"
            log.debug("%s imported but no client-like attr found", mod_name)
        except Exception as e:
            log.debug("Import attempt failed for %s: %s", mod_name, repr(e))
    log.warning("No Coinbase client class found among candidates.")
    return None, None

def get_coinbase_client(**override_kwargs) -> Tuple[Optional[Any], Optional[str], Optional[Exception]]:
    """
    Returns a tuple (client_instance, client_id, error).
    If client_instance is None and error is not None, instantiation failed or no client discovered.
    override_kwargs can be passed to the client constructor (e.g. api_key, api_secret,...).
    It will also look for ENV VARs (COINBASE_API_KEY, COINBASE_API_SECRET, COINBASE_PASSPHRASE) as default.
    """
    ClientClass, client_identifier = get_coinbase_client_class()
    if ClientClass is None:
        return None, None, None

    # collect common env var names; keep optional
    env_kwargs = {}
    if "api_key" in ClientClass.__init__.__code__.co_varnames:
        # best-effort hint; we still pass whatever we have
        pass
    # standard env names (optional)
    for k in ("COINBASE_API_KEY", "COINBASE_API_SECRET", "COINBASE_PASSPHRASE", "COINBASE_API_PASSPHRASE", "COINBASE_TOKEN"):
        if k in os.environ:
            env_key = k.lower()
            env_kwargs[env_key] = os.environ[k]

    # merge override_kwargs -> env_kwargs -> {} (override wins)
    # but keep names consistent: user likely passes api_key/api_secret -> use those.
    final_kwargs = {}
    final_kwargs.update(env_kwargs)
    final_kwargs.update(override_kwargs)

    try:
        instance = ClientClass(**final_kwargs) if final_kwargs else ClientClass()
        log.info("Instantiated Coinbase client from %s", client_identifier)
        return instance, client_identifier, None
    except Exception as e:
        log.exception("Failed to instantiate Coinbase client %s: %s", client_identifier, e)
        return None, client_identifier, e
