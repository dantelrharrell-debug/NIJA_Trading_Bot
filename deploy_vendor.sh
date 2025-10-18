#!/bin/bash
set -e

# -----------------------------
# CONFIG — replace with your GitHub PAT
# -----------------------------
GITHUB_PAT="ghp_11BXO73GQ0NyZijomU2x1x_3Z1m6cQbQL0PxmTqWRhLQ7dNrcJSt5hdmr20H2maT2iBF47SUPF7KfKMWqx"
GITHUB_REPO="dantelrharrell-debug/NIJA_Trading_Bot"
BRANCH="main"

# -----------------------------
# 1️⃣ Ensure directories
# -----------------------------
mkdir -p vendor vendor_tmp

# -----------------------------
# 2️⃣ Download coinbase_advanced_py wheel (no dependencies)
# -----------------------------
cd vendor_tmp
python3 -m pip download coinbase-advanced-py==1.8.2 --no-deps -d .

# -----------------------------
# 3️⃣ Extract wheel
# -----------------------------
WHL_FILE=$(ls | grep coinbase_advanced_py | head -n1)
if [ -z "$WHL_FILE" ]; then
    echo "❌ Wheel not found!"
    exit 1
fi

mkdir -p coinbase_advanced_py
unzip -o "$WHL_FILE" -d coinbase_advanced_py

# -----------------------------
# 4️⃣ Move extracted package into repo vendor folder
# -----------------------------
cp -r coinbase_advanced_py ../vendor/
cd ..

# -----------------------------
# 5️⃣ Cleanup temp folder
# -----------------------------
rm -rf vendor_tmp

# -----------------------------
# 6️⃣ Verify contents
# -----------------------------
echo "✅ Contents of vendor/coinbase_advanced_py:"
ls -la vendor/coinbase_advanced_py | head -n20

# -----------------------------
# 7️⃣ Git add & commit
# -----------------------------
git add nija_bot.py start.sh vendor/coinbase_advanced_py
git commit -m "Vendored coinbase_advanced_py and clean startup" || echo "Nothing to commit"

# -----------------------------
# 8️⃣ Push using PAT (non-interactive)
# -----------------------------
git remote set-url origin https://$GITHUB_PAT@github.com/$GITHUB_REPO.git
git push origin $BRANCH

# -----------------------------
# 9️⃣ Done
# -----------------------------
echo "✅ Vendoring, commit, and push complete! You can now deploy."
