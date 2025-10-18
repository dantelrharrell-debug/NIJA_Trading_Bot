#!/usr/bin/env python3
# run_nija_bot_wrapper.py
# Force-create sys.modules["coinbase_advanced_py"] so nija_bot.py can import it.

import sys
import os
import importlib
import pkgutil
import shutil
import traceback
from types import ModuleType

ROOT = os.path.abspath(os.path.dirname(__file__))
BOT = os.path.join(ROOT, "nija_bot.py")
BACKUP = os.path.join(ROOT, "nija_bot.py.bak")

def find_candidate():
    # Preferred names in order
    for name in ("coinbase_advanced_py", "coinbase_advanced", "coinbase"):
        try:
            m = importlib.import_module(name)
            return name, m
        except Exception:
            continue
    # Fallback: search top-level modules for "coin" string
    for info in pkgutil.iter_modules():
        if "coin" in (info.name or "").lower():
            try:
                m = importlib.import_module(info.name)
                return info.name, m
            except Exception:
                continue
    return None, None

def attach_client_if_missing(alias_mod, source_mod):
    # If 'Client' already present, done.
    if hasattr(alias_mod, "Client"):
        return True
    # Search common places for Client
    candidates = [
        "client",
        "rest.client",
        "rest",
        "websocket",
        "client.client",
        "rest.client.client",
    ]
    # Try source_mod and its submodules
    for c in candidates:
        try:
            subname = f"{source_mod.__name__}.{c}"
            sub = importlib.import_module(subname)
            if hasattr(sub, "Client"):
                alias_mod.Client = getattr(sub, "Client")
                return True
        except Exception:
            pass
    # Also try scanning attributes for something named Client
    for attr in dir(source_mod):
        if attr.lower() == "client" or "client" in attr.lower():
            try:
                val = getattr(source_mod, attr)
                if hasattr(val, "Client"):
                    alias_mod.Client = getattr(val, "Client")
                    return True
            except Exception:
                pass
    return False

def create_alias(name, source):
    alias = ModuleType(name)
    alias.__file__ = getattr(source, "__file__", None)
    alias.__package__ = name
    # copy top-level public attributes
    for k in dir(source):
        if k.startswith("_"):
            continue
        try:
            setattr(alias, k, getattr(source, k))
        except Exception:
            pass
    # try to ensure Client exists if it will be imported
    attach_client_if_missing(alias, source)
    return alias

def main():
    print("🔍 Wrapper starting: ensuring coinbase_advanced_py is importable...")
    found_name, found_mod = find_candidate()
    if not found_mod:
        print("❌ Could not find any installed coin/coinbase package.")
        print("Installed modules (first 200):", [m.name for m in pkgutil.iter_modules()][:200])
        sys.exit(1)

    print(f"✅ Found installed package: {found_name} -> {getattr(found_mod,'__file__',None)}")

    # If coinbase_advanced_py already importable, show and continue
    try:
        import coinbase_advanced_py  # noqa: F401
        print("ℹ️ coinbase_advanced_py already importable; running bot normally.")
    except Exception:
        # Create alias module and insert into sys.modules BEFORE running bot
        print("➡️ Creating alias sys.modules['coinbase_advanced_py'] -> installed package object")
        alias = create_alias("coinbase_advanced_py", found_mod)
        # also keep the original module available for debugging
        sys.modules[f"__orig_{found_name}__"] = found_mod
        sys.modules["coinbase_advanced_py"] = alias
        # sanity check
        try:
            import importlib
            importlib.invalidate_caches()
            t = importlib.import_module("coinbase_advanced_py")
            print("🔬 Test import OK:", getattr(t, "__file__", None))
            print("🔧 Has Client?:", hasattr(t, "Client"))
        except Exception:
            print("⚠️ Test import failed after aliasing (this is unexpected).")
            traceback.print_exc()

    # Backup bot
    if os.path.exists(BOT):
        try:
            shutil.copy2(BOT, BACKUP)
            print(f"💾 Backed up {BOT} -> {BACKUP}")
        except Exception:
            print("⚠️ Could not back up bot (permissions?)")

    # Execute bot in-process so imports use our sys.modules patch
    if not os.path.exists(BOT):
        print("❌ nija_bot.py not found at:", BOT)
        sys.exit(1)

    print("▶️ Executing nija_bot.py (imports will use patched sys.modules)...\n")
    try:
        with open(BOT, "rb") as f:
            code = compile(f.read(), BOT, "exec")
            globals_map = {"__name__": "__main__", "__file__": BOT}
            exec(code, globals_map)
    except SystemExit:
        raise
    except Exception:
        print("❌ Exception while running nija_bot.py:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
