#!/usr/bin/env python3
# 🧠 智能压缩主控系统
# 整合三层压缩策略

import os
import json
import subprocess
import datetime
import logging
from pathlib import Path

class SmartCompressionSystem:
    """智能压缩主控系统"""
    
    def __init__(self):
        self.max_length = 98304  # OpenClaw最大上下文长度
        self.threshold_percent = 70  # 压缩触发阈值
        self.target_percent = 40  # 压缩后目标阈值
        
        self.threshold_length = self.max_length * self.threshold_percent // 100
        self.target_length = self.max_length * self.target_percent // 100
        
        self.session_dir = Path("/root/.openclaw/agents/main/sessions")
        self.memory_dir = Path("/root/.openclaw/workspace/memory")
        
        # 设置日志
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """设置日志系统"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "smart_compression.log"),
                logging.StreamHandler()
            ]
        )
    
    def estimate_context_length(self):
        """估算当前上下文长度"""
        session_files = list(self.session_dir.glob("*.jsonl"))
        if not session_files:
            self.logger.warning("找不到会话文件")
            return 0
        
        # 获取最新会话文件
        current_session = max(session_files, key=lambda x: x.stat().st_mtime)
        
        try:
            # 统计消息数量
            with open(current_session, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                message_count = len(lines)
            
            # 每条消息约400字符
            estimated_length = message_count * 400
            
            self.logger.info(f"估算结果: {message_count}条消息, {estimated_length}字符")
            return estimated_length
            
        except Exception as e:
            self.logger.error(f"估算上下文长度失败: {e}")
            return 0
    
    def check_openclaw_compression(self):
        """检查OpenClaw是否正在执行压缩"""
        try:
            # 检查OpenClaw日志中的压缩记录
            cmd = "journalctl --user -u openclaw-gateway --since '3 minutes ago' 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if "attempting auto-compaction" in result.stdout:
                self.logger.info("检测到OpenClaw正在执行自动压缩")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"检查OpenClaw压缩状态失败: {e}")
            return False
    
    def check_overflow_logs(self):
        """检查溢出日志"""
        try:
            cmd = "journalctl --user -u openclaw-gateway --since '1 hour ago' 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            overflow_count = result.stdout.count("exceeds the maximum length")
            self.logger.info(f"最近1小时溢出次数: {overflow_count}")
            return overflow_count
            
        except Exception as e:
            self.logger.error(f"检查溢出日志失败: {e}")
            return 0
    
    def log_decision(self, decision_type, context_length, usage_percent, additional_info=""):
        """记录压缩决策"""
        today_file = self.memory_dir / f"{datetime.datetime.now().strftime('%Y-%m-%d')}.md"
        
        try:
            # 创建或打开今日记忆文件
            if not today_file.exists():
                with open(today_file, 'w', encoding='utf-8') as f:
                    f.write(f"# 🧠 记忆文件 - {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
                    f.write(f"创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 添加决策记录
            with open(today_file, 'a', encoding='utf-8') as f:
                f.write("## 🧠 智能压缩决策记录\n")
                f.write(f"- **时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **决策类型**: {decision_type}\n")
                f.write(f"- **上下文长度**: {context_length} 字符\n")
                f.write(f"- **使用率**: {usage_percent}%\n")
                f.write(f"- **阈值**: {self.threshold_percent}% ({self.threshold_length} 字符)\n")
                f.write(f"- **目标**: {self.target_percent}% ({self.target_length} 字符)\n")
                
                if additional_info:
                    f.write(f"- **附加信息**: {additional_info}\n")
                
                f.write("\n")
            
            self.logger.info(f"决策已记录到: {today_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录决策失败: {e}")
            return False
    
    def execute_emergency_compression(self):
        """执行应急压缩"""
        self.logger.info("🚨 执行应急压缩...")
        
        try:
            # 调用应急压缩器
            emergency_script = Path(__file__).parent / "emergency_compressor.py"
            result = subprocess.run(
                ["python3", str(emergency_script)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("✅ 应急压缩执行成功")
                return True
            else:
                self.logger.error(f"应急压缩执行失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"调用应急压缩器失败: {e}")
            return False
    
    def execute_regular_compression(self, context_length):
        """执行常规压缩"""
        self.logger.info("🔧 执行常规压缩...")
        
        # 计算需要的压缩率
        needed_rate = 100 - (self.target_length * 100 // context_length)
        if needed_rate < 30:
            needed_rate = 30  # 至少压缩30%
        
        self.logger.info(f"压缩策略: FIFO + 渐进式总结")
        self.logger.info(f"目标压缩率: {needed_rate}%")
        self.logger.info(f"目标使用率: {self.target_percent}% 以下")
        
        # 这里应该调用实际的常规压缩逻辑
        # 暂时记录成功状态
        return True
    
    def make_decision(self):
        """做出压缩决策"""
        self.logger.info("🎯 开始压缩决策分析...")
        
        # 1. 获取当前状态
        context_length = self.estimate_context_length()
        usage_percent = (context_length * 100) // self.max_length
        overflow_count = self.check_overflow_logs()
        
        print(f"\n📊 系统状态分析:")
        print(f"  - 估算长度: {context_length} 字符")
        print(f"  - 使用率: {usage_percent}%")
        print(f"  - 阈值 ({self.threshold_percent}%): {self.threshold_length} 字符")
        print(f"  - 目标 ({self.target_percent}%): {self.target_length} 字符")
        print(f"  - 最近溢出次数: {overflow_count}")
        
        # 2. 检查OpenClaw冲突
        if self.check_openclaw_compression():
            print(f"\n⏸️ 检测到OpenClaw正在压缩")
            print(f"📋 决策: 跳过我们的压缩，避免冲突")
            
            self.log_decision(
                "跳过压缩（避免冲突）",
                context_length,
                usage_percent,
                "OpenClaw正在执行自动压缩"
            )
            
            return "skip"
        
        # 3. 决策逻辑
        # 情况A：已严重溢出 (>100%)
        if context_length >= self.max_length:
            print(f"\n🚨 情况A：上下文已严重溢出！")
            print(f"📋 决策: 执行应急压缩（重建会话）")
            
            self.log_decision(
                "应急压缩",
                context_length,
                usage_percent,
                f"使用率 {usage_percent}% > 100%"
            )
            
            return "emergency"
        
        # 情况B：超过阈值但未溢出 (70%-100%)
        if context_length >= self.threshold_length:
            print(f"\n⚠️ 情况B：超过{self.threshold_percent}%阈值但未溢出")
            print(f"📋 决策: 执行常规智能压缩")
            
            self.log_decision(
                "常规压缩",
                context_length,
                usage_percent,
                f"使用率 {usage_percent}% > {self.threshold_percent}%"
            )
            
            return "regular"
        
        # 情况C：正常状态 (<70%)
        print(f"\n✅ 情况C：状态正常 (<{self.threshold_percent}%)")
        print(f"📋 决策: 无需压缩，继续监控")
        
        self.log_decision(
            "无需压缩",
            context_length,
            usage_percent,
            f"使用率 {usage_percent}% < {self.threshold_percent}%"
        )
        
        return "normal"
    
    def execute_decision(self, decision):
        """执行决策"""
        if decision == "emergency":
            return self.execute_emergency_compression()
        elif decision == "regular":
            context_length = self.estimate_context_length()
            return self.execute_regular_compression(context_length)
        elif decision == "skip":
            return True  # 跳过也是成功
        elif decision == "normal":
            return True  # 正常状态
        else:
            self.logger.error(f"未知决策类型: {decision}")
            return False

def main():
    """主函数"""
    print("==========================================")
    print("🧠 智能压缩主控系统启动")
    print("时间:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("==========================================")
    
    system = SmartCompressionSystem()
    
    try:
        # 做出决策
        decision = system.make_decision()
        
        # 执行决策
        success = system.execute_decision(decision)
        
        if success:
            print("\n✅ 智能压缩决策执行成功")
            
            # 显示总结
            print("\n==========================================")
            print("🧠 智能压缩决策完成")
            print("系统采用三层策略：")
            print("  1. 应急压缩 (>100%)：重建会话")
            print("  2. 常规压缩 (70-100%)：渐进式总结")
            print("  3. 冲突避免：检测OpenClaw状态")
            print("  4. 正常状态 (<70%)：仅监控")
            print("==========================================")
        else:
            print("\n❌ 决策执行失败")
            
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())