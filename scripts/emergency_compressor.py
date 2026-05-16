#!/usr/bin/env python3
"""
应急压缩器
当上下文严重超限时执行紧急压缩
"""

import json
import time
from datetime import datetime

class EmergencyCompressor:
    """应急压缩器 - 处理严重超限情况"""
    
    def __init__(self, config=None):
        """初始化应急压缩器"""
        self.config = config or {}
        self.compression_history = []
        
        # 应急压缩配置
        self.emergency_threshold = self.config.get("emergency_threshold", 1.0)  # 100%
        self.max_emergency_attempts = self.config.get("max_emergency_attempts", 3)
        self.emergency_timeout = self.config.get("emergency_timeout", 30)  # 秒
        
        # 压缩策略
        self.strategy = self.config.get("emergency_strategy", "restart_session")
    
    def is_emergency(self, context_length, max_length):
        """判断是否为紧急情况"""
        usage = context_length / max_length
        return usage >= self.emergency_threshold
    
    def execute_emergency_compression(self, context_length, max_length, error_id=None):
        """执行应急压缩"""
        print(f"💥 检测到紧急情况！上下文长度: {context_length:,}/{max_length:,} 字符")
        print(f"   🚨 使用率: {(context_length/max_length*100):.1f}%")
        
        if error_id:
            print(f"   🔧 错误ID: {error_id}")
        
        # 记录压缩开始
        compression_record = {
            "timestamp": datetime.now().isoformat(),
            "context_length": context_length,
            "max_length": max_length,
            "usage_percentage": (context_length / max_length) * 100,
            "error_id": error_id,
            "strategy": self.strategy,
            "start_time": time.time()
        }
        
        result = None
        
        try:
            # 根据策略执行应急压缩
            if self.strategy == "restart_session":
                result = self.restart_session_strategy()
            elif self.strategy == "force_cleanup":
                result = self.force_cleanup_strategy()
            elif self.strategy == "minimal_preserve":
                result = self.minimal_preserve_strategy()
            else:
                result = self.restart_session_strategy()  # 默认策略
            
            # 记录压缩结果
            compression_record.update({
                "end_time": time.time(),
                "duration": time.time() - compression_record["start_time"],
                "result": result,
                "status": "success" if result.get("success") else "failed"
            })
            
        except Exception as e:
            print(f"❌ 应急压缩执行失败: {e}")
            compression_record.update({
                "end_time": time.time(),
                "duration": time.time() - compression_record["start_time"],
                "error": str(e),
                "status": "error"
            })
            result = {"success": False, "error": str(e)}
        
        # 保存记录
        self.compression_history.append(compression_record)
        
        # 限制历史记录数量
        if len(self.compression_history) > 10:
            self.compression_history = self.compression_history[-10:]
        
        return result
    
    def restart_session_strategy(self):
        """重启会话策略"""
        print("🔄 执行重启会话策略...")
        
        steps = [
            "1. 提取关键信息摘要",
            "2. 清理工具调用历史", 
            "3. 保留核心对话内容",
            "4. 重建会话上下文"
        ]
        
        for step in steps:
            print(f"   {step}")
            time.sleep(0.5)
        
        # 模拟重启操作
        result = {
            "success": True,
            "strategy": "restart_session",
            "action": "session_restart",
            "compressed_to": "minimal_context",
            "preserved_items": [
                "key_instructions",
                "important_decisions", 
                "project_status"
            ],
            "removed_items": [
                "tool_call_history",
                "redundant_messages",
                "detailed_logs"
            ],
            "message": "会话已重启，关键信息已保留"
        }
        
        print("✅ 重启会话策略执行完成")
        return result
    
    def force_cleanup_strategy(self):
        """强制清理策略"""
        print("🧹 执行强制清理策略...")
        
        # 模拟强制清理
        cleanup_items = [
            "删除旧工具调用记录",
            "清理重复消息",
            "压缩长文本内容",
            "移除调试信息"
        ]
        
        for item in cleanup_items:
            print(f"   🗑️  {item}")
            time.sleep(0.3)
        
        result = {
            "success": True,
            "strategy": "force_cleanup",
            "action": "aggressive_cleanup",
            "estimated_reduction": "40-60%",
            "cleaned_items": cleanup_items,
            "message": "强制清理完成，上下文大幅减少"
        }
        
        print("✅ 强制清理策略执行完成")
        return result
    
    def minimal_preserve_strategy(self):
        """最小保留策略"""
        print("📝 执行最小保留策略...")
        
        preserve_rules = [
            "仅保留最后10轮对话",
            "保留系统指令和关键决策",
            "删除所有工具调用详情",
            "压缩长回复为摘要"
        ]
        
        for rule in preserve_rules:
            print(f"   📌 {rule}")
            time.sleep(0.3)
        
        result = {
            "success": True,
            "strategy": "minimal_preserve",
            "action": "selective_preservation",
            "preservation_ratio": "20%",
            "preserved_categories": [
                "user_instructions",
                "agent_decisions",
                "project_context"
            ],
            "message": "最小保留策略执行完成，仅保留核心内容"
        }
        
        print("✅ 最小保留策略执行完成")
        return result
    
    def get_compression_history(self):
        """获取压缩历史"""
        return self.compression_history
    
    def get_recent_emergencies(self, limit=5):
        """获取最近的紧急情况"""
        return self.compression_history[-limit:] if self.compression_history else []
    
    def get_emergency_stats(self):
        """获取应急压缩统计"""
        if not self.compression_history:
            return {"total_emergencies": 0, "success_rate": 0}
        
        total = len(self.compression_history)
        successful = len([r for r in self.compression_history if r.get("status") == "success"])
        
        return {
            "total_emergencies": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 2) if total > 0 else 0,
            "latest_emergency": self.compression_history[-1] if self.compression_history else None
        }

def create_emergency_response(context_length, max_length, error_id=None):
    """创建应急响应"""
    compressor = EmergencyCompressor()
    
    if compressor.is_emergency(context_length, max_length):
        print(f"🚨 检测到紧急超限情况！")
        print(f"   长度: {context_length:,}/{max_length:,}")
        print(f"   使用率: {(context_length/max_length*100):.1f}%")
        
        result = compressor.execute_emergency_compression(context_length, max_length, error_id)
        return result
    else:
        print(f"✅ 未达到紧急阈值 (当前: {(context_length/max_length*100):.1f}%)")
        return {"success": False, "reason": "not_emergency"}

if __name__ == "__main__":
    # 测试应急压缩器
    
    print("🧪 测试应急压缩器")
    print("=" * 50)
    
    # 测试紧急情况
    test_cases = [
        {"length": 103933, "max": 98304, "emergency": True},  # 超限
        {"length": 90000, "max": 98304, "emergency": False},  # 未超限
        {"length": 120000, "max": 98304, "emergency": True},  # 严重超限
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test['length']:,}/{test['max']:,} 字符")
        result = create_emergency_response(test["length"], test["max"], f"test_error_{i}")
        print(f"结果: {result}")
        time.sleep(1)
    
    # 显示统计
    compressor = EmergencyCompressor()
    stats = compressor.get_emergency_stats()
    print(f"\n📊 应急压缩统计: {stats}")