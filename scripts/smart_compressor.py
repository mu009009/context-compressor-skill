#!/usr/bin/env python3
# 🗜️ 智能压缩器
# 执行上下文智能压缩，保留关键信息，删除冗余内容

import json
import re
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class SmartCompressor:
    """智能压缩器 - 执行上下文智能压缩"""
    
    def __init__(self, config_path=None, debug=False):
        """初始化压缩器
        
        Args:
            config_path: 配置文件路径
            debug: 调试模式
        """
        self.debug = debug
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # 加载压缩策略
        self.strategy = self.config.get("strategy", {})
        self.preservation_rules = self.strategy.get("preservation_rules", {})
        self.compression_rules = self.strategy.get("compression_rules", {})
        
        # 性能指标
        self.metrics = {
            "total_compressions": 0,
            "total_chars_compressed": 0,
            "average_compression_rate": 0,
            "last_compression_time": None
        }
        
        if debug:
            logging.info(f"智能压缩器初始化完成")
            logging.info(f"压缩策略: {self.strategy.get('algorithm', 'smart_compression')}")
    
    def _load_config(self, config_path):
        """加载配置文件"""
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent / "config" / "compression_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"配置文件不存在: {config_path}, 使用默认配置")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logging.error(f"配置文件格式错误: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "strategy": {
                "algorithm": "smart_compression",
                "compression_ratio_target": 0.6,
                "preservation_rules": {
                    "preserve_keywords": ["指令", "决策", "重要", "项目"],
                    "preserve_patterns": ["^## ", "^### "]
                },
                "compression_rules": {
                    "compress_keywords": ["你好", "谢谢", "明白了"]
                }
            }
        }
    
    def setup_logging(self):
        """设置日志"""
        log_level = self.config.get("monitoring", {}).get("log_level", "INFO")
        log_file = self.config.get("monitoring", {}).get("log_file", "logs/compression.log")
        
        # 创建日志目录
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler() if self.debug else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def compress(self, context_data=None, strength="standard"):
        """执行上下文压缩
        
        Args:
            context_data: 上下文数据 (如果为None则模拟)
            strength: 压缩强度 (light, standard, aggressive)
        
        Returns:
            dict: 压缩结果
        """
        self.logger.info(f"开始执行压缩，强度: {strength}")
        start_time = datetime.now()
        
        # 获取或模拟上下文数据
        if context_data is None:
            original_context = self._simulate_context()
            original_length = len(original_context)
        else:
            original_context = context_data
            original_length = len(str(context_data))
        
        # 执行压缩算法
        compressed_context = self._apply_compression_algorithm(original_context, strength)
        compressed_length = len(compressed_context)
        
        # 计算压缩率
        if original_length > 0:
            compression_rate = 1 - (compressed_length / original_length)
        else:
            compression_rate = 0
        
        # 更新指标
        self._update_metrics(original_length, compressed_length, compression_rate)
        
        # 准备结果
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "original_length": original_length,
            "compressed_length": compressed_length,
            "compression_rate": round(compression_rate * 100, 2),
            "compression_strength": strength,
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "preserved_key_info": self._check_preserved_info(original_context, compressed_context),
            "compressed_context_preview": self._get_preview(compressed_context, 200),
            "metrics": self.metrics.copy()
        }
        
        self.logger.info(f"压缩完成: {result['compression_rate']}% 压缩率")
        return result
    
    def _simulate_context(self):
        """模拟上下文数据（用于测试）"""
        # 模拟一个包含各种类型内容的对话上下文
        context_parts = []
        
        # 重要信息（应该保留）
        context_parts.append("## 重要项目决策")
        context_parts.append("我们决定使用Python 3.11作为主要开发语言。")
        context_parts.append("数据库选择PostgreSQL，版本14。")
        context_parts.append("API密钥需要妥善保管，不要提交到Git。")
        
        # 技术讨论（应该保留）
        context_parts.append("## 技术问题讨论")
        context_parts.append("遇到一个上下文溢出错误：Input length exceeds the maximum length 98304。")
        context_parts.append("解决方案：实现自动压缩机制，阈值70%。")
        context_parts.append("压缩算法需要保留关键指令和决策。")
        
        # 日常问候（可以压缩）
        for _ in range(3):
            context_parts.append("你好！今天过得怎么样？")
            context_parts.append("谢谢！我明白了。")
            context_parts.append("哈哈，这个确实有趣。")
        
        # 重复确认（可以压缩）
        for _ in range(2):
            context_parts.append("好的，我收到了。")
            context_parts.append("明白了，我会处理的。")
            context_parts.append("确认，任务已完成。")
        
        # 更多重要信息
        context_parts.append("## 安全注意事项")
        context_parts.append("GitHub token需要定期轮换，不要使用永久token。")
        context_parts.append("生产环境数据库密码必须加密存储。")
        context_parts.append("API访问需要添加速率限制。")
        
        return "\n".join(context_parts)
    
    def _apply_compression_algorithm(self, context, strength):
        """应用压缩算法
        
        Args:
            context: 原始上下文
            strength: 压缩强度
        
        Returns:
            str: 压缩后的上下文
        """
        lines = context.split('\n')
        preserved_lines = []
        compression_level = self._get_compression_level(strength)
        
        for line in lines:
            # 检查是否应该保留
            if self._should_preserve(line):
                preserved_lines.append(line)
            
            # 检查是否应该压缩（删除或简化）
            elif self._should_compress(line, compression_level):
                # 根据压缩强度决定处理方式
                if strength == "aggressive":
                    # 重度压缩：直接删除
                    continue
                elif strength == "standard":
                    # 标准压缩：简化或合并
                    simplified = self._simplify_line(line)
                    if simplified:
                        preserved_lines.append(simplified)
                else:
                    # 轻度压缩：基本保留，只删除明显冗余
                    preserved_lines.append(line)
            
            else:
                # 其他内容：根据强度决定
                if random.random() < compression_level:
                    preserved_lines.append(line)
        
        # 应用后处理
        compressed_context = self._post_process('\n'.join(preserved_lines), strength)
        return compressed_context
    
    def _get_compression_level(self, strength):
        """获取压缩级别"""
        levels = {
            "light": 0.3,      # 轻度：30%压缩
            "standard": 0.5,   # 标准：50%压缩
            "aggressive": 0.7  # 重度：70%压缩
        }
        return levels.get(strength, 0.5)
    
    def _should_preserve(self, line):
        """检查是否应该保留该行"""
        line_lower = line.lower()
        
        # 检查保留关键词
        preserve_keywords = self.preservation_rules.get("preserve_keywords", [])
        for keyword in preserve_keywords:
            if keyword in line:
                return True
        
        # 检查保留模式
        preserve_patterns = self.preservation_rules.get("preserve_patterns", [])
        for pattern in preserve_patterns:
            if re.match(pattern, line):
                return True
        
        # 检查重要句子
        preserve_sentences = self.preservation_rules.get("preserve_sentences_with", [])
        for word in preserve_sentences:
            if word in line:
                return True
        
        # 标题行通常保留
        if line.startswith('#') and len(line.strip()) > 2:
            return True
        
        # 列表项通常保留
        if line.strip().startswith(('* ', '- ', '• ', '1.', '2.', '3.')):
            return True
        
        return False
    
    def _should_compress(self, line, compression_level):
        """检查是否应该压缩该行"""
        line_lower = line.lower()
        
        # 检查压缩关键词
        compress_keywords = self.compression_rules.get("compress_keywords", [])
        for keyword in compress_keywords:
            if keyword in line_lower:
                return True
        
        # 检查压缩模式
        compress_patterns = self.compression_rules.get("compress_patterns", [])
        for pattern in compress_patterns:
            if re.search(pattern, line_lower):
                return True
        
        # 纯表情或短回复
        if len(line.strip()) < 5 and any(c in line for c in '😀😊😂😍😎😭😤😡🤔😴'):
            return True
        
        # 简单确认
        simple_confirms = ['ok', '好的', '收到', '明白', '了解', '是的', '对的']
        if line_lower.strip() in simple_confirms:
            return True
        
        # 基于压缩级别的随机压缩
        if random.random() < compression_level * 0.5:
            return True
        
        return False
    
    def _simplify_line(self, line):
        """简化一行内容"""
        # 移除多余的空格
        line = ' '.join(line.split())
        
        # 简化常见表达
        simplifications = {
            r'非常+': '很',
            r'真的+': '确实',
            r'特别+': '很',
            r'十分+': '很',
            r'超级+': '很',
            r'哈哈哈+': '哈哈',
            r'呵呵呵+': '呵呵',
            r'嘿嘿嘿+': '嘿嘿'
        }
        
        for pattern, replacement in simplifications.items():
            line = re.sub(pattern, replacement, line)
        
        return line if len(line) > 3 else None
    
    def _post_process(self, context, strength):
        """后处理压缩后的上下文"""
        lines = context.split('\n')
        processed_lines = []
        
        # 移除空行（根据强度）
        max_empty_lines = {
            "light": 2,
            "standard": 1,
            "aggressive": 0
        }.get(strength, 1)
        
        empty_count = 0
        for line in lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= max_empty_lines:
                    processed_lines.append(line)
            else:
                empty_count = 0
                processed_lines.append(line)
        
        # 添加压缩标记
        if strength != "light":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            compression_note = f"\n\n[🗜️ 上下文已压缩 - {strength}模式 - {timestamp}]"
            processed_lines.append(compression_note)
        
        return '\n'.join(processed_lines)
    
    def _update_metrics(self, original_length, compressed_length, compression_rate):
        """更新性能指标"""
        self.metrics["total_compressions"] += 1
        self.metrics["total_chars_compressed"] += (original_length - compressed_length)
        
        # 更新平均压缩率
        total_comps = self.metrics["total_compressions"]
        old_avg = self.metrics["average_compression_rate"]
        new_avg = ((old_avg * (total_comps - 1)) + compression_rate) / total_comps
        self.metrics["average_compression_rate"] = new_avg
        
        self.metrics["last_compression_time"] = datetime.now().isoformat()
    
    def _check_preserved_info(self, original, compressed):
        """检查保留的关键信息"""
        preserved_info = {
            "important_keywords": [],
            "technical_terms": [],
            "decisions": [],
            "total_preserved": 0
        }
        
        # 检查重要关键词
        important_keywords = self.preservation_rules.get("preserve_keywords", [])
        for keyword in important_keywords:
            if keyword in original and keyword in compressed:
                preserved_info["important_keywords"].append(keyword)
        
        # 检查技术术语（简单实现）
        tech_terms = ["API", "数据库", "服务器", "配置", "错误", "修复", "部署"]
        for term in tech_terms:
            if term in original and term in compressed:
                preserved_info["technical_terms"].append(term)
        
        # 检查决策（通过模式匹配）
        decision_patterns = [r'决定[：:]', r'选择[：:]', r'方案[：:]', r'应该']
        for pattern in decision_patterns:
            if re.search(pattern, original) and re.search(pattern, compressed):
                preserved_info["decisions"].append(pattern)
        
        preserved_info["total_preserved"] = len(preserved_info["important_keywords"]) + \
                                           len(preserved_info["technical_terms"]) + \
                                           len(preserved_info["decisions"])
        
        return preserved_info
    
    def _get_preview(self, context, max_length=200):
        """获取上下文预览"""
        if len(context) <= max_length:
            return context
        
        # 尝试获取开头和结尾
        preview = context[:max_length//2] + "\n...\n" + context[-max_length//2:]
        return preview
    
    def get_compression_report(self):
        """获取压缩报告"""
        return {
            "压缩器状态": {
                "总压缩次数": self.metrics["total_compressions"],
                "总压缩字符数": f"{self.metrics['total_chars_compressed']:,}",
                "平均压缩率": f"{self.metrics['average_compression_rate']*100:.1f}%",
                "最后压缩时间": self.metrics["last_compression_time"] or "从未",
                "当前策略": self.strategy.get("algorithm", "smart_compression")
            },
            "配置信息": {
                "保留关键词": len(self.preservation_rules.get("preserve_keywords", [])),
                "压缩关键词": len(self.compression_rules.get("compress_keywords", [])),
                "目标压缩率": f"{self.strategy.get('compression_ratio_target', 0.6)*100:.0f}%",
                "最小保留率": f"{self.strategy.get('min_content_preserved', 0.8)*100:.0f}%"
            }
        }

# 命令行接口
def main():
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能压缩器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--strength", choices=["light", "standard", "aggressive"], 
                       default="standard", help="压缩强度")
    parser.add_argument("--test", action="store_true", help="测试压缩")
    parser.add_argument("--report", action="store_true", help="显示压缩报告")
    
    args = parser.parse_args()
    
    # 创建压缩器
    compressor = SmartCompressor(config_path=args.config, debug=args.debug)
    
    if args.test:
        print(f"测试{args.strength}强度压缩...")
        result = compressor.compress(strength=args.strength)
        
        print(f"压缩结果:")
        print(f"  原始长度: {result['original_length']:,} 字符")
        print(f"  压缩后长度: {result['compressed_length']:,} 字符")
        print(f"  压缩率: {result['compression_rate']}%")
        print(f"  执行时间: {result['execution_time']:.2f}秒")
        print(f"  保留关键信息: {result['preserved_key_info']['total_preserved']}项")
        
        print(f"\n压缩预览:")
        print("-" * 50)
        print(result['compressed_context_preview'])
        print("-" * 50)
    
    if args.report:
        report = compressor.get_compression_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.test, args.report]):
        parser.print_help()

if __name__ == "__main__":
    main()