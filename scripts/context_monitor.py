#!/usr/bin/env python3
"""
上下文监控器
实时监控上下文长度和使用率
"""

import time
import subprocess
import re
from datetime import datetime
from pathlib import Path

class ContextMonitor:
    """上下文监控器"""
    
    def __init__(self, config=None):
        """初始化监控器"""
        self.config = config or {}
        self.monitoring = False
        self.last_check = None
        self.usage_history = []
        
        # 默认配置
        self.check_interval = self.config.get("check_interval_seconds", 60)
        self.warning_threshold = self.config.get("warning_threshold", 0.85)  # 85%
        self.critical_threshold = self.config.get("critical_threshold", 0.90)  # 90%
        self.max_history = self.config.get("max_history", 100)
        
        # 从配置获取上下文限制
        self.context_limits = self.config.get("context_limits", {})
        self.max_chars = self.context_limits.get("max_chars", 98304)
        self.warning_chars = self.context_limits.get("warning_chars", int(98304 * 0.85))
        self.critical_chars = self.context_limits.get("critical_chars", int(98304 * 0.90))
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        print(f"🔍 上下文监控已启动，检查间隔: {self.check_interval}秒")
        
        try:
            while self.monitoring:
                self.check_context_usage()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n⏹️ 上下文监控已停止")
        except Exception as e:
            print(f"❌ 监控异常: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        print("⏹️ 上下文监控已停止")
    
    def check_context_usage(self):
        """检查上下文使用率"""
        try:
            # 方法1：检查OpenClaw日志中的超限错误
            overflow_detected = self.check_overflow_logs()
            
            if overflow_detected:
                usage_percentage = 100.0  # 检测到超限，假设100%
                context_length = self.max_chars * 1.05  # 假设超限5%
            else:
                # 方法2：通过检查脚本获取使用率
                usage_data = self.get_usage_from_checker()
                if usage_data:
                    usage_percentage = usage_data.get("usage_percentage", 50.0)
                    context_length = usage_data.get("context_length", self.max_chars * 0.5)
                else:
                    # 方法3：估计使用率
                    usage_percentage = self.estimate_usage()
                    context_length = self.max_chars * (usage_percentage / 100)
            
            # 记录使用率历史
            self.record_usage(usage_percentage, context_length)
            
            # 检查阈值
            status = self.check_thresholds(usage_percentage)
            
            self.last_check = {
                "timestamp": datetime.now().isoformat(),
                "usage_percentage": usage_percentage,
                "context_length": context_length,
                "status": status,
                "max_chars": self.max_chars
            }
            
            # 输出状态
            self.print_status(status, usage_percentage, context_length)
            
            return self.last_check
            
        except Exception as e:
            print(f"❌ 上下文检查失败: {e}")
            return None
    
    def check_overflow_logs(self, minutes=10):
        """检查最近的超限日志"""
        try:
            result = subprocess.run(
                ["journalctl", "--user", "-u", "openclaw-gateway", "--since", f"{minutes} minutes ago"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 检查是否有超限错误
            overflow_patterns = [
                "exceeds the maximum length",
                "Input length.*exceeds",
                "context overflow"
            ]
            
            for pattern in overflow_patterns:
                if pattern in result.stdout:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ 检查超限日志失败: {e}")
            return False
    
    def get_usage_from_checker(self):
        """从检查脚本获取使用率"""
        try:
            # 尝试调用现有的检查脚本
            checker_path = Path("/root/.openclaw/workspace/context-compressor-skill/scripts/conversation_compression_checker.py")
            if checker_path.exists():
                result = subprocess.run(
                    ["python3", str(checker_path)],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                # 解析输出中的使用率
                for line in result.stdout.split('\n'):
                    if "上下文使用率" in line:
                        match = re.search(r'上下文使用率\s*([\d.]+)%', line)
                        if match:
                            usage = float(match.group(1))
                            # 估计上下文长度
                            context_length = self.max_chars * (usage / 100)
                            return {
                                "usage_percentage": usage,
                                "context_length": context_length
                            }
            
            return None
            
        except subprocess.TimeoutExpired:
            print("⚠️ 检查脚本执行超时")
            return None
        except Exception as e:
            print(f"❌ 获取检查脚本数据失败: {e}")
            return None
    
    def estimate_usage(self):
        """估计使用率"""
        # 基于历史数据估计
        if self.usage_history:
            # 使用最近的平均值
            recent_history = self.usage_history[-10:] if len(self.usage_history) >= 10 else self.usage_history
            avg_usage = sum([h["usage_percentage"] for h in recent_history]) / len(recent_history)
            return avg_usage
        else:
            # 默认估计：如果没有超限记录，假设正常
            return 50.0
    
    def record_usage(self, usage_percentage, context_length):
        """记录使用率"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "usage_percentage": usage_percentage,
            "context_length": context_length
        }
        
        self.usage_history.append(record)
        
        # 限制历史记录数量
        if len(self.usage_history) > self.max_history:
            self.usage_history = self.usage_history[-self.max_history:]
    
    def check_thresholds(self, usage_percentage):
        """检查阈值"""
        if usage_percentage >= 100:
            return "CRITICAL_OVERFLOW"  # 超限
        elif usage_percentage >= (self.critical_threshold * 100):
            return "CRITICAL"  # 临界
        elif usage_percentage >= (self.warning_threshold * 100):
            return "WARNING"  # 警告
        else:
            return "NORMAL"  # 正常
    
    def print_status(self, status, usage_percentage, context_length):
        """输出状态"""
        status_icons = {
            "NORMAL": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
            "CRITICAL_OVERFLOW": "💥"
        }
        
        status_texts = {
            "NORMAL": "正常",
            "WARNING": "警告",
            "CRITICAL": "临界",
            "CRITICAL_OVERFLOW": "超限"
        }
        
        icon = status_icons.get(status, "❓")
        text = status_texts.get(status, "未知")
        
        print(f"{icon} 上下文状态: {text} | 使用率: {usage_percentage:.1f}% | 长度: {int(context_length):,}/{self.max_chars:,} 字符")
        
        if status == "CRITICAL_OVERFLOW":
            print(f"   💥 上下文已超限！需要立即压缩！")
        elif status == "CRITICAL":
            print(f"   🚨 上下文接近超限 ({usage_percentage:.1f}%)，建议压缩")
        elif status == "WARNING":
            print(f"   ⚠️ 上下文使用率较高 ({usage_percentage:.1f}%)，请关注")
    
    def get_usage_trend(self):
        """获取使用率趋势"""
        if len(self.usage_history) < 2:
            return "stable"  # 稳定
        
        recent = self.usage_history[-5:] if len(self.usage_history) >= 5 else self.usage_history
        first = recent[0]["usage_percentage"]
        last = recent[-1]["usage_percentage"]
        
        if last - first > 5:
            return "increasing"  # 上升
        elif last - first < -5:
            return "decreasing"  # 下降
        else:
            return "stable"  # 稳定
    
    def get_summary(self):
        """获取监控摘要"""
        if not self.usage_history:
            return {"status": "NO_DATA", "message": "暂无监控数据"}
        
        current = self.usage_history[-1]
        trend = self.get_usage_trend()
        
        summary = {
            "current_usage": current["usage_percentage"],
            "current_length": current["context_length"],
            "max_length": self.max_chars,
            "status": self.check_thresholds(current["usage_percentage"]),
            "trend": trend,
            "history_count": len(self.usage_history),
            "last_check": self.last_check.get("timestamp") if self.last_check else None
        }
        
        return summary

if __name__ == "__main__":
    # 测试监控器
    config = {
        "check_interval_seconds": 10,
        "warning_threshold": 0.85,
        "critical_threshold": 0.90,
        "context_limits": {
            "max_chars": 98304,
            "warning_chars": 83558,
            "critical_chars": 88474
        }
    }
    
    monitor = ContextMonitor(config)
    
    print("🧪 测试上下文监控器")
    print("=" * 50)
    
    # 测试几次检查
    for i in range(3):
        result = monitor.check_context_usage()
        if result:
            print(f"检查 {i+1}: {result['status']} - {result['usage_percentage']:.1f}%")
        time.sleep(2)
    
    # 获取摘要
    summary = monitor.get_summary()
    print(f"\n📊 监控摘要: {summary}")