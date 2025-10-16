#!/bin/bash
# 🥷 Nija Bot: Clear Cache & Redeploy
# ✅ Safe version ready to use
# Replace API_KEY if you ever change it
API_KEY="f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
SERVICE_ID="rnd_Xiq8UsGVHYyhZfPT3o2xHVNvygQb"

echo "🧹 Clearing Nija Bot cache and redeploying..."
curl -X POST "https://api.render.com/deploy/$SERVICE_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": true}'

echo "🚀 Deploy triggered! Give Render a few minutes to rebuild Nija Bot..."
