#!/usr/bin/env python3
"""
Ralph Supervisor - Automated task execution with retry logic
Gre acts as supervisor, sub-agents do the work
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


class RalphSupervisor:
    """Supervises sub-agent task execution with automatic retry."""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / ".ralph" / "supervisor_state.json"
        self.log_file = self.project_dir / ".ralph" / "supervisor.log"
        self.state = self._load_state()
        
    def _load_state(self) -> dict:
        """Load supervisor state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "current_phase": "us001_completion",
            "current_task": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "retry_count": 0,
            "last_action": None,
        }
    
    def _save_state(self):
        """Save supervisor state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
    
    def _check_quota_status(self) -> dict:
        """Check if we can spawn sub-agents."""
        # Try a test spawn to check quota
        result = subprocess.run(
            ["python3", "-c", "print('quota_ok')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {"ok": result.returncode == 0}
    
    def _spawn_task(self, task_label: str, task_prompt: str, timeout: int = 300) -> dict:
        """Spawn a sub-agent task."""
        self._log(f"Spawning task: {task_label}")
        
        # Create a temporary task file
        task_file = self.project_dir / ".ralph" / f"task_{task_label}.json"
        task_data = {
            "label": task_label,
            "prompt": task_prompt,
            "timeout": timeout,
            "status": "pending"
        }
        with open(task_file, "w") as f:
            json.dump(task_data, f)
        
        return {
            "status": "spawned",
            "task_file": str(task_file),
            "label": task_label
        }
    
    def _check_task_result(self, task_label: str) -> dict:
        """Check if a spawned task completed."""
        # In real implementation, this would check session history
        # For now, we'll check if expected outputs exist
        
        task_checks = {
            "us001_alembic": lambda: (self.project_dir / "alembic" / "env.py").exists(),
            "us001_migrate": lambda: len(list((self.project_dir / "alembic" / "versions").glob("*.py"))) > 0,
            "us002_x_fetcher": lambda: (self.project_dir / "src" / "fetcher" / "x_fetcher.py").exists(),
        }
        
        check_fn = task_checks.get(task_label)
        if check_fn and check_fn():
            return {"status": "completed", "success": True}
        
        return {"status": "unknown"}
    
    def run_us001_completion(self):
        """Complete US-001: Alembic setup and verification."""
        self._log("=== Starting US-001 Completion ===")
        
        tasks = [
            {
                "label": "us001_verify_structure",
                "prompt": "Verify US-001 structure is complete. Check:\n"
                         "1. All src/ directories exist\n"
                         "2. All model files exist\n" 
                         "3. pyproject.toml is valid\n"
                         "4. Report any missing files\n\n"
                         "Work in: /home/admin/clawd/projects/info-flow-platform",
                "verify": lambda: (self.project_dir / "src" / "models" / "content.py").exists()
            },
            {
                "label": "us001_alembic_init", 
                "prompt": "Initialize Alembic for the project:\n"
                         "1. Check if alembic/ directory exists\n"
                         "2. If not, create minimal alembic structure manually:\n"
                         "   - Create alembic/ directory\n"
                         "   - Create alembic.ini (copy from template if exists)\n"
                         "   - Create alembic/env.py (minimal config)\n"
                         "3. Point alembic to src.models.Base\n\n"
                         "Work in: /home/admin/clawd/projects/info-flow-platform",
                "verify": lambda: (self.project_dir / "alembic" / "env.py").exists()
            },
            {
                "label": "us001_verify_migration",
                "prompt": "Verify migration file exists and is valid:\n"
                         "1. Check alembic/versions/001_initial_migration.py exists\n"
                         "2. Verify it has upgrade() and downgrade() functions\n"
                         "3. Report the tables it creates\n\n"
                         "Work in: /home/admin/clawd/projects/info-flow-platform",
                "verify": lambda: (self.project_dir / "alembic" / "versions" / "001_initial_migration.py").exists()
            }
        ]
        
        for task in tasks:
            self._log(f"\n--- Task: {task['label']} ---")
            
            # Check if already done
            if task["verify"]():
                self._log(f"✅ Task {task['label']} already completed")
                self.state["completed_tasks"].append(task["label"])
                self._save_state()
                continue
            
            # Try to complete with sub-agent
            max_retries = 3
            for attempt in range(max_retries):
                self._log(f"Attempt {attempt + 1}/{max_retries}")
                
                # Spawn sub-agent
                result = self._spawn_task(task["label"], task["prompt"])
                
                if result["status"] == "spawned":
                    self._log(f"Sub-agent spawned, waiting...")
                    # Wait for completion (in real impl, poll session)
                    time.sleep(30)
                    
                    # Check result
                    check = self._check_task_result(task["label"])
                    if check["status"] == "completed":
                        self._log(f"✅ Task {task['label']} completed")
                        self.state["completed_tasks"].append(task["label"])
                        self._save_state()
                        break
                    else:
                        self._log(f"⏳ Task not yet complete, will retry")
                        time.sleep(10)
                else:
                    self._log(f"❌ Failed to spawn: {result}")
                    time.sleep(60)  # Wait before retry
            
            else:
                self._log(f"⚠️ Task {task['label']} failed after {max_retries} attempts")
                self.state["failed_tasks"].append(task["label"])
                self._save_state()
        
        self._log("\n=== US-001 Completion Phase Done ===")
        self._log(f"Completed: {len(self.state['completed_tasks'])} tasks")
        self._log(f"Failed: {len(self.state['failed_tasks'])} tasks")
    
    def run(self):
        """Main supervisor loop."""
        self._log("🚀 Ralph Supervisor Starting")
        self._log(f"Project: {self.project_dir}")
        self._log(f"Current phase: {self.state['current_phase']}")
        
        if self.state["current_phase"] == "us001_completion":
            self.run_us001_completion()
        
        self._log("\n🏁 Supervisor run complete")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ralph Supervisor")
    parser.add_argument("--project", default=".", help="Project directory")
    parser.add_argument("--phase", default="us001_completion", help="Phase to run")
    
    args = parser.parse_args()
    
    supervisor = RalphSupervisor(args.project)
    if args.phase:
        supervisor.state["current_phase"] = args.phase
    
    supervisor.run()


if __name__ == "__main__":
    main()
