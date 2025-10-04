# coinbase_loader.py
"""
Robust Coinbase client auto-discovery.

Exports:
- CLIENT_CLASS: the discovered client class or callable, or None
- CLIENT_MODULE: module path string where it was found (or None)
- DISCOVERY_DEBUG: dict with debug info about attempts
- instantiate_client(**kwargs): try to instantiate discovered client with sensible kwargs
"""

import importlib
import importlib.util
import logging
from typing import Any, Optional, Tuple

log = logging.getLogger(__name__)

CLIENT_CLASS = None
CLIENT_MODULE = None
DISCOVERY_DEBUG = {"attempts": []}

# candidate modules and preferred attribute names
CANDIDATES = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]


def find_likely_client_in_module(m) -> Tuple[Optional[Any], Optional[str]]:
    """
    Inspect module m and return (callable_attr, attr_name) if it looks like a client.
    """
    names = [n for n in dir(m) if not n.startswith("_")]
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    for p in preferred:
        if p in names:
            cand = getattr(m, p)
            if callable(cand):
                return cand, p
    # fallback: any callable with 'client' or 'wallet' in the name
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(m, n)
            if callable(cand):
                return cand, n
    return None, None


for mod_name, attr in CANDIDATES:
    attempt = {"module": mod_name, "spec": None, "imported": False, "selected_attr": None, "error": None}
    try:
        spec = importlib.util.find_spec(mod_name)
        attempt["spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        if spec is None:
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.debug("Spec not found for %s", mod_name)
            continue
        m = importlib.import_module(mod_name)
        attempt["imported"] = True
        # if exact attr exists
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            attempt["selected_attr"] = attr
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.info("Found %s in %s", attr, mod_name)
            break
        # else try to find a likely client attr
        cand, cand_name = find_likely_client_in_module(m)
        if cand:
            CLIENT_CLASS = cand
            CLIENT_MODULE = f"{mod_name}.{cand_name}"
            attempt["selected_attr"] = cand_name
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.info("Auto-selected client-like attribute %s from %s", cand_name, mod_name)
            break
        else:
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.debug("%s imported but no client-like attribute found", mod_name)
    except Exception as e:
        attempt["error"] = repr(e)
        DISCOVERY_DEBUG["attempts"].append(attempt)
        log.debug("Import attempt failed for %s: %s", mod_name, repr(e))


if CLIENT_CLASS is None:
    log.warning("No Coinbase client class found among candidates. Running in diagnostic mode.")
else:
    log.info("Using Coinbase client %s from module %s",
             getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)


def instantiate_client(**kwargs) -> Tuple[Optional[Any], dict]:
    """
    Try to instantiate the discovered client class with several common constructor signatures.

    Returns (instance_or_None, info_dict).
    info_dict contains 'attempts' list and 'success' boolean.
    """
    info = {"attempts": [], "success": False}
    if CLIENT_CLASS is None:
        info["error"] = "No CLIENT_CLASS discovered"
        return None, info

    # common constructor kw names to try (ordered by likelihood)
    tries = [
        {"api_key": kwargs.get("api_key"), "api_secret": kwargs.get("api_secret")},
        {"api_key": kwargs.get("key"), "api_secret": kwargs.get("secret")},
        {"key": kwargs.get("key"), "secret": kwargs.get("secret")},
        {"api_key": kwargs.get("api_key")},  # some libs only need key + env/other
        {},  # try no-arg constructor
    ]

    # also allow passing through full kwargs if user passed them explicitly
    if kwargs:
        tries.insert(0, kwargs)

    for t in tries:
        # filter out None values so we don't pass api_key=None
        kw = {k: v for k, v in (t or {}).items() if v is not None}
        attempt_info = {"kwargs": kw, "error": None}
        try:
            inst = CLIENT_CLASS(**kw) if kw else CLIENT_CLASS()
            attempt_info["instance_repr"] = repr(inst)[:400]
            info["attempts"].append(attempt_info)
            info["success"] = True
            return inst, info
        except TypeError as te:
            attempt_info["error"] = f"TypeError: {repr(te)}"
            info["attempts"].append(attempt_info)
        except Exception as e:
            attempt_info["error"] = repr(e)
            info["attempts"].append(attempt_info)

    info["success"] = False
    return None, info
