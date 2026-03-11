#!/usr/bin/env python3
"""
Conversation Compression Checker
对话压缩检查器
核心功能：每次对话后检查上下文大小，触发压缩
"""

import os
import sys
import json
import time
import yaml
import subprocess
from pathlib import Path

class ConversationCompressionChecker:
    def __init__(self, config_path="config/compression_config.yaml"):
        self.config_path = config_path
        self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f"✅ 压缩配置文件加载成功: {self.config_path}")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "compression_strategy": {
                "trigger_timing": "after_conversation",
                "thresholds": {"warning": 0.85, "execution": 0.90},
                "context_limits": {
                    "max_chars": 98304,
                    "warning_chars": 83558,
                    "compress_chars": 88474
                }
            }
        }
    
    def setup_logging(self):
        """设置日志"""
        log_dir = self.config.get("monitoring", {}).get("log_dir", "./logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"compression_{time.strftime('%Y%m%d')}.log")
    
    def get_context_usage(self):
        """获取当前上下文使用情况"""
        try:
            # 尝试从OpenClaw日志或状态获取上下文使用率
            result = subprocess.run(
                "openclaw status 2>&1 | grep -i 'context\|token' | head -5",
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 简化：返回模拟数据（实际应解析OpenClaw输出）
            return {
                "estimated_chars": 45000,  # 模拟值，实际需要解析
                "estimated_percentage": 0.46,
                "status": "normal"
            }
        except Exception as e:
            print(f"⚠️ 获取上下文使用率失败: {e}")
            return {"estimated_percentage": 0.0, "status": "unknown"}
    
    def is_openclaw_compressing(self):
        """检查OpenClaw是否正在执行压缩"""
        try:
            # 检查OpenClaw日志中是否有压缩相关活动
            result = subprocess.run(
                "journalctl --user -u openclaw-gateway --since '1 minute ago' | grep -i 'compress\|compact' | wc -l",
                shell=True,
                capture_output=True,
                text=True
            )
            active_compressions = int(result.stdout.strip())
            return active_compressions > 0
        except:
            return False
    
    def should_compress(self, context_usage):
        """判断是否应该执行压缩"""
        percentage = context_usage.get("estimated_percentage", 0)
        
        # 检查防冲突：OpenClaw是否已在压缩
        if self.config["compression_strategy"]["conflict_prevention"]["check_openclaw_compression"]:
            if self.is_openclaw_compressing():
                print("⏸️  OpenClaw正在执行压缩，跳过本次检查")
                return False
        
        # 检查阈值
        warning_threshold = self.config["compression_strategy"]["thresholds"]["warning"]
        execution_threshold = self.config["compression_strategy"]["thresholds"]["execution"]
        
        if percentage >= execution_threshold:
            print(f"🚨 上下文使用率 {percentage:.1%} ≥ {execution_threshold:.0%}，需要压缩")
            return True
        elif percentage >= warning_threshold:
            print(f"⚠️  上下文使用率 {percentage:.1%} ≥ {warning_threshold:.0%}，达到警告级别")
            return False  # 警告但不压缩
        else:
            print(f"✅ 上下文使用率 {percentage:.1%}，正常范围")
            return False
    
    def execute_compression(self):
        """执行压缩操作"""
        print("🔄 开始执行上下文压缩...")
        
        # 调用压缩执行脚本
        try:
            script_path = "../conversation_compression_executor.sh"
            if os.path.exists(script_path):
                result = subprocess.run(
                    ["bash", script_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✅ 压缩执行成功")
                    return True
                else:
                    print(f"❌ 压缩执行失败: {result.stderr}")
                    return False
            else:
                print(f"❌ 压缩脚本不存在: {script_path}")
                return False
        except Exception as e:
            print(f"❌ 压缩执行异常: {e}")
            return False
    
    def check_after_conversation(self):
        """对话后检查（主入口点）"""
        print("🔍 对话后上下文检查开始...")
        
        # 获取当前上下文使用情况
        context_usage = self.get_context_usage()
        percentage = context_usage.get("estimated_percentage", 0)
        
        # 记录日志
        self.log_check(percentage)
        
        # 判断是否需要压缩
        if self.should_compress(context_usage):
            return self.execute_compression()
        else:
            return False
    
    def log_check(self, percentage):
        """记录检查日志"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - 上下文使用率: {percentage:.1%}\n")
        except:
            pass

if __name__ == "__main__":
    checker = ConversationCompressionChecker()
    
    # 模拟对话后检查
    print("🧪 测试模式：模拟对话后检查")
    checker.check_after_conversation()
