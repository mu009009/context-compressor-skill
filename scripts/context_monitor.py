#!/usr/bin/env python3
# 🗜️ 上下文监控器
# 监控OpenClaw上下文长度，检测溢出风险

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

class ContextMonitor:
    """上下文监控器 - 实时监控上下文长度和溢出风险"""
    
    def __init__(self, config_path=None, debug=False):
        """初始化监控器
        
        Args:
            config_path: 配置文件路径
            debug: 调试模式
        """
        self.debug = debug
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # 计算触发长度
        self.max_length = self.config.get("compression", {}).get("max_context_length", 98304)
        self.threshold_percent = self.config.get("compression", {}).get("threshold_percent", 70)
        self.trigger_length = int(self.max_length * self.threshold_percent / 100)
        
        # 状态变量
        self.last_check_time = None
        self.compression_count = 0
        self.last_compression_time = None
        
        if debug:
            logging.info(f"上下文监控器初始化完成")
            logging.info(f"最大长度: {self.max_length}, 阈值: {self.threshold_percent}%")
            logging.info(f"触发长度: {self.trigger_length}")
    
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
            "compression": {
                "threshold_percent": 70,
                "max_context_length": 98304,
                "check_frequency_messages": 10,
                "min_interval_minutes": 30
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
    
    def estimate_context_length(self, method="simulation"):
        """估计当前上下文长度
        
        Args:
            method: 估计方法 (simulation, log_analysis, api_call)
        
        Returns:
            int: 估计的上下文长度
        """
        if method == "simulation":
            # 模拟方法 - 基于当前时间生成伪随机长度
            # 在实际使用中应该替换为真实的上下文长度获取
            import random
            base_length = 50000
            time_variation = int(time.time() % 10000)
            random_variation = random.randint(-10000, 10000)
            return base_length + time_variation + random_variation
        
        elif method == "log_analysis":
            # 分析OpenClaw日志获取上下文信息
            # 这里需要实际集成OpenClaw的日志分析
            return self._analyze_openclaw_logs()
        
        elif method == "api_call":
            # 通过API调用获取上下文信息
            # 这里需要OpenClaw提供相关API
            return self._get_context_via_api()
        
        else:
            self.logger.warning(f"未知的估计方法: {method}, 使用模拟方法")
            return self.estimate_context_length("simulation")
    
    def _analyze_openclaw_logs(self):
        """分析OpenClaw日志获取上下文信息"""
        # 这里需要实际实现日志分析逻辑
        # 暂时返回模拟值
        return 60000
    
    def _get_context_via_api(self):
        """通过API获取上下文信息"""
        # 这里需要实际实现API调用逻辑
        # 暂时返回模拟值
        return 55000
    
    def check_context_status(self):
        """检查上下文状态
        
        Returns:
            dict: 状态信息
        """
        current_length = self.estimate_context_length()
        usage_percent = (current_length / self.max_length) * 100
        
        status = {
            "current_length": current_length,
            "max_length": self.max_length,
            "usage_percent": round(usage_percent, 2),
            "trigger_length": self.trigger_length,
            "threshold_percent": self.threshold_percent,
            "needs_compression": current_length >= self.trigger_length,
            "is_critical": usage_percent >= 90,
            "needs_warning": usage_percent >= 65,
            "last_check_time": datetime.now().isoformat(),
            "compression_count": self.compression_count
        }
        
        self.last_check_time = datetime.now()
        
        # 记录状态
        if status["needs_compression"]:
            self.logger.warning(f"上下文需要压缩: {usage_percent:.1f}% 使用率")
        elif status["needs_warning"]:
            self.logger.info(f"上下文接近阈值: {usage_percent:.1f}% 使用率")
        
        return status
    
    def needs_compression(self):
        """检查是否需要压缩
        
        Returns:
            bool: 是否需要压缩
        """
        status = self.check_context_status()
        return status["needs_compression"]
    
    def get_detailed_report(self):
        """获取详细报告"""
        status = self.check_context_status()
        
        report = {
            "监控状态": {
                "当前长度": f"{status['current_length']:,} 字符",
                "最大限制": f"{status['max_length']:,} 字符",
                "使用率": f"{status['usage_percent']}%",
                "触发阈值": f"{status['threshold_percent']}% ({status['trigger_length']:,} 字符)",
                "需要压缩": "是" if status["needs_compression"] else "否",
                "临界状态": "是" if status["is_critical"] else "否"
            },
            "系统信息": {
                "检查时间": status["last_check_time"],
                "压缩次数": status["compression_count"],
                "上次压缩": self.last_compression_time or "从未",
                "调试模式": "开启" if self.debug else "关闭"
            },
            "建议操作": self._get_recommendations(status)
        }
        
        return report
    
    def _get_recommendations(self, status):
        """根据状态获取建议"""
        recommendations = []
        
        if status["is_critical"]:
            recommendations.append("🚨 **立即执行压缩** - 上下文使用率超过90%，随时可能溢出")
            recommendations.append("⚠️ **减少对话内容** - 暂时避免长回复或详细解释")
            recommendations.append("🔧 **检查配置** - 确认阈值设置是否合理")
        
        elif status["needs_compression"]:
            recommendations.append("⚠️ **建议执行压缩** - 上下文使用率超过阈值")
            recommendations.append("📝 **总结关键信息** - 压缩前确认重要内容")
            recommendations.append("⏰ **安排压缩时间** - 选择合适时间执行压缩")
        
        elif status["needs_warning"]:
            recommendations.append("📊 **监控上下文** - 使用率超过65%，接近阈值")
            recommendations.append("🗑️ **清理冗余** - 删除不必要的问候和确认")
            recommendations.append("🔍 **准备压缩** - 系统可能很快需要压缩")
        
        else:
            recommendations.append("✅ **状态正常** - 上下文使用率在安全范围内")
            recommendations.append("📈 **继续监控** - 定期检查上下文状态")
            recommendations.append("🎯 **保持良好习惯** - 避免不必要的长对话")
        
        return recommendations
    
    def record_compression(self, compression_result):
        """记录压缩操作
        
        Args:
            compression_result: 压缩结果字典
        """
        self.compression_count += 1
        self.last_compression_time = datetime.now().isoformat()
        
        # 记录到日志
        self.logger.info(f"压缩操作记录: 第{self.compression_count}次压缩")
        self.logger.info(f"压缩结果: {compression_result}")
        
        # 保存到文件
        self._save_compression_record(compression_result)
    
    def _save_compression_record(self, compression_result):
        """保存压缩记录到文件"""
        record_dir = Path("logs/compression_records")
        record_dir.mkdir(parents=True, exist_ok=True)
        
        record_file = record_dir / f"compression_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "compression_number": self.compression_count,
            "result": compression_result,
            "monitor_status": self.check_context_status()
        }
        
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"压缩记录保存到: {record_file}")
        except Exception as e:
            self.logger.error(f"保存压缩记录失败: {e}")

# 命令行接口
def main():
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="上下文监控器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--check", action="store_true", help="检查上下文状态")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    parser.add_argument("--estimate", action="store_true", help="估计上下文长度")
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = ContextMonitor(config_path=args.config, debug=args.debug)
    
    if args.estimate:
        length = monitor.estimate_context_length()
        print(f"估计上下文长度: {length:,} 字符")
    
    if args.check:
        status = monitor.check_context_status()
        print(f"上下文状态:")
        print(f"  当前长度: {status['current_length']:,} 字符")
        print(f"  使用率: {status['usage_percent']}%")
        print(f"  需要压缩: {'是' if status['needs_compression'] else '否'}")
    
    if args.report:
        report = monitor.get_detailed_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.check, args.report, args.estimate]):
        parser.print_help()

if __name__ == "__main__":
    main()