import importlib
import importlib.util
import logging

LOG = logging.getLogger("all_in_one_bot")

def try_import_coinbase():
    """
    Robust runtime importer:
    - Inspect installed distributions with importlib.metadata for any dist with 'coinbase' in the dist name.
    - Read their top_level.txt to get actual importable package names.
    - Try to import those packages and look for sensible client constructors/attributes.
    Returns (client_instance_or_None, attempts_dict).
    """
    attempts = {}
    client = None

    # Candidate fallback names (legacy)
    fallback_candidates = [
        ("coinbase_advanced_py", "Client"),
        ("coinbase_advanced", "Client"),
        ("coinbase", "Client"),
        ("coinbase.wallet.client", "Client"),
    ]

    # 1) Try distributions in importlib.metadata that contain 'coinbase'
    try:
        try:
            from importlib import metadata as importlib_metadata  # py3.8+
        except Exception:
            import importlib_metadata as importlib_metadata  # type: ignore

        for dist in importlib_metadata.distributions():
            dist_name = dist.metadata.get("Name", "") or dist.metadata.get("name", "")
            if not dist_name:
                continue
            if "coinbase" not in dist_name.lower():
                continue

            # record distribution
            attempts[f"dist:{dist_name}"] = {"status": "found_distribution"}

            # try top_level.txt (names of top-level packages)
            try:
                top = dist.read_text("top_level.txt")
                if top:
                    top_levels = [s.strip() for s in top.splitlines() if s.strip()]
                else:
                    top_levels = []
                attempts[f"dist:{dist_name}"]["top_level"] = top_levels
            except Exception as e:
                attempts[f"dist:{dist_name}"]["top_level"] = []
                attempts[f"dist:{dist_name}"]["top_level_error"] = repr(e)
                top_levels = []

            # try to import each top level module
            for pkg in top_levels:
                try:
                    spec = importlib.util.find_spec(pkg)
                    if spec is None:
                        attempts[f"dist:{dist_name}"][pkg] = {"status": "not_found_by_find_spec"}
                        continue
                    module = importlib.import_module(pkg)
                    attempts[f"dist:{dist_name}"][pkg] = {"status": "imported"}
                    # try common Client attr names
                    for attr in ("Client", "client", "CoinbaseAdvancedClient"):
                        if hasattr(module, attr):
                            ClientClass = getattr(module, attr)
                            try:
                                client = ClientClass(os.getenv("API_KEY"), os.getenv("API_SECRET"))
                                attempts[f"dist:{dist_name}"][pkg]["instantiated_via"] = attr
                                LOG.info("Instantiated client from %s -> %s", dist_name, pkg)
                                return client, attempts
                            except Exception as e:
                                attempts[f"dist:{dist_name}"][pkg]["instantiation_error"] = repr(e)
                except Exception as e:
                    attempts[f"dist:{dist_name}"][pkg] = {"status": "import_failed", "detail": repr(e)}
    except Exception as e:
        LOG.exception("importlib.metadata scan failed: %s", e)
        attempts["importlib_metadata_scan_error"] = repr(e)

    # 2) If none found by distributions, try fallback candidate strings
    for mod_name, attr in fallback_candidates:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                attempts[mod_name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue
            module = importlib.import_module(mod_name)
            attempts[mod_name] = {"status": "imported"}
            if hasattr(module, attr):
                ClientClass = getattr(module, attr)
                try:
                    client = ClientClass(os.getenv("API_KEY"), os.getenv("API_SECRET"))
                    attempts[mod_name]["client_instantiated"] = True
                    return client, attempts
                except Exception as e:
                    attempts[mod_name]["client_error"] = repr(e)
            else:
                attempts[mod_name]["has_attr"] = False
        except Exception as e:
            attempts[mod_name] = {"status": "import_failed", "detail": repr(e)}

    return client, attempts all_in_one_bot.
