#!/usr/bin/env bash
# Ralph PLANNING Loop for InfoFlow Platform
set -euo pipefail

PROMISE='PLANNING complete'
MAX_ITERS=5
PLAN_SENTINEL='STATUS: COMPLETE'

# 确保在 git 仓库中
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Run this inside a git repo."
  exit 1
fi

# 确保文件存在
touch PROMPT.md AGENTS.md IMPLEMENTATION_PLAN.md
mkdir -p specs

LOG_FILE=".ralph/planning.log"
mkdir -p .ralph

echo "🚀 Starting Ralph PLANNING loop for InfoFlow Platform"
echo "📁 Project: $(pwd)"
echo "📝 Max iterations: $MAX_ITERS"
echo ""

# 检测可用的 AI CLI
if command -v claude &> /dev/null; then
  CLI_CMD="claude"
  echo "✅ Using: Claude Code"
elif command -v codex &> /dev/null; then
  CLI_CMD="codex exec"
  echo "✅ Using: Codex"
elif command -v opencode &> /dev/null; then
  CLI_CMD="opencode run"
  echo "✅ Using: OpenCode"
else
  echo "❌ No AI CLI found. Please install claude, codex, or opencode."
  exit 1
fi

echo ""

for i in $(seq 1 "$MAX_ITERS"); do
  echo -e "\n═══════════════════════════════════════════════════" | tee -a "$LOG_FILE"
  echo "🔄 Ralph PLANNING iteration $i/$MAX_ITERS" | tee -a "$LOG_FILE"
  echo "═══════════════════════════════════════════════════" | tee -a "$LOG_FILE"

  # 运行 AI 迭代
  $CLI_CMD "$(cat PROMPT.md)" | tee -a "$LOG_FILE"

  # 检查完成状态
  if grep -Fq "$PLAN_SENTINEL" IMPLEMENTATION_PLAN.md; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ PLANNING complete detected! Stopping loop." | tee -a "$LOG_FILE"
    echo "📋 Review IMPLEMENTATION_PLAN.md and then run ralph-build.sh"
    exit 0
  fi

  if grep -Fq "$PROMISE" "$LOG_FILE"; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Promise phrase detected! Stopping loop." | tee -a "$LOG_FILE"
    exit 0
  fi

done

echo "" | tee -a "$LOG_FILE"
echo "⚠️ Max iterations reached without completion." | tee -a "$LOG_FILE"
echo "📝 Review IMPLEMENTATION_PLAN.md and adjust PROMPT.md if needed."
exit 1
