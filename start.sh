#!/bin/bash

echo "=== START: NIJA Trading Bot ==="
echo "Python version: $(python --version)"
echo "Starting NIJA Bot on port 10000..."

python main.py \
  --coinbase-api-key "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267" \
  --coinbase-api-secret "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49" \
  --tv-webhook-secret "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49" \
  --port 10000
