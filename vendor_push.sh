#!/bin/bash
set -e

# -----------------------------
# 0️⃣ CONFIG — replace with your GitHub PAT
# -----------------------------
GITHUB_PAT="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"
GITHUB_REPO="dantelrharrell-debug/NIJA_Trading_Bot"
BRANCH="main"

# -----------------------------
# 1️⃣ Ensure directories
# -----------------------------
mkdir -p vendor vendor_tmp
cd vendor_tmp

# -----------------------------
# 2️⃣ Download coinbase_advanced_py wheel (no dependencies)
# -----------------------------
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
# 6️⃣ Git add & commit
# -----------------------------
git add vendor/coinbase_advanced_py
git commit -m "Vendored coinbase_advanced_py for Render deployment" || echo "⚠️ Nothing to commit"

# -----------------------------
# 7️⃣ Rebase local main with remote
# -----------------------------
git fetch https://$GITHUB_PAT@github.com/$GITHUB_REPO.git $BRANCH
git rebase FETCH_HEAD || git rebase --abort

# -----------------------------
# 8️⃣ Push safely
# -----------------------------
git push https://$GITHUB_PAT@github.com/$GITHUB_REPO.git $BRANCH

# -----------------------------
# ✅ Done
# -----------------------------
echo "✅ Vendoring, commit, rebase, and push complete!"
