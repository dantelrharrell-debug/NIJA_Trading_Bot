#!/usr/bin/env python3
"""
NIJA_Trading_Bot Cleanup & Setup Script (Python)
Cleans repo, updates .gitignore, removes tracked ignored files,
adds README, optimizes Git, optionally sets up Git LFS.
"""

import os
import subprocess
import sys

# -------------------------------
# Helper function
# -------------------------------
def run(cmd, check=True):
    print(f"💻 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit(f"❌ Command failed: {cmd}")
    return result

# -------------------------------
# 1️⃣ Update .gitignore
# -------------------------------
gitignore_content = """# Python
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
"""

print("📄 Creating/updating .gitignore...")
with open(".gitignore", "w") as f:
    f.write(gitignore_content)

run("git add .gitignore")
run('git commit -m "Add/update .gitignore"')

# -------------------------------
# 2️⃣ Remove tracked files now ignored
# -------------------------------
print("🗑 Removing files tracked that are now in .gitignore...")
run("git rm --cached $(git ls-files -i -c --exclude-standard) || true")
run('git commit -m "Remove files tracked that are now in .gitignore" || true')

# -------------------------------
# 3️⃣ Optimize repository
# -------------------------------
print("⚡ Optimizing repository...")
run("git clean -fdx")
run("git reflog expire --expire=now --all")
run("git gc --prune=now --aggressive")

# -------------------------------
# 4️⃣ Secure sensitive files
# -------------------------------
if os.path.exists(".env"):
    print("🔒 Found .env. Removing from git history...")
    try:
        run("git filter-repo --path .env --invert-paths")
    except SystemExit:
        print("⚠️ git-filter-repo not installed or failed. Skipping.")

# -------------------------------
# 5️⃣ Add README.md
# -------------------------------
readme_content = """# NIJA_Trading_Bot

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
"""

print("📘 Adding README.md...")
with open("README.md", "w") as f:
    f.write(readme_content)

run("git add README.md")
run('git commit -m "Add README with project overview and setup instructions"')

# -------------------------------
# 6️⃣ Optional: Git LFS
# -------------------------------
print("💾 Setting up Git LFS...")
try:
    run("git lfs install")
    run("git lfs track '*.zip' '*.bin'")
    run("git add .gitattributes")
    run('git commit -m "Add Git LFS support for large files" || true')
except SystemExit:
    print("⚠️ Git LFS not installed or failed. Skipping.")

# -------------------------------
# 7️⃣ Push changes
# -------------------------------
print("📤 Pushing changes to remote...")
run("git push origin main")

print("✅ NIJA_Trading_Bot cleanup & setup completed!")
