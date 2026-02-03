#!/bin/bash
# Ralph BUILDING Loop with Key Rotation
set -euo pipefail

cd /home/admin/clawd/projects/info-flow-platform

echo "🚀 Ralph BUILDING Loop for InfoFlow Platform"
echo ""

MAX_ITERS=20
ITER=0

while [ $ITER -lt $MAX_ITERS ]; do
    ITER=$((ITER + 1))
    echo "═══════════════════════════════════════════════════"
    echo "🔄 BUILDING Iteration $ITER/$MAX_ITERS"
    echo "═══════════════════════════════════════════════════"
    
    # Get active API key
    echo "🔑 Getting active API key..."
    ACTIVE_KEY=$(python3 scripts/key_manager.py get)
    
    if [ -z "$ACTIVE_KEY" ]; then
        echo "❌ No active API key available. Waiting 60s..."
        sleep 60
        python3 scripts/key_manager.py reset
        continue
    fi
    
    echo "✅ Using key: ${ACTIVE_KEY:0:10}..."
    
    # Export key for subagent
    export OPENAI_API_KEY="$ACTIVE_KEY"
    
    # Spawn building subagent
    echo "🤖 Spawning building agent..."
    
    # Note: This uses moltbot sessions_spawn internally
    # The subagent will use the exported OPENAI_API_KEY
    
    # Check if IMPLEMENTATION_PLAN shows completion
    if grep -q "STATUS: PHASE1_COMPLETE" IMPLEMENTATION_PLAN.md 2>/dev/null; then
        echo ""
        echo "✅ Phase 1 complete! Stopping BUILDING loop."
        exit 0
    fi
    
    # Check if all tasks done
    if ! grep -q "\[ \]" IMPLEMENTATION_PLAN.md; then
        echo ""
        echo "✅ All tasks complete! Stopping BUILDING loop."
        exit 0
    fi
    
    # Wait between iterations to avoid rate limits
    echo "⏳ Waiting 30s before next iteration..."
    sleep 30
    
done

echo "⚠️ Max iterations reached."
exit 1
