#!/usr/bin/env python3
"""
智能压缩主程序
协调所有压缩组件，提供统一接口
"""

import sys
import time
import json
import yaml
from pathlib import Path

# 导入其他组件
sys.path.append(str(Path(__file__).parent))

try:
    from smart_compressor import SmartCompressor
    from context_monitor import ContextMonitor
    from emergency_compressor import EmergencyCompressor
    from compression_logger import CompressionLogger, get_logger
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 组件导入失败: {e}")
    COMPONENTS_AVAILABLE = False

class SmartCompressionSystem:
    """智能压缩系统 - 主协调器"""
    
    def __init__(self, config_path=None):
        """初始化智能压缩系统"""
        self.config_path = config_path or "/root/.openclaw/workspace/context-compressor-skill/config/compression_config.json"
        self.config = self.load_config()
        
        # 初始化组件
        self.components = {}
        self.initialize_components()
        
        # 系统状态
        self.system_status = {
            "initialized": False,
            "components_ready": False,
            "last_check": None,
            "last_compression": None,
            "total_compressions": 0,
            "total_overflows": 0
        }
        
        # 从配置获取参数
        self.setup_from_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
                else:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            else:
                print(f"⚠️ 配置文件不存在: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "compression_strategy": {
                "trigger_timing": "after_conversation",
                "thresholds": {
                    "warning": 0.85,
                    "execution": 0.90
                },
                "context_limits": {
                    "max_chars": 98304,
                    "warning_chars": 83558,
                    "compress_chars": 88474
                }
            },
            "emergency_config": {
                "emergency_threshold": 1.0,
                "max_emergency_attempts": 3,
                "emergency_strategy": "restart_session"
            },
            "monitoring": {
                "check_interval_seconds": 60,
                "enable_real_time_monitoring": True
            }
        }
    
    def setup_from_config(self):
        """从配置设置参数"""
        # 压缩策略
        strategy = self.config.get("compression_strategy", {})
        thresholds = strategy.get("thresholds", {})
        context_limits = strategy.get("context_limits", {})
        
        self.warning_threshold = thresholds.get("warning", 0.85)
        self.execution_threshold = thresholds.get("execution", 0.90)
        
        self.max_chars = context_limits.get("max_chars", 98304)
        self.warning_chars = context_limits.get("warning_chars", int(98304 * 0.85))
        self.compress_chars = context_limits.get("compress_chars", int(98304 * 0.90))
        
        # 应急配置
        emergency_config = self.config.get("emergency_config", {})
        self.emergency_threshold = emergency_config.get("emergency_threshold", 1.0)
        
        # 监控配置
        monitoring = self.config.get("monitoring", {})
        self.check_interval = monitoring.get("check_interval_seconds", 60)
    
    def initialize_components(self):
        """初始化所有组件"""
        if not COMPONENTS_AVAILABLE:
            print("⚠️ 组件不可用，使用简化模式")
            self.components_available = False
            return
        
        try:
            # 初始化日志记录器
            self.components["logger"] = get_logger()
            
            # 初始化上下文监控器
            monitor_config = {
                "check_interval_seconds": self.check_interval,
                "warning_threshold": self.warning_threshold,
                "critical_threshold": self.execution_threshold,
                "context_limits": {
                    "max_chars": self.max_chars,
                    "warning_chars": self.warning_chars,
                    "critical_chars": self.compress_chars
                }
            }
            self.components["monitor"] = ContextMonitor(monitor_config)
            
            # 初始化智能压缩器
            self.components["compressor"] = SmartCompressor()
            
            # 初始化应急压缩器
            emergency_config = {
                "emergency_threshold": self.emergency_threshold,
                "emergency_strategy": "restart_session"
            }
            self.components["emergency"] = EmergencyCompressor(emergency_config)
            
            self.components_available = True
            print("✅ 所有组件初始化完成")
            
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")
            self.components_available = False
    
    def check_context_status(self):
        """检查上下文状态"""
        print("🔍 检查上下文状态...")
        
        try:
            if self.components_available and "monitor" in self.components:
                status = self.components["monitor"].check_context_usage()
            else:
                # 简化检查
                status = self.simple_context_check()
            
            self.system_status["last_check"] = time.time()
            
            if status:
                # 记录状态
                if self.components_available and "logger" in self.components:
                    if status.get("status") == "CRITICAL_OVERFLOW":
                        self.components["logger"].log_context_overflow(
                            status["context_length"],
                            status["max_chars"],
                            "system_check"
                        )
                        self.system_status["total_overflows"] += 1
            
            return status
            
        except Exception as e:
            print(f"❌ 上下文检查失败: {e}")
            return None
    
    def simple_context_check(self):
        """简化上下文检查"""
        # 这里可以调用现有的检查脚本或简单估计
        import subprocess
        
        try:
            # 尝试调用现有的检查脚本
            result = subprocess.run(
                ["python3", "/root/.openclaw/workspace/context-compressor-skill/scripts/conversation_compression_checker.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析输出
            usage = 50.0  # 默认
            for line in result.stdout.split('\n'):
                if "上下文使用率" in line and "%" in line:
                    import re
                    match = re.search(r'([\d.]+)%', line)
                    if match:
                        usage = float(match.group(1))
                        break
            
            context_length = self.max_chars * (usage / 100)
            
            # 确定状态
            if usage >= 100:
                status = "CRITICAL_OVERFLOW"
            elif usage >= (self.execution_threshold * 100):
                status = "CRITICAL"
            elif usage >= (self.warning_threshold * 100):
                status = "WARNING"
            else:
                status = "NORMAL"
            
            return {
                "usage_percentage": usage,
                "context_length": context_length,
                "max_chars": self.max_chars,
                "status": status,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"❌ 简化检查失败: {e}")
            # 返回默认状态
            return {
                "usage_percentage": 50.0,
                "context_length": self.max_chars * 0.5,
                "max_chars": self.max_chars,
                "status": "NORMAL",
                "timestamp": time.time()
            }
    
    def decide_compression_action(self, status):
        """决定压缩操作"""
        if not status:
            return None
        
        usage = status.get("usage_percentage", 0)
        context_status = status.get("status", "NORMAL")
        
        actions = []
        
        # 应急情况
        if usage >= 100:
            actions.append({
                "type": "EMERGENCY",
                "priority": "HIGHEST",
                "reason": f"上下文超限 ({usage:.1f}%)",
                "component": "emergency"
            })
        
        # 临界情况
        elif usage >= (self.execution_threshold * 100):
            actions.append({
                "type": "COMPRESSION",
                "priority": "HIGH",
                "reason": f"上下文接近超限 ({usage:.1f}%)",
                "component": "compressor"
            })
        
        # 警告情况
        elif usage >= (self.warning_threshold * 100):
            actions.append({
                "type": "MONITOR",
                "priority": "MEDIUM",
                "reason": f"上下文使用率较高 ({usage:.1f}%)",
                "component": "monitor"
            })
        
        return actions
    
    def execute_compression(self, action):
        """执行压缩操作"""
        if not action:
            return {"success": False, "reason": "no_action"}
        
        action_type = action.get("type")
        component_name = action.get("component")
        
        print(f"🔧 执行压缩操作: {action_type} (优先级: {action.get('priority')})")
        print(f"   原因: {action.get('reason')}")
        
        try:
            if self.components_available and component_name in self.components:
                component = self.components[component_name]
                
                if action_type == "EMERGENCY" and hasattr(component, "execute_emergency_compression"):
                    # 执行应急压缩
                    status = self.check_context_status()
                    if status:
                        result = component.execute_emergency_compression(
                            status["context_length"],
                            status["max_chars"],
                            "system_triggered"
                        )
                elif action_type == "COMPRESSION" and hasattr(component, "compress"):
                    # 执行常规压缩
                    result = component.compress()
                else:
                    result = {"success": False, "reason": "component_not_supported"}
            else:
                # 简化执行
                result = self.simple_compression_execution(action_type)
            
            # 记录压缩操作
            if result.get("success"):
                self.system_status["total_compressions"] += 1
                self.system_status["last_compression"] = time.time()
                
                if self.components_available and "logger" in self.components:
                    self.components["logger"].log_compression_end(
                        None, "success", 0, compressed_to="unknown"
                    )
            
            return result
            
        except Exception as e:
            print(f"❌ 压缩执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def simple_compression_execution(self, action_type):
        """简化压缩执行"""
        if action_type == "EMERGENCY":
            print("💥 执行应急压缩 (简化模式)...")
            print("   建议: 重启当前会话")
            return {
                "success": True,
                "action": "suggest_restart",
                "message": "建议重启会话来清理上下文"
            }
        else:
            print("🔧 执行常规压缩 (简化模式)...")
            print("   建议: 清理工具调用历史")
            return {
                "success": True,
                "action": "suggest_cleanup",
                "message": "建议清理工具调用历史"
            }
    
    def get_system_status(self):
        """获取系统状态"""
        status = self.system_status.copy()
        
        # 添加组件状态
        status["components"] = {}
        if self.components_available:
            for name, component in self.components.items():
                status["components"][name] = "available"
        else:
            status["components"] = {"all": "unavailable"}
        
        # 添加配置信息
        status["config"] = {
            "warning_threshold": self.warning_threshold,
            "execution_threshold": self.execution_threshold,
            "max_chars": self.max_chars,
            "emergency_threshold": self.emergency_threshold
        }
        
        return status
    
    def run_compression_cycle(self):
        """运行压缩周期"""
        print("🔄 开始压缩周期检查")
        print("=" * 50)
        
        # 检查上下文状态
        status = self.check_context_status()
        if not status:
            print("❌ 无法获取上下文状态")
            return
        
        # 显示状态
        status_icons = {
            "NORMAL": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
            "CRITICAL_OVERFLOW": "💥"
        }
        
        icon = status_icons.get(status["status"], "❓")
        print(f"{icon} 上下文状态: {status['status']}")
        print(f"   使用率: {status['usage_percentage']:.1f}%")
        print(f"   长度: {int(status['context_length']):,}/{status['max_chars']:,} 字符")
        
        # 决定压缩操作
        actions = self.decide_compression_action(status)
        
        if actions:
            print(f"\n📋 建议操作 ({len(actions)} 个):")
            for i, action in enumerate(actions):
                print(f"  {i+1}. [{action['priority']}] {action['type']}: {action['reason']}")
            
            # 执行最高优先级操作
            if actions:
                primary_action = actions[0]
                result = self.execute_compression(primary_action)
                print(f"\n📊 执行结果: {result}")
        else:
            print("\n✅ 无需压缩操作")
        
        print("=" * 50)
        return status, actions

def main():
    """主函数"""
    print("🧠 智能压缩系统 v1.0")
    print("=" * 50)
    
    # 创建系统实例
    system = SmartCompressionSystem()
    
    # 显示系统状态
    status = system.get_system_status()
    print(f"📊 系统状态: {'已初始化' if status['initialized'] else '未初始化'}")
    print(f"🔧 组件状态: {len(status['components'])} 个组件")
    
    # 运行压缩周期
    result = system.run_compression_cycle()
    
    # 显示最终状态
    final_status = system.get_system_status()
    print(f"\n📈 统计信息:")
    print(f"   总压缩次数: {final_status['total_compressions']}")
    print(f"   总超限次数: {final_status['total_overflows']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())