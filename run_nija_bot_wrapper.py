#!/usr/bin/env python3
"""
run_nija_bot_wrapper.py

Wrapper to make code that does `import coinbase_advanced_py as cb`
work even when pip installed package exposes a different top-level
name (e.g. `coinbase`).

Behavior:
 - Try to import coinbase_advanced_py directly.
 - If that fails, try a list of likely alternative names.
 - If an alternative is found, alias it into sys.modules as
   'coinbase_advanced_py' so existing imports succeed.
 - Back up nija_bot.py to nija_bot.py.bak (only once per run).
 - Exec nija_bot.py in the same process so you get normal exception traces.
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
        mod = importlib.import_module(name)
        return mod
    except Exception:
        return None

def find_candidate_module():
    # First try the exact name the code expects
    candidates = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase",
        # scan other modules that contain 'coinbase' as a fallback
    ]

    for name in candidates:
        mod = try_import(name)
        if mod:
            return name, mod

    # If none of the above worked, scan installed modules for 'coin' or 'coinbase' matches
    for m in pkgutil.iter_modules():
        nm = (m.name or "").lower()
        if "coin" in nm or "coinbase" in nm:
            mod = try_import(m.name)
            if mod:
                return m.name, mod

    return None, None

def main():
    print("🔍 Wrapper: checking for coinbase_advanced_py or an equivalent module...")
    # Try direct import first
    direct = try_import("coinbase_advanced_py")
    if direct:
        print("✅ 'coinbase_advanced_py' already importable:", getattr(direct, "__file__", None))
    else:
        found_name, found_mod = find_candidate_module()
        if not found_mod:
            print("❌ Could not find any coinbase-related module installed.")
            print("Installed top-level modules (first 200):")
            print([m.name for m in pkgutil.iter_modules()][:200])
            print("\nPlease ensure the correct package is in requirements.txt or update your import.")
            sys.exit(1)

        print(f"ℹ️ Found installed Coinbase module: '{found_name}' -> {getattr(found_mod, '__file__', None)}")
        # Insert alias into sys.modules so `import coinbase_advanced_py` resolves to the found module
        sys.modules["coinbase_advanced_py"] = found_mod
        # Also create a shallow ModuleType in case code expects top-level symbols to be directly in that module
        # (but most times mapping sys.modules to the same module is sufficient)
        try:
            alias_mod = ModuleType("coinbase_advanced_py")
            # copy attributes from found_mod onto alias_mod for top-level access if needed
            for attr in dir(found_mod):
                # skip private internals to be safe
                if attr.startswith("_"):
                    continue
                try:
                    setattr(alias_mod, attr, getattr(found_mod, attr))
                except Exception:
                    pass
            sys.modules["coinbase_advanced_py"] = alias_mod
            # keep a reference to original under a different name so nothing is lost
            sys.modules[f"__orig_{found_name}__"] = found_mod
            print("➡️ Aliased", found_name, "as coinbase_advanced_py (sys.modules patched).")
        except Exception:
            # fallback: at least put the original module object in place
            sys.modules["coinbase_advanced_py"] = found_mod
            print("➡️ Aliased original module object as coinbase_advanced_py (fallback).")

    # Backup original bot file (if exists)
    if os.path.exists(BOT_FILENAME):
        try:
            shutil.copy2(BOT_FILENAME, BACKUP_FILENAME)
            print(f"💾 Backed up '{BOT_FILENAME}' -> '{BACKUP_FILENAME}'")
        except Exception as e:
            print("⚠️ Could not back up nija_bot.py:", e)

    # Execute the bot script in this process so exceptions are clear
    if not os.path.exists(BOT_FILENAME):
        print("❌ nija_bot.py not found at expected path:", BOT_FILENAME)
        sys.exit(1)

    print("▶️ Starting nija_bot.py ... (this will run in the current process)")
    try:
        # Execute the bot file in a fresh globals map (so it behaves like normal script)
        with open(BOT_FILENAME, "rb") as f:
            code = compile(f.read(), BOT_FILENAME, 'exec')
            globals_map = {"__name__": "__main__", "__file__": BOT_FILENAME}
            exec(code, globals_map)
    except SystemExit:
        raise
    except Exception:
        print("❌ Exception while executing nija_bot.py:")
        traceback.print_exc()
        # keep exit code non-zero so Render shows failure
        sys.exit(1)

if __name__ == "__main__":
    main()
