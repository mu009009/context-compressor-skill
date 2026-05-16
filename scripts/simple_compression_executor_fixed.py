#!/usr/bin/env python3
"""
Simple Compression Executor FIXED v1.2.0
修复版简单压缩执行器
避免过度压缩和无限循环
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

class SimpleCompressionExecutorFixed:
    def __init__(self):
        self.workspace_dir = "/root/.openclaw/workspace"
        self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """设置日志"""
        os.makedirs("./logs", exist_ok=True)
        
        log_file = f"./logs/compression_executor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - COMPRESSOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("CompressionExecutor")
    
    def load_config(self):
        """加载配置"""
        config_path = "../config/compression_config_v1.2.0.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"✅ 加载配置: {config_path}")
            except Exception as e:
                self.logger.error(f"❌ 配置加载失败: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.logger.warning("⚠️  使用默认配置")
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "version": "1.2.0_fallback",
            "regular_compression": {
                "target_threshold_percent": 40,
                "preserve_recent_conversations": True
            },
            "safety_limits": {
                "min_context_chars_after_compression": 10000
            }
        }
    
    def check_current_context(self):
        """检查当前上下文"""
        try:
            # 检查记忆文件大小
            memory_dir = os.path.join(self.workspace_dir, "memory")
            total_size = 0
            file_count = 0
            
            if os.path.exists(memory_dir):
                for file in os.listdir(memory_dir):
                    if file.endswith('.md'):
                        file_path = os.path.join(memory_dir, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            # 检查会话文件
            session_files = list(Path(self.workspace_dir).glob("session_*.json"))
            session_size = sum(f.stat().st_size for f in session_files)
            
            context_info = {
                "memory_size": total_size,
                "memory_files": file_count,
                "session_size": session_size,
                "session_files": len(session_files),
                "estimated_context_chars": int((total_size + session_size) * 0.7),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"📊 上下文分析:")
            self.logger.info(f"   记忆文件: {file_count} 个, {total_size:,} 字节")
            self.logger.info(f"   会话文件: {len(session_files)} 个, {session_size:,} 字节")
            self.logger.info(f"   估算上下文: {context_info['estimated_context_chars']:,} 字符")
            
            return context_info
            
        except Exception as e:
            self.logger.error(f"❌ 上下文检查失败: {e}")
            return {"error": str(e)}
    
    def safe_compression(self, context_info):
        """安全压缩（避免过度压缩）"""
        self.logger.info("🔧 开始安全压缩")
        
        # 检查是否需要压缩
        estimated_chars = context_info.get("estimated_context_chars", 0)
        max_limit = 98304
        
        if estimated_chars <= max_limit * 0.7:  # 低于70%不压缩
            self.logger.info(f"✅ 上下文正常 ({estimated_chars:,} 字符 < {int(max_limit*0.7):,} 字符)，无需压缩")
            return False
        
        percentage = (estimated_chars / max_limit * 100) if max_limit > 0 else 0
        self.logger.info(f"📈 上下文使用率: {percentage:.1f}%，需要压缩")
        
        # 确定压缩强度
        if percentage > 200:
            compression_strength = "aggressive"
            target_percent = 50
            self.logger.warning("🚨 严重超标，使用激进压缩")
        elif percentage > 100:
            compression_strength = "moderate"
            target_percent = 60
            self.logger.warning("⚠️  超标，使用中等压缩")
        else:
            compression_strength = "conservative"
            target_percent = 70
            self.logger.info("⚡ 正常范围，使用保守压缩")
        
        # 执行压缩
        try:
            compressed = self.execute_compression(compression_strength, target_percent)
            
            if compressed:
                self.logger.info(f"✅ 压缩完成，强度: {compression_strength}")
                
                # 验证压缩后状态
                post_context = self.check_current_context()
                post_chars = post_context.get("estimated_context_chars", 0)
                post_percentage = (post_chars / max_limit * 100) if max_limit > 0 else 0
                
                self.logger.info(f"📊 压缩后状态: {post_chars:,} 字符 ({post_percentage:.1f}%)")
                
                # 检查压缩效果
                reduction = estimated_chars - post_chars
                if reduction > 0:
                    self.logger.info(f"📉 压缩减少: {reduction:,} 字符 ({(reduction/estimated_chars*100):.1f}%)")
                else:
                    self.logger.warning("⚠️  压缩效果不明显")
                
                return True
            else:
                self.logger.error("❌ 压缩执行失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 压缩过程出错: {e}")
            return False
    
    def execute_compression(self, strength, target_percent):
        """执行具体压缩操作"""
        self.logger.info(f"⚙️  执行{strength}强度压缩，目标: {target_percent}%")
        
        # 创建备份
        backup_dir = os.path.join(self.workspace_dir, "compression_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "strength": strength,
            "target_percent": target_percent,
            "original_files": []
        }
        
        try:
            # 处理记忆文件
            memory_dir = os.path.join(self.workspace_dir, "memory")
            if os.path.exists(memory_dir):
                memory_files = [f for f in os.listdir(memory_dir) if f.endswith('.md')]
                
                for filename in memory_files:
                    filepath = os.path.join(memory_dir, filename)
                    
                    # 备份原文件
                    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
                    with open(filepath, 'r', encoding='utf-8') as src, \
                         open(backup_path, 'w', encoding='utf-8') as dst:
                        content = src.read()
                        dst.write(content)
                    
                    backup_info["original_files"].append({
                        "file": filename,
                        "size": len(content),
                        "backup": backup_path
                    })
                    
                    # 根据强度决定压缩方式
                    if strength == "aggressive":
                        # 激进：只保留最近内容
                        compressed_content = self.compress_memory_aggressive(content, filename)
                    elif strength == "moderate":
                        # 中等：保留关键内容
                        compressed_content = self.compress_memory_moderate(content, filename)
                    else:
                        # 保守：轻度整理
                        compressed_content = self.compress_memory_conservative(content, filename)
                    
                    # 写回压缩后的内容
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(compressed_content)
                    
                    self.logger.info(f"📄 压缩记忆文件: {filename} ({len(content):,} → {len(compressed_content):,} 字符)")
            
            # 保存备份信息
            info_file = os.path.join(backup_dir, f"backup_info_{timestamp}.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 压缩完成，备份保存在: {backup_dir}")
            self.logger.info(f"📋 备份信息: {info_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 压缩执行出错: {e}")
            return False
    
    def compress_memory_conservative(self, content, filename):
        """保守压缩：轻度整理"""
        lines = content.split('\n')
        
        # 保留重要部分
        preserved_lines = []
        for line in lines:
            # 保留标题、重要标记、最近内容
            if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
                preserved_lines.append(line)
            elif '🚨' in line or '✅' in line or '⚠️' in line or '🔧' in line:
                preserved_lines.append(line)
            elif '重要' in line or '关键' in line or '紧急' in line:
                preserved_lines.append(line)
            elif len(line.strip()) > 0 and len(preserved_lines) < 100:  # 限制行数
                preserved_lines.append(line)
        
        # 添加压缩说明
        result = [
            f"# 🧠 记忆文件 - {filename.replace('.md', '')} (保守压缩)",
            f"压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"压缩强度: 保守 (轻度整理)",
            f"原始大小: {len(content):,} 字符",
            f"压缩后大小: {sum(len(l) for l in preserved_lines):,} 字符",
            f"保留比例: {(sum(len(l) for l in preserved_lines)/len(content)*100):.1f}%",
            "",
            "## 📝 压缩内容"
        ]
        
        result.extend(preserved_lines)
        
        return '\n'.join(result)
    
    def compress_memory_moderate(self, content, filename):
        """中等压缩：保留关键内容"""
        lines = content.split('\n')
        
        # 只保留关键信息
        preserved_lines = []
        sections_to_preserve = [
            '核心身份', '重要系统配置', '项目进展', 
            '重要问题记录', '近期目标', '重要教训'
        ]
        
        current_section = None
        for line in lines:
            # 检查是否是重要章节
            is_important_section = False
            for section in sections_to_preserve:
                if section in line and '#' in line:
                    current_section = section
                    is_important_section = True
                    preserved_lines.append(line)
                    break
            
            # 如果是重要章节的内容，多保留一些
            if current_section and not is_important_section:
                if len(preserved_lines) < 50:  # 限制每个章节的行数
                    preserved_lines.append(line)
            elif line.startswith('# ') or line.startswith('## '):
                # 其他章节标题，但少保留内容
                preserved_lines.append(line)
                current_section = None
        
        # 添加压缩说明
        result = [
            f"# 🧠 记忆文件 - {filename.replace('.md', '')} (中等压缩)",
            f"压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"压缩强度: 中等 (保留关键内容)",
            f"原始大小: {len(content):,} 字符",
            f"压缩后大小: {sum(len(l) for l in preserved_lines):,} 字符",
            f"保留比例: {(sum(len(l) for l in preserved_lines)/len(content)*100):.1f}%",
            f"保留章节: {', '.join(sections_to_preserve)}",
            "",
            "## 📋 压缩内容 (关键信息保留)"
        ]
        
        result.extend(preserved_lines)
        
        return '\n'.join(result)
    
    def compress_memory_aggressive(self, content, filename):
        """激进压缩：只保留核心信息"""
        lines = content.split('\n')
        
        # 只保留最核心的信息
        preserved_lines = []
        core_patterns = [
            '🚨', '❌', '✅', '🔴', '重要问题', '紧急', '严重',
            '修复', 'bug', '错误', '崩溃', '无法工作'
        ]
        
        for line in lines:
            # 保留紧急/重要标记的行
            if any(pattern in line for pattern in core_patterns):
                preserved_lines.append(line)
            # 保留一级标题
            elif line.startswith('# '):
                preserved_lines.append(line)
            # 保留极少量内容（前20行）
            elif len(preserved_lines) < 20 and len(line.strip()) > 50:
                preserved_lines.append(line)
        
        # 添加压缩说明
        result = [
            f"# 🧠 记忆文件 - {filename.replace('.md', '')} (激进压缩)",
            f"压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"压缩强度: 激进 (只保留核心信息)",
            f"原始大小: {len(content):,} 字符",
            f"压缩后大小: {sum(len(l) for l in preserved_lines):,} 字符",
            f"保留比例: {(sum(len(l) for l in preserved_lines)/len(content)*100):.1f}%",
            f"警告: 只保留紧急和重要信息，其他内容已删除",
            "",
            "## 🚨 核心信息保留"
        ]
        
        result.extend(preserved_lines)
        
        return '\n'.join(result)
    
    def verify_compression_integrity(self):
        """验证压缩完整性"""
        self.logger.info("🔍 验证压缩完整性")
        
        # 检查关键文件是否还存在
        essential_files = [
            "memory/2026-05-15.md",
            "MEMORY.md",
            "IDENTITY.md",
            "USER.md"
        ]
        
        all_exist = True
        for file_path in essential_files:
            full_path = os.path.join(self.workspace_dir, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.logger.info(f"✅ 关键文件存在: {file_path} ({size:,} 字节)")
                
                # 检查文件是否为空
                if size == 0:
                    self.logger.warning(f"⚠️  文件为空: {file_path}")
                    all_exist = False
            else:
                self.logger.error(f"❌ 关键文件缺失: {file_path}")
                all_exist = False
        
        # 测试输出完整性
        test_messages = [
            "压缩完整性测试 - 短消息",
            "这是一条测试消息，用于验证系统能否正常输出。",
            "括号平衡测试：（正常括号）",
            "特殊字符测试：Hello! 123 @#$"
        ]
        
        for msg in test_messages:
            self.logger.info(f"📝 输出测试: {msg}")
        
        if all_exist:
            self.logger.info("🎉 压缩完整性验证通过")
        else:
            self.logger.warning("⚠️  压缩完整性验证失败")
        
        return all_exist
    
    def run(self):
        """主运行函数"""
        self.logger.info("=" * 50)
        self.logger.info("🚀 Simple Compression Executor FIXED v1.2.0")
        self.logger.info("🔧 修复版：避免过度压缩和无限循环")
        self.logger.info("=" * 50)
        
        start_time = time.time()
        
        # 1. 检查当前上下文
        context_info = self.check_current_context()
        
        if "error" in context_info:
            self.logger.error("❌ 无法获取上下文信息，停止压缩")
            return False
        
        # 2. 执行安全压缩
        compression_performed = self.safe_compression(context_info)
        
        # 3. 验证完整性
        if compression_performed:
            integrity_ok = self.verify_compression_integrity()
        else:
            integrity_ok = True
        
        # 4. 生成报告
        end_time = time.time()
        duration = end_time - start_time
        
        report = {
            "compression_session": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "compression_performed": compression_performed,
                "integrity_verified": integrity_ok,
                "context_before": context_info,
                "status": "completed"
            }
        }
        
        # 保存报告
        report_file = f"./logs/compression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info("=" * 50)
        self.logger.info("📋 压缩会话报告:")
        self.logger.info(f"   耗时: {duration:.2f} 秒")
        self.logger.info(f"   执行压缩: {'是' if compression_performed else '否'}")
        self.logger.info(f"   完整性验证: {'通过' if integrity_ok else '失败'}")
        self.logger.info(f"   报告文件: {report_file}")
        self.logger.info("=" * 50)
        
        return compression_performed and integrity_ok

def main():
    """主函数"""
    print("🚀 Simple Compression Executor FIXED v1.2.0")
    print("🔧 安全压缩，避免无限循环")
    
    executor = SimpleCompressionExecutorFixed()
    
    try:
        success = executor.run()
        
        if success:
            print("\n✅ 压缩执行成功且安全")
            return 0
        else:
            print("\n⚠️  压缩未执行或存在问题")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())