#!/usr/bin/env python3
"""
API Key 智能调度管理器
- 多 key 轮转
- 自动故障切换
- 429 冷却机制
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class KeyManager:
    def __init__(self, keys_file: str = ".keys/keys.json"):
        self.keys_file = Path(keys_file)
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """加载 key 配置"""
        if self.keys_file.exists():
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        return {"keys": [], "current_index": 0}
    
    def _save(self):
        """保存 key 配置"""
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_active_key(self) -> Optional[str]:
        """获取当前可用的 key"""
        keys = self.data["keys"]
        cooldown_minutes = self.data.get("cooldown_minutes", 5)
        
        # 按优先级尝试每个 key
        for i, key in enumerate(keys):
            # 检查是否在冷却期
            if key.get("cooldown_until"):
                cooldown = datetime.fromisoformat(key["cooldown_until"])
                if datetime.now() < cooldown:
                    continue  # 还在冷却中
                else:
                    # 冷却结束，重置状态
                    key["status"] = "active"
                    key["cooldown_until"] = None
            
            # 检查错误次数
            if key.get("error_count", 0) >= 3:
                key["status"] = "cooling"
                key["cooldown_until"] = (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
                self._save()
                continue
            
            # 更新使用记录
            key["last_used"] = datetime.now().isoformat()
            self.data["current_index"] = i
            self._save()
            
            return key["value"]
        
        # 所有 key 都不可用，尝试重置
        print("⚠️ All keys in cooldown, trying reset...")
        for key in keys:
            key["status"] = "active"
            key["cooldown_until"] = None
            key["error_count"] = 0
        self._save()
        
        # 递归重试一次
        if keys:
            return keys[0]["value"]
        
        return None
    
    def report_error(self, key_value: str, error_type: str = "429"):
        """报告 key 错误"""
        for key in self.data["keys"]:
            if key["value"] == key_value:
                key["error_count"] = key.get("error_count", 0) + 1
                
                if error_type == "429":
                    # 429 错误进入冷却
                    key["status"] = "cooling"
                    cooldown_minutes = self.data.get("cooldown_minutes", 5)
                    key["cooldown_until"] = (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
                    print(f"🔑 Key {key['id']} hit 429, cooling for {cooldown_minutes}min")
                
                self._save()
                break
    
    def report_success(self, key_value: str):
        """报告 key 成功使用，重置错误计数"""
        for key in self.data["keys"]:
            if key["value"] == key_value:
                key["error_count"] = 0
                key["status"] = "active"
                self._save()
                break
    
    def get_status(self) -> Dict[str, Any]:
        """获取所有 key 的状态"""
        return {
            "keys": [
                {
                    "id": k["id"],
                    "status": k.get("status", "active"),
                    "error_count": k.get("error_count", 0),
                    "cooldown_until": k.get("cooldown_until"),
                    "last_used": k.get("last_used")
                }
                for k in self.data["keys"]
            ],
            "current_index": self.data.get("current_index", 0)
        }


def main():
    """CLI 工具"""
    import sys
    
    manager = KeyManager()
    
    if len(sys.argv) < 2:
        print("Usage: key_manager.py <get|status|reset>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "get":
        key = manager.get_active_key()
        if key:
            print(key)
        else:
            print("No active key available", file=sys.stderr)
            sys.exit(1)
    
    elif cmd == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))
    
    elif cmd == "reset":
        for key in manager.data["keys"]:
            key["status"] = "active"
            key["cooldown_until"] = None
            key["error_count"] = 0
        manager._save()
        print("✅ All keys reset to active")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
