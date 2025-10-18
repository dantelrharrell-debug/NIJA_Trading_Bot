#!/usr/bin/env python3
"""
NIJA_Trading_Bot Silent Cleanup Script
- Fully automated, cross-platform
- No verbose output (silent mode)
- Handles .gitignore, README, tracked ignored files
- Optimizes repo
- Installs Git LFS if missing
- Pushes changes to GitHub
"""

import os
import subprocess
import platform

def run(cmd, ignore_errors=True):
    """Run a shell command silently"""
    return subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)

# Detect OS
current_os = platform.system()

# 1️⃣ Create / Update .gitignore
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
with open(".gitignore", "w") as f:
    f.write(gitignore_content)
run("git add .gitignore")
run('git commit -m "Add/update .gitignore"', ignore_errors=True)

# 2️⃣ Remove tracked files now ignored
run("git rm --cached $(git ls-files -i -c --exclude-standard)", ignore_errors=True)
run('git commit -m "Remove files tracked that are now in .gitignore"', ignore_errors=True)

# 3️⃣ Optimize repository
run("git clean -fdx", ignore_errors=True)
run("git reflog expire --expire=now --all", ignore_errors=True)
run("git gc --prune=now --aggressive", ignore_errors=True)

# 4️⃣ Secure sensitive files
if os.path.exists(".env"):
    run("git filter-repo --path .env --invert-paths", ignore_errors=True)

# 5️⃣ Add README.md
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
with open("README.md", "w") as f:
    f.write(readme_content)
run("git add README.md", ignore_errors=True)
run('git commit -m "Add README with project overview and setup instructions"', ignore_errors=True)

# 6️⃣ Git LFS setup
git_lfs_installed = subprocess.run("git lfs version", shell=True, stdout=subprocess.DEVNULL).returncode == 0
if not git_lfs_installed:
    if current_os in ["Linux", "Darwin"]:
        run("curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash", ignore_errors=True)
        run("sudo apt-get install git-lfs -y", ignore_errors=True)
    run("git lfs install", ignore_errors=True)
else:
    run("git lfs install", ignore_errors=True)

run("git lfs track '*.zip' '*.bin'", ignore_errors=True)
run("git add .gitattributes", ignore_errors=True)
run('git commit -m "Add Git LFS support for large files"', ignore_errors=True)

# 7️⃣ Push changes
run("git push origin main", ignore_errors=True)
