#!/usr/bin/env bash
set -e
echo "🔧 Upgrading pip & installing coinbase-advanced-py..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir coinbase-advanced-py==1.8.2
echo "📦 Installing requirements..."
pip install --no-cache-dir -r requirements.txt
