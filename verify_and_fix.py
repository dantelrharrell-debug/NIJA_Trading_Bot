#!/usr/bin/env python3
"""
NIJA_Trading_Bot Self-Healing Verification & Cleanup
- Verifies repo readiness
- Automatically runs cleanup if any check fails
- Ensures backups, Git LFS, .gitignore, README, tags, and push readiness
"""

import os, subprocess, sys

def run(cmd, capture_output=True, ignore_errors=False):
    try:
        return subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout='', stderr='')

def check_repo():
    """Run verification checks, return True if all pass"""
    errors = []

    # Backup directory
    if not (os.path.exists("backup") and os.listdir("backup")):
        errors.append("Backup directory missing or empty")

    # .gitignore
    if not os.path.exists(".gitignore"):
        errors.append(".gitignore missing")

    # README
    if not os.path.exists("README.md"):
        errors.append("README.md missing")

    # Git LFS
    lfs_installed = run("git lfs version").returncode == 0
    if not lfs_installed:
        errors.append("Git LFS not installed")

    # Tracked ignored files
    ignored_files = run("git ls-files -i -c --exclude-standard").stdout.strip()
    if ignored_files:
        errors.append(f"Ignored files are still tracked:\n{ignored_files}")

    # Uncommitted changes
    status = run("git status --porcelain").stdout.strip()
    if status:
        errors.append(f"Uncommitted changes:\n{status}")

    # Commit tags
    tags = run("git tag").stdout.strip()
    if not tags:
        errors.append("No commit tags found")

    # Git remote
    remote = run("git remote -v").stdout.strip()
    if not remote:
        errors.append("Git remote not configured")

    if errors:
        print("\n⚠️ Repo verification FAILED:")
        for e in errors:
            print(" -", e)
        return False
    return True

def run_cleanup():
    """Run the ultimate cleanup script automatically"""
    if os.path.exists("ultimate_clean_repo.py"):
        print("\n🔧 Running self-healing cleanup...")
        subprocess.run("python3 ultimate_clean_repo.py", shell=True)
        print("\n✅ Cleanup complete")
    else:
        print("❌ ultimate_clean_repo.py not found! Cannot auto-fix.")

# -------------------------------
# MAIN
# -------------------------------
print("🎯 Verifying NIJA_Trading_Bot repository readiness...")
if check_repo():
    print("\n🎉 All checks passed! Repo is live and ready to trade 🚀")
else:
    run_cleanup()
    # Verify again after cleanup
    print("\n🔄 Re-verifying repo after cleanup...")
    if check_repo():
        print("\n🎉 All checks passed! Repo is now live and ready to trade 🚀")
    else:
        print("\n❌ Repo still has issues after cleanup. Check logs manually.")
