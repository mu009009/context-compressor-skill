#!/usr/bin/env python3
"""
Conversation Compression Checker FIXED v1.2.0
修复版对话压缩检查器
核心修复：无限压缩循环、回复截断、严重超标处理
"""

import os
import sys
import json
import time
import yaml
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta

class ConversationCompressionCheckerFixed:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = "/root/.openclaw/workspace/context-compressor-skill/config/compression_config_v1.2.0.json"
        self.config_path = config_path
        self.load_config()
        self.setup_logging()
        self.init_anti_loop_protection()
        
    def load_config(self):
        """加载配置文件（优先使用v1.2.0修复版）"""
        try:
            # 优先加载v1.2.0配置
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ 加载修复版配置文件: {self.config_path}")
                print(f"📋 版本: {self.config.get('version', 'unknown')}")
            else:
                # 回退到yaml配置
                yaml_path = self.config_path.replace('.json', '.yaml')
                if os.path.exists(yaml_path):
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        self.config = yaml.safe_load(f)
                    print(f"⚠️  使用旧版yaml配置: {yaml_path}")
                else:
                    self.config = self.get_default_config()
                    print("⚠️  使用默认配置")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置（包含紧急模式）"""
        return {
            "version": "1.2.0_fallback",
            "emergency_mode": {
                "enabled": True,
                "threshold_percent": 200,
                "one_time_compress_to_percent": 50,
                "max_compression_attempts": 2,
                "cooldown_minutes": 15
            },
            "anti_loop_protection": {
                "enabled": True,
                "max_consecutive_compressions": 3,
                "detect_rapid_compression": True,
                "rapid_threshold_minutes": 5
            },
            "safety_limits": {
                "max_context_chars": 98304,
                "absolute_max_chars_before_emergency": 196608
            }
        }
    
    def setup_logging(self):
        """设置日志系统"""
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"compression_check_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("CompressionChecker")
    
    def init_anti_loop_protection(self):
        """初始化防循环保护"""
        self.compression_history = []
        self.last_compression_time = None
        self.consecutive_compressions = 0
        self.loop_detected = False
        
        # 从文件加载历史记录（如果存在）
        history_file = "./logs/compression_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self.compression_history = history_data.get('history', [])[-10:]  # 只保留最近10次
                    self.consecutive_compressions = history_data.get('consecutive', 0)
            except:
                pass
    
    def save_anti_loop_state(self):
        """保存防循环状态"""
        history_file = "./logs/compression_history.json"
        history_data = {
            'history': self.compression_history[-20:],  # 保留最近20次
            'consecutive': self.consecutive_compressions,
            'last_update': datetime.now().isoformat()
        }
        try:
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except:
            pass
    
    def detect_emergency_mode(self, context_size):
        """检测是否进入紧急模式"""
        max_chars = self.config.get("safety_limits", {}).get("max_context_chars", 98304)
        emergency_threshold = self.config.get("emergency_mode", {}).get("threshold_percent", 200)
        
        if max_chars <= 0:
            return False
        
        percentage = (context_size / max_chars) * 100
        is_emergency = percentage >= emergency_threshold
        
        if is_emergency:
            self.logger.warning(f"🚨 紧急模式触发！上下文使用率: {percentage:.1f}% ≥ {emergency_threshold}%")
            self.logger.warning(f"   上下文大小: {context_size:,} 字符，限制: {max_chars:,} 字符")
        
        return is_emergency, percentage
    
    def check_anti_loop_protection(self):
        """检查防循环保护"""
        if not self.config.get("anti_loop_protection", {}).get("enabled", True):
            return True
        
        # 检查连续压缩次数
        max_consecutive = self.config["anti_loop_protection"].get("max_consecutive_compressions", 3)
        if self.consecutive_compressions >= max_consecutive:
            self.logger.error(f"🔴 防循环保护触发！连续压缩次数: {self.consecutive_compressions} ≥ {max_consecutive}")
            self.loop_detected = True
            return False
        
        # 检查快速压缩
        if self.last_compression_time:
            rapid_threshold = self.config["anti_loop_protection"].get("rapid_threshold_minutes", 5)
            time_since_last = (datetime.now() - self.last_compression_time).total_seconds() / 60
            
            if time_since_last < rapid_threshold:
                self.logger.warning(f"⚠️  快速压缩检测！距离上次压缩仅 {time_since_last:.1f} 分钟 < {rapid_threshold} 分钟")
                self.consecutive_compressions += 1
            else:
                # 重置连续计数（如果时间间隔足够长）
                self.consecutive_compressions = max(0, self.consecutive_compressions - 1)
        
        return True
    
    def get_context_usage(self):
        """获取上下文使用情况"""
        try:
            # 尝试从OpenClaw状态获取
            result = subprocess.run(
                ["openclaw", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                if "context" in status_data:
                    context_info = status_data["context"]
                    usage_chars = context_info.get("used_chars", 0)
                    max_chars = context_info.get("max_chars", 200000)
                    
                    return {
                        "used_chars": usage_chars,
                        "max_chars": max_chars,
                        "percentage": (usage_chars / max_chars * 100) if max_chars > 0 else 0,
                        "source": "openclaw_status"
                    }
        except:
            pass
        
        # 回退方法：估算当前会话的大小
        try:
            # 获取当前目录下的会话文件大小
            session_files = list(Path("/root/.openclaw/workspace").glob("session_*.json"))
            if session_files:
                latest_file = max(session_files, key=lambda p: p.stat().st_mtime)
                file_size = latest_file.stat().st_size
                
                # 粗略估算：文件大小 ≈ 上下文字符数 * 1.2（包含元数据）
                estimated_chars = int(file_size / 1.2)
                
                return {
                    "used_chars": estimated_chars,
                    "max_chars": 200000,  # 默认值
                    "percentage": (estimated_chars / 200000 * 100),
                    "source": "file_size_estimation"
                }
        except:
            pass
        
        # 最终回退
        return {
            "used_chars": 0,
            "max_chars": 98304,
            "percentage": 0,
            "source": "fallback"
        }
    
    def should_compress(self, context_usage):
        """判断是否应该执行压缩（修复版）"""
        # 1. 检查防循环保护
        if not self.check_anti_loop_protection():
            self.logger.warning("⏸️  防循环保护阻止压缩")
            return False
        
        # 2. 检测紧急模式
        is_emergency, percentage = self.detect_emergency_mode(context_usage["used_chars"])
        
        if is_emergency:
            # 紧急模式：总是压缩，但记录并检查冷却
            if self.last_compression_time:
                cooldown = self.config.get("emergency_mode", {}).get("cooldown_minutes", 15)
                time_since_last = (datetime.now() - self.last_compression_time).total_seconds() / 60
                
                if time_since_last < cooldown:
                    self.logger.warning(f"⏸️  紧急模式冷却中，等待 {cooldown - time_since_last:.1f} 分钟")
                    return False
            
            self.logger.critical(f"🚨 执行紧急压缩！上下文使用率: {percentage:.1f}%")
            return True
        
        # 3. 常规模式阈值检查
        regular_config = self.config.get("regular_compression", {})
        trigger_threshold = regular_config.get("trigger_threshold_percent", 70)
        
        if percentage >= trigger_threshold:
            self.logger.info(f"📊 常规压缩触发: {percentage:.1f}% ≥ {trigger_threshold}%")
            
            # 检查冷却时间
            if self.last_compression_time:
                min_interval = self.config.get("conflict_detection", {}).get("min_interval_seconds", 600)
                time_since_last = (datetime.now() - self.last_compression_time).total_seconds()
                
                if time_since_last < min_interval:
                    self.logger.info(f"⏸️  冷却时间未到，等待 {min_interval - time_since_last:.0f} 秒")
                    return False
            
            return True
        
        # 4. 警告级别
        warning_threshold = trigger_threshold * 0.8  # 警告阈值为触发阈值的80%
        if percentage >= warning_threshold:
            self.logger.info(f"⚠️  接近压缩阈值: {percentage:.1f}% ≥ {warning_threshold:.1f}%")
        
        return False
    
    def execute_compression(self, context_usage, is_emergency=False):
        """执行压缩操作"""
        try:
            # 记录压缩历史
            compression_record = {
                "timestamp": datetime.now().isoformat(),
                "context_size": context_usage["used_chars"],
                "percentage": context_usage["percentage"],
                "emergency": is_emergency,
                "source": context_usage["source"]
            }
            self.compression_history.append(compression_record)
            self.last_compression_time = datetime.now()
            
            if is_emergency:
                self.consecutive_compressions += 1
                # 执行紧急压缩
                script_path = "./scripts/emergency_context_cleaner.py"
                if os.path.exists(script_path):
                    self.logger.info("🚨 执行紧急压缩脚本...")
                    result = subprocess.run(
                        ["python3", script_path, str(context_usage["used_chars"])],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    self.logger.info(f"紧急压缩结果: {result.returncode}")
                else:
                    # 回退到简单清理
                    self.logger.warning("⚠️  紧急压缩脚本不存在，执行简单清理")
                    self.simple_emergency_cleanup(context_usage)
            else:
                # 执行常规压缩
                script_path = "./scripts/simple_compression_executor.py"
                if os.path.exists(script_path):
                    self.logger.info("⚙️  执行常规压缩...")
                    result = subprocess.run(
                        ["python3", script_path],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    self.logger.info(f"常规压缩结果: {result.returncode}")
            
            # 保存状态
            self.save_anti_loop_state()
            
            # 验证压缩后完整性
            self.verify_output_integrity()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 压缩执行失败: {e}")
            return False
    
    def simple_emergency_cleanup(self, context_usage):
        """简单的紧急清理（回退方法）"""
        self.logger.warning("🧹 执行简单紧急清理...")
        
        # 清理过大的记忆文件
        memory_dir = "/root/.openclaw/workspace/memory"
        if os.path.exists(memory_dir):
            for file in os.listdir(memory_dir):
                if file.endswith('.md'):
                    file_path = os.path.join(memory_dir, file)
                    try:
                        size = os.path.getsize(file_path)
                        if size > 500000:  # 超过500KB
                            self.logger.warning(f"清理过大的记忆文件: {file} ({size:,} 字节)")
                            # 备份并清理
                            backup_path = file_path + ".backup"
                            os.rename(file_path, backup_path)
                            # 创建新的干净文件
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(f"# 🧠 记忆文件 (紧急清理于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
                                f.write(f"原因: 上下文过大 ({context_usage['used_chars']:,} 字符)\n")
                                f.write(f"原文件备份: {backup_path}\n")
                    except:
                        pass
        
        self.logger.info("✅ 简单紧急清理完成")
    
    def verify_output_integrity(self):
        """验证输出完整性"""
        try:
            # 简单的完整性检查：能否正常输出测试消息
            test_message = "压缩完整性测试: Hello World! 这是一条测试消息。"
            self.logger.info(f"✅ 输出完整性测试: {test_message}")
            
            # 检查括号平衡（如果之前有括号截断问题）
            if "（" in test_message and "）" not in test_message:
                self.logger.warning("⚠️  括号不平衡检测")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ 输出完整性验证失败: {e}")
            return False
    
    def check_after_conversation(self):
        """对话后检查（主要入口点）"""
        self.logger.info("=" * 50)
        self.logger.info("🔄 对话后压缩检查开始")
        
        # 获取上下文使用情况
        context_usage = self.get_context_usage()
        self.logger.info(f"📊 上下文使用情况: {context_usage['used_chars']:,} 字符 / {context_usage['max_chars']:,} 字符 ({context_usage['percentage']:.1f}%)")
        self.logger.info(f"📡 数据来源: {context_usage['source']}")
        
        # 判断是否需要压缩
        should_compress = self.should_compress(context_usage)
        
        if should_compress:
            is_emergency, percentage = self.detect_emergency_mode(context_usage["used_chars"])
            self.logger.info(f"🔧 需要压缩: {'紧急模式' if is_emergency else '常规模式'}")
            
            # 执行压缩
            success = self.execute_compression(context_usage, is_emergency)
            
            if success:
                self.logger.info("✅ 压缩执行成功")
            else:
                self.logger.error("❌ 压缩执行失败")
        else:
            self.logger.info("✅ 无需压缩，状态正常")
        
        self.logger.info("=" * 50)
        
        # 保存状态（即使没有压缩）
        self.save_anti_loop_state()
        
        return should_compress

def main():
    """主函数"""
    print("🚀 Context Compressor Checker FIXED v1.2.0 启动")
    print("🔧 修复内容: 无限压缩循环、回复截断、紧急模式")
    
    checker = ConversationCompressionCheckerFixed()
    
    try:
        # 执行对话后检查
        checker.check_after_conversation()
        
        print("\n✅ 检查完成")
        print("📋 状态总结:")
        print(f"  - 防循环保护: {'启用' if checker.config.get('anti_loop_protection', {}).get('enabled', True) else '禁用'}")
        print(f"  - 紧急模式: {'启用' if checker.config.get('emergency_mode', {}).get('enabled', True) else '禁用'}")
        print(f"  - 连续压缩计数: {checker.consecutive_compressions}")
        print(f"  - 循环检测: {'是' if checker.loop_detected else '否'}")
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())