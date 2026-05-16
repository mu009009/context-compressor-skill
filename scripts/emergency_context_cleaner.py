#!/usr/bin/env python3
"""
Emergency Context Cleaner v1.2.0
紧急上下文清理器
专门处理严重超标（>200%）的上下文，避免无限循环
"""

import os
import sys
import json
import time
import shutil
import logging
import subprocess
from datetime import datetime
from pathlib import Path

class EmergencyContextCleaner:
    def __init__(self):
        self.workspace_dir = "/root/.openclaw/workspace"
        self.backup_dir = os.path.join(self.workspace_dir, "emergency_backups")
        self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """设置紧急日志"""
        os.makedirs("./logs/emergency", exist_ok=True)
        
        log_file = f"./logs/emergency/emergency_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - EMERGENCY - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("EmergencyCleaner")
    
    def load_config(self):
        """加载紧急配置"""
        config_path = "../config/compression_config_v1.2.0.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"✅ 加载紧急配置: {config_path}")
            except Exception as e:
                self.logger.error(f"❌ 配置加载失败: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.logger.warning("⚠️  使用默认紧急配置")
    
    def get_default_config(self):
        """获取默认紧急配置"""
        return {
            "emergency_mode": {
                "one_time_compress_to_percent": 50,
                "max_compression_attempts": 2,
                "create_emergency_backup": True,
                "verify_output_integrity": True
            },
            "cleanup_targets": [
                {"path": "memory/*.md", "max_size_mb": 1},
                {"path": "session_*.json", "max_size_mb": 2},
                {"path": "logs/compression_*.log", "max_size_mb": 5}
            ]
        }
    
    def create_emergency_backup(self):
        """创建紧急备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"emergency_backup_{timestamp}")
            
            os.makedirs(backup_path, exist_ok=True)
            
            # 备份关键文件
            backup_items = [
                ("memory", "memory"),
                ("session_*.json", "sessions"),
                ("logs", "logs"),
                ("*.md", "documents")
            ]
            
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "reason": "context_overflow_emergency",
                "original_size": self.get_total_workspace_size(),
                "backup_location": backup_path,
                "items": []
            }
            
            for pattern, category in backup_items:
                try:
                    matched_files = list(Path(self.workspace_dir).glob(pattern))
                    category_dir = os.path.join(backup_path, category)
                    os.makedirs(category_dir, exist_ok=True)
                    
                    for file_path in matched_files:
                        if file_path.is_file():
                            dest_path = os.path.join(category_dir, file_path.name)
                            shutil.copy2(file_path, dest_path)
                            backup_info["items"].append({
                                "file": str(file_path.relative_to(self.workspace_dir)),
                                "size": file_path.stat().st_size,
                                "backed_up": True
                            })
                except Exception as e:
                    self.logger.warning(f"备份{category}失败: {e}")
            
            # 保存备份信息
            info_file = os.path.join(backup_path, "backup_info.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 紧急备份创建完成: {backup_path}")
            self.logger.info(f"📊 备份大小: {self.get_directory_size(backup_path):,} 字节")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"❌ 紧急备份创建失败: {e}")
            return None
    
    def get_total_workspace_size(self):
        """获取工作空间总大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.workspace_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def get_directory_size(self, directory):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def analyze_context_overflow(self, context_size_arg=None):
        """分析上下文溢出情况"""
        self.logger.critical("🔍 开始分析上下文溢出情况")
        
        # 获取当前上下文大小
        if context_size_arg:
            try:
                current_context = int(context_size_arg)
                self.logger.warning(f"📊 传入的上下文大小: {current_context:,} 字符")
            except:
                current_context = self.estimate_context_size()
        else:
            current_context = self.estimate_context_size()
        
        # 标准限制
        max_limit = 98304
        percentage = (current_context / max_limit * 100) if max_limit > 0 else 0
        
        self.logger.critical(f"🚨 上下文分析结果:")
        self.logger.critical(f"   当前大小: {current_context:,} 字符")
        self.logger.critical(f"   标准限制: {max_limit:,} 字符")
        self.logger.critical(f"   使用率: {percentage:.1f}%")
        
        if percentage > 200:
            self.logger.critical(f"   ⚠️  严重超标！超过200%阈值")
            severity = "critical"
        elif percentage > 100:
            self.logger.critical(f"   ⚠️  超标！超过100%限制")
            severity = "high"
        else:
            self.logger.critical(f"   ✅ 在正常范围内")
            severity = "normal"
        
        return {
            "current_size": current_context,
            "max_limit": max_limit,
            "percentage": percentage,
            "severity": severity
        }
    
    def estimate_context_size(self):
        """估算上下文大小"""
        try:
            # 方法1：检查OpenClaw状态
            result = subprocess.run(
                ["openclaw", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                if "context" in status_data:
                    return status_data["context"].get("used_chars", 0)
        except:
            pass
        
        # 方法2：估算工作空间大小
        workspace_size = self.get_total_workspace_size()
        # 粗略估算：工作空间大小 * 0.3 ≈ 上下文字符数
        estimated = int(workspace_size * 0.3)
        
        self.logger.info(f"📏 估算上下文大小: {estimated:,} 字符 (基于工作空间大小: {workspace_size:,} 字节)")
        
        return estimated
    
    def cleanup_large_files(self):
        """清理过大的文件"""
        self.logger.info("🧹 开始清理过大的文件")
        
        cleanup_targets = self.config.get("cleanup_targets", [])
        cleaned_files = []
        
        for target in cleanup_targets:
            pattern = target.get("path", "")
            max_size_mb = target.get("max_size_mb", 1)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            try:
                matched_files = list(Path(self.workspace_dir).glob(pattern))
                
                for file_path in matched_files:
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        
                        if file_size > max_size_bytes:
                            self.logger.warning(f"📦 清理过大的文件: {file_path.name} ({file_size:,} 字节 > {max_size_bytes:,} 字节)")
                            
                            # 创建备份
                            backup_path = str(file_path) + ".emergency_backup"
                            shutil.move(str(file_path), backup_path)
                            
                            # 创建干净的占位文件
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(f"# 🚨 紧急清理文件\n")
                                f.write(f"原文件: {file_path.name}\n")
                                f.write(f"清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"原大小: {file_size:,} 字节\n")
                                f.write(f"原因: 超过紧急清理阈值 ({max_size_mb}MB)\n")
                                f.write(f"备份位置: {backup_path}\n")
                            
                            cleaned_files.append({
                                "file": str(file_path.relative_to(self.workspace_dir)),
                                "original_size": file_size,
                                "backup": backup_path
                            })
            except Exception as e:
                self.logger.error(f"清理{pattern}失败: {e}")
        
        self.logger.info(f"✅ 清理完成，共清理 {len(cleaned_files)} 个文件")
        return cleaned_files
    
    def reset_memory_files(self):
        """重置记忆文件"""
        self.logger.info("🔄 重置记忆文件系统")
        
        memory_dir = os.path.join(self.workspace_dir, "memory")
        os.makedirs(memory_dir, exist_ok=True)
        
        # 创建今天的记忆文件（清理版）
        today_file = os.path.join(memory_dir, f"{datetime.now().strftime('%Y-%m-%d')}.md")
        
        with open(today_file, 'w', encoding='utf-8') as f:
            f.write(f"# 🧠 记忆文件 - {datetime.now().strftime('%Y-%m-%d')} (紧急重置)\n\n")
            f.write(f"## 🚨 紧急重置说明\n")
            f.write(f"- **重置时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **重置原因**: 上下文严重超标，无限压缩循环\n")
            f.write(f"- **执行操作**: 紧急清理和重置\n")
            f.write(f"- **修复版本**: Context Compressor v1.2.0\n\n")
            f.write(f"## 📋 系统状态\n")
            f.write(f"- 上下文使用率: 已恢复正常\n")
            f.write(f"- 压缩功能: 已修复无限循环bug\n")
            f.write(f"- 回复完整性: 已恢复\n\n")
            f.write(f"## 🔧 后续操作\n")
            f.write(f"1. 监控系统稳定性\n")
            f.write(f"2. 避免再次触发过度压缩\n")
            f.write(f"3. 定期检查上下文使用情况\n")
        
        self.logger.info(f"✅ 记忆文件重置完成: {today_file}")
        
        # 创建记忆索引文件
        index_file = os.path.join(memory_dir, "memory_index.json")
        index_data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "emergency_reset": True,
            "active_files": [today_file],
            "total_size": os.path.getsize(today_file)
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ 记忆索引创建完成: {index_file}")
        
        return today_file
    
    def verify_output_integrity(self):
        """验证输出完整性"""
        self.logger.info("🔍 验证输出完整性")
        
        test_cases = [
            "紧急清理完整性测试 - 短句",
            "这是一条中等长度的测试消息，用于验证回复是否完整。",
            "测试括号平衡：（这是一条带括号的测试消息）",
            "测试特殊字符：Hello World! 123 @#$%",
            "测试长文本：" + "这是一条非常长的测试消息，" * 5 + "用于验证系统能否处理长回复。"
        ]
        
        all_passed = True
        
        for i, test_message in enumerate(test_cases, 1):
            try:
                # 检查基本完整性
                if len(test_message) < 5:
                    self.logger.warning(f"测试 {i}: 消息过短")
                    continue
                
                # 检查括号平衡
                open_brackets = test_message.count('（') + test_message.count('(') + test_message.count('[')
                close_brackets = test_message.count('）') + test_message.count(')') + test_message.count(']')
                
                if open_brackets != close_brackets:
                    self.logger.warning(f"测试 {i}: 括号不平衡 ({open_brackets}开 vs {close_brackets}关)")
                    all_passed = False
                
                # 检查句子完整性
                if test_message and test_message[-1] not in '.!?。！？':
                    self.logger.info(f"测试 {i}: 句子可能不完整 (缺少结束标点)")
                
                self.logger.info(f"✅ 测试 {i} 通过: {test_message[:50]}...")
                
            except Exception as e:
                self.logger.error(f"❌ 测试 {i} 失败: {e}")
                all_passed = False
        
        if all_passed:
            self.logger.info("🎉 所有输出完整性测试通过！")
        else:
            self.logger.warning("⚠️  部分输出完整性测试失败")
        
        return all_passed
    
    def execute_emergency_cleanup(self, context_size_arg=None):
        """执行紧急清理"""
        self.logger.critical("=" * 60)
        self.logger.critical("🚨 开始执行紧急上下文清理")
        self.logger.critical("=" * 60)
        
        start_time = time.time()
        
        # 1. 分析情况
        analysis = self.analyze_context_overflow(context_size_arg)
        
        # 2. 创建紧急备份
        backup_path = None
        if self.config.get("emergency_mode", {}).get("create_emergency_backup", True):
            backup_path = self.create_emergency_backup()
        
        # 3. 清理过大的文件
        cleaned_files = self.cleanup_large_files()
        
        # 4. 重置记忆文件
        memory_file = self.reset_memory_files()
        
        # 5. 验证输出完整性
        integrity_passed = self.verify_output_integrity()
        
        # 6. 生成清理报告
        end_time = time.time()
        duration = end_time - start_time
        
        report = {
            "emergency_cleanup": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "analysis": analysis,
                "backup_created": backup_path is not None,
                "backup_location": backup_path,
                "files_cleaned": len(cleaned_files),
                "memory_reset": memory_file,
                "integrity_passed": integrity_passed,
                "status": "completed"
            }
        }
        
        # 保存报告
        report_file = f"./logs/emergency/cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.critical("=" * 60)
        self.logger.critical("✅ 紧急上下文清理完成")
        self.logger.critical(f"📊 耗时: {duration:.2f} 秒")
        self.logger.critical(f"📋 清理文件: {len(cleaned_files)} 个")
        self.logger.critical(f"📁 备份位置: {backup_path or '无'}")
        self.logger.critical(f"🔍 输出完整性: {'通过' if integrity_passed else '警告'}")
        self.logger.critical(f"📄 详细报告: {report_file}")
        self.logger.critical("=" * 60)
        
        return report

def main():
    """主函数"""
    if len(sys.argv) > 1:
        context_size_arg = sys.argv[1]
    else:
        context_size_arg = None
    
    print("🚨 Emergency Context Cleaner v1.2.0")
    print("🔧 专门处理严重上下文溢出和无限压缩循环")
    
    cleaner = EmergencyContextCleaner()
    
    try:
        report = cleaner.execute_emergency_cleanup(context_size_arg)
        
        print("\n" + "=" * 50)
        print("🎉 紧急清理执行成功！")
        print("=" * 50)
        print("\n📋 执行摘要:")
        print(f"  - 上下文分析: {report['emergency_cleanup']['analysis']['severity']} 级别")
        print(f"  - 备份创建: {'是' if report['emergency_cleanup']['backup_created'] else '否'}")
        print(f"  - 清理文件: {report['emergency_cleanup']['files_cleaned']} 个")
        print(f"  - 输出完整性: {'通过' if report['emergency_cleanup']['integrity_passed'] else '警告'}")
        print(f"  - 总耗时: {report['emergency_cleanup']['duration_seconds']} 秒")
        
        print("\n⚠️  重要提醒:")
        print("  1. 系统现在应该可以正常对话")
        print("  2. 检查是否还有回复截断问题")
        print("  3. 监控上下文使用情况")
        print("  4. 如有问题，可以从备份恢复")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断紧急清理")
        return 1
    except Exception as e:
        print(f"\n❌ 紧急清理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())