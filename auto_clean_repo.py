#!/usr/bin/env python3
"""
NIJA_Trading_Bot Full Automatic Cleanup Script
- Cross-platform (Windows, macOS, Linux)
- Handles .gitignore, README, tracked ignored files
- Optimizes repo
- Installs Git LFS if missing
- Pushes changes to GitHub
"""

import os
import subprocess
import sys
import platform

def run(cmd, check=True):
    """Run a shell command and handle errors"""
    print(f"💻 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit(f"❌ Command failed: {cmd}")
    return result

# -------------------------------
# 0️⃣ Detect OS
# -------------------------------
current_os = platform.system()
print(f"🌐 Detected OS: {current_os}")

# -------------------------------
# 1️⃣ Create / Update .gitignore
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
run('git commit -m "Add/update .gitignore" || true')

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
run("git clean -fdx || true")
run("git reflog expire --expire=now --all || true")
run("git gc --prune=now --aggressive || true")

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
run('git commit -m "Add README with project overview and setup instructions" || true')

# -------------------------------
# 6️⃣ Git LFS installation and setup
# -------------------------------
print("💾 Setting up Git LFS...")
git_lfs_installed = subprocess.run("git lfs version", shell=True, capture_output=True).returncode == 0

if not git_lfs_installed:
    print("🔧 Git LFS not detected. Installing...")
    if current_os == "Windows":
        print("⚠️ Please install Git LFS manually from https://git-lfs.com/")
    elif current_os in ["Linux", "Darwin"]:
        run("curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash || true")
        run("sudo apt-get install git-lfs -y || true")
    run("git lfs install || true")
else:
    run("git lfs install || true")

run("git lfs track '*.zip' '*.bin' || true")
run("git add .gitattributes || true")
run('git commit -m "Add Git LFS support for large files" || true')

# -------------------------------
# 7️⃣ Push all changes
# -------------------------------
print("📤 Pushing changes to remote repository...")
run("git push origin main || true")

print("✅ NIJA_Trading_Bot full automatic cleanup completed!")
