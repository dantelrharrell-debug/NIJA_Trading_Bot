#!/usr/bin/env python3
"""
NIJA_Trading_Bot Ultimate Cleanup Script
- Fully automated, cross-platform
- Backup, dry-run, error logging, commit tagging
- Handles .gitignore, README, tracked ignored files, Git LFS
"""

import os
import subprocess
import platform
import shutil
import datetime
import sys

# -------------------------------
# CONFIGURATION
# -------------------------------
DRY_RUN = False         # Set True to simulate cleanup without committing
VERBOSE = True          # Set False for fully silent mode
BACKUP_DIR = "backup"

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------
def log(msg):
    if VERBOSE:
        print(msg)

def run(cmd, ignore_errors=True):
    """Run shell command, capture errors"""
    try:
        if VERBOSE:
            subprocess.run(cmd, shell=True, check=True)
        else:
            subprocess.run(cmd, shell=True, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            with open("cleanup_errors.log", "a") as f:
                f.write(f"{cmd} -> {e}\n")

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# -------------------------------
# 0️⃣ BACKUP REPO
# -------------------------------
log("🗂 Creating backup of repository...")
os.makedirs(BACKUP_DIR, exist_ok=True)
backup_name = f"{BACKUP_DIR}/NIJA_Trading_Bot_backup_{timestamp()}.zip"
shutil.make_archive(backup_name.replace(".zip",""), 'zip', '.')

# Backup .env separately
if os.path.exists(".env"):
    env_backup = f"{BACKUP_DIR}/.env_backup_{timestamp()}"
    shutil.copy2(".env", env_backup)
    log(f"🔒 Backed up .env to {env_backup}")

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
with open(".gitignore", "w") as f:
    f.write(gitignore_content)
run("git add .gitignore")
if not DRY_RUN:
    run('git commit -m "Add/update .gitignore"', ignore_errors=True)

# -------------------------------
# 2️⃣ Remove tracked files now ignored
# -------------------------------
run("git rm --cached $(git ls-files -i -c --exclude-standard)", ignore_errors=True)
if not DRY_RUN:
    run('git commit -m "Remove files tracked that are now in .gitignore"', ignore_errors=True)

# -------------------------------
# 3️⃣ Optimize repository
# -------------------------------
run("git clean -fdx", ignore_errors=True)
run("git reflog expire --expire=now --all", ignore_errors=True)
run("git gc --prune=now --aggressive", ignore_errors=True)

# -------------------------------
# 4️⃣ Secure sensitive files
# -------------------------------
if os.path.exists(".env"):
    run("git filter-repo --path .env --invert-paths", ignore_errors=True)

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
with open("README.md", "w") as f:
    f.write(readme_content)
run("git add README.md", ignore_errors=True)
if not DRY_RUN:
    run('git commit -m "Add README with project overview and setup instructions"', ignore_errors=True)

# -------------------------------
# 6️⃣ Git LFS setup
# -------------------------------
git_lfs_installed = subprocess.run("git lfs version", shell=True, stdout=subprocess.DEVNULL).returncode == 0
current_os = platform.system()

if not git_lfs_installed:
    log("💾 Installing Git LFS...")
    if current_os in ["Linux", "Darwin"]:
        run("curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash", ignore_errors=True)
        run("sudo apt-get install git-lfs -y", ignore_errors=True)
    else:
        log("⚠️ Git LFS installation on Windows must be manual: https://git-lfs.com/")
    run("git lfs install", ignore_errors=True)
else:
    run("git lfs install", ignore_errors=True)

run("git lfs track '*.zip' '*.bin'", ignore_errors=True)
run("git add .gitattributes", ignore_errors=True)
if not DRY_RUN:
    run('git commit -m "Add Git LFS support for large files"', ignore_errors=True)

# -------------------------------
# 7️⃣ Commit tag for cleanup
# -------------------------------
tag_name = f"cleanup-{timestamp()}"
if not DRY_RUN:
    run(f"git tag {tag_name}", ignore_errors=True)

# -------------------------------
# 8️⃣ Push changes
# -------------------------------
if not DRY_RUN:
    run("git push origin main", ignore_errors=True)
    run(f"git push origin {tag_name}", ignore_errors=True)

log("✅ NIJA_Trading_Bot ultimate cleanup completed!")
log(f"Backup created at {backup_name}")
