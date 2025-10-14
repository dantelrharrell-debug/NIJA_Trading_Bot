#!/usr/bin/env bash
# start.sh - start script for Render
set -e
# Activate virtualenv if available
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi
# Run the bot
python3 nija_bot.py
#!/usr/bin/env bash
set -e
. .venv/bin/activate
python3 nija_bot.py

#!/bin/bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
. .venv/bin/activate
python3 nija_bot.py

#!/bin/bash
# ------------------------------
# start.sh for Render deploy
# ------------------------------

# 1️⃣ Activate virtual environment (create if missing)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2️⃣ Upgrade pip
pip install --upgrade pip

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run main.py
python3 main.py

#!/bin/bash
# ------------------------------
# start.sh for Render deploy
# ------------------------------

# 1️⃣ Activate virtual environment (create if missing)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2️⃣ Upgrade pip
pip install --upgrade pip

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run main.py
python3 main.py

#!/bin/bash
# Activate virtual environment
source .venv/bin/activate

# Run main.py
python3 main.py

#!/usr/bin/env bash
set -eo pipefail

# start.sh - debug + start script for Render
# 1) activate venv
# 2) run debug_import_coinbase.py
# 3) if a working import name was discovered, temporarily patch nija_bot.py to use it and run the bot
# 4) otherwise print logs and exit non-zero so you can inspect deploy output.

VENV=".venv"
PY="$VENV/bin/python3"

echo "==> Using Python: $PY"

if [ ! -x "$PY" ]; then
  echo "❌ Python executable $PY not found. Make sure venv exists and build installed packages."
  exit 1
fi

echo "📦 Installed packages (quick pip freeze head):"
"$PY" -m pip freeze | sed -n '1,120p' || true

echo "🚀 Running debug_import_coinbase.py..."
# Ensure debug script exists
if [ ! -f debug_import_coinbase.py ]; then
  cat > debug_import_coinbase.py <<'PY'
# (creates the debug_import_coinbase.py if missing)
# Paste the same full script content here if you want the start.sh to generate it automatically.
PY
  echo "Wrote placeholder debug_import_coinbase.py - please commit the real file."
  exit 1
fi

# remove any stale file
if [ -f /tmp/coinbase_import_name ]; then
  rm -f /tmp/coinbase_import_name
fi

"$PY" debug_import_coinbase.py || true

if [ -f /tmp/coinbase_import_name ]; then
  FOUND=$(cat /tmp/coinbase_import_name)
  echo "✅ Detected importable module name: $FOUND"

  # Backup original file if not already backed up
  if [ -f nija_bot.py ] && [ ! -f nija_bot.py.bak ]; then
    cp nija_bot.py nija_bot.py.bak
    echo "Backed up nija_bot.py to nija_bot.py.bak"
  fi

  # Create a temporary wrapper that injects the detected import name before starting the bot.
  # This avoids editing the repo permanently.
  TMP_WRAPPER="/tmp/run_nija_bot_wrapper.py"
  cat > "$TMP_WRAPPER" <<PY
# Temporary wrapper that imports detected coinbase module then runs nija_bot.py
import sys, importlib
FOUND = "$FOUND"
try:
    module = importlib.import_module(FOUND)
    print("Imported", FOUND, "->", getattr(module, "__file__", None))
except Exception as e:
    print("Failed to import detected module", FOUND, ":", e)
    raise

# Now execute the real nija_bot.py in same process (so it uses the imported module)
with open("nija_bot.py", "rb") as f:
    code = compile(f.read(), "nija_bot.py", "exec")
    globals_map = {"__name__": "__main__"}
    exec(code, globals_map)
PY

  echo "Starting bot using wrapper..."
  # Run the wrapper with the venv python
  exec "$PY" "$TMP_WRAPPER"
else
  echo "❌ No importable module detected by debug script."
  echo "Check the earlier debug output above in your deploy logs for site-packages contents and pkgutil results."
  exit 1
fi
