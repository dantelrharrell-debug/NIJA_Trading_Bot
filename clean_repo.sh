#!/bin/bash
# ============================================
# NIJA_Trading_Bot Cleanup & Setup Script
# ============================================

set -e  # Exit on error

echo "🚀 Starting NIJA_Trading_Bot cleanup..."

# -------------------------------
# 1️⃣ Add / Update .gitignore
# -------------------------------
echo "📄 Creating/updating .gitignore..."
cat > .gitignore <<EOL
# Python
__pycache__/
*.py[cod]
*.pyo
*.env

# Logs
*.log

# Virtual environments
.venv/
env/

# Node.js dependencies
node_modules/

# OS Files
.DS_Store
Thumbs.db

# IDEs
.vscode/
.idea/
EOL

git add .gitignore
git commit -m "Add/update .gitignore"

# -------------------------------
# 2️⃣ Remove tracked files now ignored
# -------------------------------
echo "🗑 Removing files tracked that are now in .gitignore..."
git rm --cached $(git ls-files -i -c --exclude-standard) || true
git commit -m "Remove files tracked that are now in .gitignore" || true

# -------------------------------
# 3️⃣ Optimize repository
# -------------------------------
echo "⚡ Optimizing repository..."
git clean -fdx
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# -------------------------------
# 4️⃣ Secure sensitive files
# -------------------------------
echo "🔒 Checking for .env or sensitive files..."
if [ -f ".env" ]; then
    echo "⚠️ Found .env file. Removing from git history using git-filter-repo..."
    git filter-repo --path .env --invert-paths || echo "git-filter-repo not installed. Skipping secure removal."
fi

# -------------------------------
# 5️⃣ Add README.md
# -------------------------------
echo "📘 Adding README.md..."
cat > README.md <<EOL
# NIJA_Trading_Bot

Automated aggressive-but-safe trading bot for crypto.

## Features
- Multi-symbol support
- High-frequency micro-trades
- Dynamic position sizing
- Webhook-enabled
- 24/7 trading

## Setup
1. Clone the repo
2. Create a virtual environment
3. Install dependencies
4. Set API keys in .env
5. Run the bot
EOL

git add README.md
git commit -m "Add README with project overview and setup instructions"

# -------------------------------
# 6️⃣ Optional: Git LFS for large files
# -------------------------------
echo "💾 Setting up Git LFS for large files..."
if ! command -v git-lfs &> /dev/null
then
    echo "Git LFS not installed. Installing..."
    git lfs install
fi

git lfs track "*.zip" "*.bin" || true
git add .gitattributes || true
git commit -m "Add Git LFS support for large files" || true

# -------------------------------
# 7️⃣ Push all changes
# -------------------------------
echo "📤 Pushing changes to remote..."
git push origin main

echo "✅ NIJA_Trading_Bot cleanup & setup completed!"
