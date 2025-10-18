#!/bin/bash
set -e

# -----------------------------
# 1️⃣ Generate SSH key if none exists
# -----------------------------
SSH_KEY="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY" ]; then
    echo "🔑 Generating new SSH key..."
    ssh-keygen -t ed25519 -C "replit@NIJA_Bot" -f "$SSH_KEY" -N ""
else
    echo "🔑 SSH key already exists, skipping generation."
fi

# -----------------------------
# 2️⃣ Show public key (copy to GitHub)
# -----------------------------
echo "📋 Copy the following SSH public key and add it to GitHub -> Settings -> SSH keys -> New SSH key"
cat "${SSH_KEY}.pub"
echo
read -p "Press Enter after adding the SSH key to GitHub..."

# -----------------------------
# 3️⃣ Configure git to use SSH
# -----------------------------
git remote set-url origin git@github.com:dantelrharrell-debug/NIJA_Trading_Bot.git

# -----------------------------
# 4️⃣ Ensure vendor folder is tracked
# -----------------------------
git add vendor/coinbase_advanced_py nija_bot.py start.sh
git commit -m "Vendored coinbase_advanced_py for Render deployment" || echo "Nothing to commit"

# -----------------------------
# 5️⃣ Push to GitHub
# -----------------------------
git push origin main

echo "✅ SSH push complete! You can now deploy on Render."
