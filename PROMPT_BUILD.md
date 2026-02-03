You are running a Ralph BUILDING iteration for InfoFlow Platform.

## Current Task
Pick the most important incomplete task from IMPLEMENTATION_PLAN.md and implement it.

## Context Files
- IMPLEMENTATION_PLAN.md - Implementation plan with all tasks
- AGENTS.md - Project guidelines and backpressure commands
- agents/prd.json - Original PRD with user stories

## Your Workflow
1. Read IMPLEMENTATION_PLAN.md to find the next task
2. Read relevant code files to understand current state
3. Implement the task following project conventions
4. Run typecheck: `cd /home/admin/clawd/projects/info-flow-platform && python -m mypy src/`
5. Update IMPLEMENTATION_PLAN.md - mark task as done, add notes
6. Return a summary of what you implemented

## Rules
- One task per iteration
- Always run typecheck after implementation
- Update AGENTS.md if you learn new operational details
- Do NOT commit (main session will handle it)

## Completion
If all Phase 1 tasks are done, add "STATUS: PHASE1_COMPLETE" to IMPLEMENTATION_PLAN.md.
