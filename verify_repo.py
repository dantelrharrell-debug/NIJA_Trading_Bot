#!/usr/bin/env python3
"""
NIJA_Trading_Bot Verification Script
Checks repo readiness before live trading
- Backups
- .gitignore & tracked files
- Git LFS
- README
- Commit tagging
- Push readiness
"""

import os, subprocess, sys

def run(cmd, capture_output=True):
    return subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)

errors = []

# 1️⃣ Check backup directory
if os.path.exists("backup") and os.listdir("backup"):
    print("✅ Backup directory exists and contains files")
else:
    errors.append("❌ Backup directory missing or empty")

# 2️⃣ Check .gitignore
if os.path.exists(".gitignore"):
    print("✅ .gitignore exists")
else:
    errors.append("❌ .gitignore missing")

# 3️⃣ Check README
if os.path.exists("README.md"):
    print("✅ README.md exists")
else:
    errors.append("❌ README.md missing")

# 4️⃣ Check Git LFS
lfs_installed = run("git lfs version").returncode == 0
if lfs_installed:
    print("✅ Git LFS installed")
else:
    errors.append("❌ Git LFS not installed")

# 5️⃣ Check for tracked ignored files
ignored_files = run("git ls-files -i -c --exclude-standard").stdout.strip()
if ignored_files:
    errors.append(f"❌ Some ignored files are still tracked:\n{ignored_files}")
else:
    print("✅ No ignored files are tracked")

# 6️⃣ Check for uncommitted changes
status = run("git status --porcelain").stdout.strip()
if status:
    errors.append(f"❌ There are uncommitted changes:\n{status}")
else:
    print("✅ No uncommitted changes")

# 7️⃣ Check commit tagging
tags = run("git tag").stdout.strip()
if tags:
    print(f"✅ Commit tags found: {tags.splitlines()[-1]}")
else:
    errors.append("❌ No commit tags found")

# 8️⃣ Check push readiness
remote = run("git remote -v").stdout.strip()
if remote:
    print("✅ Git remote configured")
else:
    errors.append("❌ No Git remote configured")

# Final report
if errors:
    print("\n⚠️ Repo verification FAILED:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("\n🎯 All checks passed! Repo is ready for live trading 🚀")
