#!/bin/bash
source .venv/bin/activate
python3 nija_bot.py

#!/bin/bash

# 1️⃣ Activate the virtual environment
source .venv/bin/activate

# 2️⃣ Reinstall packages just to be 100% sure
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt

# 3️⃣ Debug: show which Python and installed packages (optional)
python3 -c "import sys, coinbase_advanced_py; print('Python:', sys.executable); print('Coinbase module loaded:', coinbase_advanced_py.__version__)"

# 4️⃣ Run the bot inside the venv
python3 nija_bot.py
