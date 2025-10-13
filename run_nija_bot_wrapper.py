#!/usr/bin/env python3
"""
run_nija_bot_wrapper.py - robust aliasing wrapper

Put this at the project root (next to nija_bot.py) and run it instead of
running nija_bot.py directly. It will try to make `import coinbase_advanced_py`
succeed by aliasing whatever Coinbase-ish package is actually installed.
"""

import sys
import importlib
import pkgutil
import os
import shutil
import traceback
from types import ModuleType

ROOT = os.path.abspath(os.path.dirname(__file__))
BOT_FILENAME = os.path.join(ROOT, "nija_bot.py")
BACKUP_FILENAME = os.path.join(ROOT, "nija_bot.py.bak")

def try_import(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None

def find_installed_coinbase_like():
    # Preferred names exactly
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    for n in names:
        m = try_import(n)
        if m:
            return n, m
    # Fallback: search for top-level modules containing "coin" or "coinbase"
    for minfo in pkgutil.iter_modules():
        nm = (minfo.name or "").lower()
        if "coin" in nm or "coinbase" in nm:
            m = try_import(minfo.name)
            if m:
                return minfo.name, m
    return None, None

def create_alias_module(alias_name, source_mod):
    """
    Create a ModuleType with name alias_name and copy public attributes
    from source_mod. Also attempt to find a 'Client' class in common places
    and attach it to the alias module to satisfy `from coinbase_advanced_py import Client`.
    """
    alias = ModuleType(alias_name)
    # Basic metadata
    alias.__file__ = getattr(source_mod, "__file__", None)
    alias.__package__ = alias_name

    # Copy public attributes
    for attr in dir(source_mod):
        if attr.startswith("_"):
            continue
        try:
            setattr(alias, attr, getattr(source_mod, attr))
        except Exception:
            # ignore attributes we can't copy
            pass

    # If no Client symbol, attempt to discover it in known submodules
    if not hasattr(alias, "Client"):
        tried = []
        candidates = [
            "coinbase.rest.client",
            "coinbase.client",
            "coinbase.client.client",
            "coinbase.rest",
            "coinbase_advanced.client",
            "coinbase_advanced.rest.client",
        ]
        for sub in candidates:
            try:
                submod = importlib.import_module(sub)
                # look for Client in the submodule
                if hasattr(submod, "Client"):
                    alias.Client = getattr(submod, "Client")
                    tried.append(sub)
                    break
            except Exception:
                tried.append(sub)
                continue

    return alias

def main():
    print("🔍 Wrapper: scanning installed packages for coinbase module...")
    found_name, found_mod = find_installed_coinbase_like()
    if not found_mod:
        print("❌ No coinbase-like module found in the environment.")
        print("Installed top-level modules (first 200):")
        print([m.name for m in pkgutil.iter_modules()][:200])
        sys.exit(1)

    print(f"✅ Found installed package: '{found_name}' -> {getattr(found_mod, '__file__', None)}")

    # If coinbase_advanced_py is importable already, nothing to do
    if try_import("coinbase_advanced_py"):
        print("ℹ️ 'coinbase_advanced_py' is already importable. Running bot directly.")
    else:
        print("➡️ Creating alias module 'coinbase_advanced_py' in sys.modules ...")
        alias = create_alias_module("coinbase_advanced_py", found_mod)
        # preserve original under a debug name
        sys.modules[f"__orig_{found_name}__"] = found_mod
        # set alias
        sys.modules["coinbase_advanced_py"] = alias
        print("✅ sys.modules patched: 'coinbase_advanced_py' -> alias module")

        # Extra verification prints for debugging
        try:
            import importlib
            importlib.invalidate_caches()
            test = importlib.import_module("coinbase_advanced_py")
            print("🔬 Test import successful. coinbase_advanced_py ->", getattr(test, "__file__", None))
            if hasattr(test, "Client"):
                print("🔧 'Client' is present on alias module.")
            else:
                print("⚠️ 'Client' not found on alias module. If your code does `from coinbase_advanced_py import Client`,")
                print("   you may need to add a specific import path. Tell me the exact import line and I will adapt.")
        except Exception:
            print("‼️ Test import failed even after aliasing. Continuing to exec the bot (you'll see errors).")

    # Backup bot file (best effort)
    if os.path.exists(BOT_FILENAME):
        try:
            shutil.copy2(BOT_FILENAME, BACKUP_FILENAME)
            print(f"💾 Backed up '{BOT_FILENAME}' -> '{BACKUP_FILENAME}'")
        except Exception as e:
            print("⚠️ Could not back up nija_bot.py:", e)

    # Execute nija_bot.py in current process
    if not os.path.exists(BOT_FILENAME):
        print("❌ nija_bot.py not found at expected path:", BOT_FILENAME)
        sys.exit(1)

    print("▶️ Executing nija_bot.py now (will run in current process).")
    try:
        with open(BOT_FILENAME, "rb") as f:
            code = compile(f.read(), BOT_FILENAME, "exec")
            globals_map = {"__name__": "__main__", "__file__": BOT_FILENAME}
            exec(code, globals_map)
    except SystemExit:
        raise
    except Exception:
        print("❌ Exception while executing nija_bot.py:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
