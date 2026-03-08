#!/usr/bin/env python3
# 📝 压缩日志记录器
# 记录和管理所有压缩操作的日志

import json
import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

class CompressionLogger:
    """压缩日志记录器 - 管理压缩操作日志"""
    
    def __init__(self, config_path=None, debug=False):
        """初始化日志记录器
        
        Args:
            config_path: 配置文件路径
            debug: 调试模式
        """
        self.debug = debug
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # 日志目录
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 日志文件
        self.log_file = self.log_dir / "compression.log"
        self.stats_file = self.log_dir / "compression_stats.json"
        self.csv_file = self.log_dir / "compression_history.csv"
        
        # 初始化统计
        self.stats = self._load_stats()
        
        if debug:
            logging.info(f"压缩日志记录器初始化完成")
            logging.info(f"日志目录: {self.log_dir.absolute()}")
    
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
            "monitoring": {
                "log_level": "INFO",
                "log_retention_days": 30
            }
        }
    
    def setup_logging(self):
        """设置日志"""
        log_level = self.config.get("monitoring", {}).get("log_level", "INFO")
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler() if self.debug else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_stats(self):
        """加载统计信息"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载统计信息失败: {e}")
        
        # 默认统计信息
        return {
            "total_compressions": 0,
            "total_chars_saved": 0,
            "average_compression_rate": 0,
            "successful_compressions": 0,
            "failed_compressions": 0,
            "first_compression": None,
            "last_compression": None,
            "daily_stats": {},
            "compression_by_strength": {
                "light": 0,
                "standard": 0,
                "aggressive": 0
            }
        }
    
    def _save_stats(self):
        """保存统计信息"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存统计信息失败: {e}")
    
    def log_compression(self, compression_result: Dict[str, Any]):
        """记录压缩操作
        
        Args:
            compression_result: 压缩结果字典
        """
        timestamp = datetime.now()
        timestamp_str = timestamp.isoformat()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        # 更新统计
        self._update_stats(compression_result, timestamp)
        
        # 记录到日志文件
        self._log_to_file(compression_result, timestamp_str)
        
        # 记录到CSV
        self._log_to_csv(compression_result, timestamp_str)
        
        # 更新每日统计
        self._update_daily_stats(compression_result, date_str)
        
        self.logger.info(f"压缩操作已记录: {compression_result.get('compression_rate', 0)}%")
    
    def _update_stats(self, result, timestamp):
        """更新统计数据"""
        self.stats["total_compressions"] += 1
        
        if result.get("success", False):
            self.stats["successful_compressions"] += 1
            
            # 计算保存的字符数
            original = result.get("original_length", 0)
            compressed = result.get("compressed_length", 0)
            chars_saved = original - compressed
            self.stats["total_chars_saved"] += chars_saved
            
            # 更新平均压缩率
            current_rate = result.get("compression_rate", 0) / 100
            total = self.stats["successful_compressions"]
            old_avg = self.stats["average_compression_rate"]
            new_avg = ((old_avg * (total - 1)) + current_rate) / total
            self.stats["average_compression_rate"] = new_avg
            
            # 更新压缩强度统计
            strength = result.get("compression_strength", "standard")
            if strength in self.stats["compression_by_strength"]:
                self.stats["compression_by_strength"][strength] += 1
        else:
            self.stats["failed_compressions"] += 1
        
        # 更新时间记录
        if self.stats["first_compression"] is None:
            self.stats["first_compression"] = timestamp.isoformat()
        self.stats["last_compression"] = timestamp.isoformat()
        
        # 保存统计
        self._save_stats()
    
    def _log_to_file(self, result, timestamp):
        """记录到日志文件"""
        log_entry = {
            "timestamp": timestamp,
            "type": "compression",
            "result": result
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"写入日志文件失败: {e}")
    
    def _log_to_csv(self, result, timestamp):
        """记录到CSV文件"""
        csv_exists = self.csv_file.exists()
        
        try:
            with open(self.csv_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # 写入表头（如果文件不存在）
                if not csv_exists:
                    header = [
                        "timestamp", "success", "original_length", "compressed_length",
                        "compression_rate", "compression_strength", "execution_time",
                        "preserved_keywords", "technical_terms", "decisions"
                    ]
                    writer.writerow(header)
                
                # 写入数据行
                preserved_info = result.get("preserved_key_info", {})
                row = [
                    timestamp,
                    result.get("success", False),
                    result.get("original_length", 0),
                    result.get("compressed_length", 0),
                    result.get("compression_rate", 0),
                    result.get("compression_strength", "standard"),
                    result.get("execution_time", 0),
                    len(preserved_info.get("important_keywords", [])),
                    len(preserved_info.get("technical_terms", [])),
                    len(preserved_info.get("decisions", []))
                ]
                writer.writerow(row)
                
        except Exception as e:
            self.logger.error(f"写入CSV文件失败: {e}")
    
    def _update_daily_stats(self, result, date_str):
        """更新每日统计"""
        if date_str not in self.stats["daily_stats"]:
            self.stats["daily_stats"][date_str] = {
                "compressions": 0,
                "successful": 0,
                "failed": 0,
                "chars_saved": 0,
                "avg_rate": 0
            }
        
        daily = self.stats["daily_stats"][date_str]
        daily["compressions"] += 1
        
        if result.get("success", False):
            daily["successful"] += 1
            
            # 计算保存的字符数
            original = result.get("original_length", 0)
            compressed = result.get("compressed_length", 0)
            chars_saved = original - compressed
            daily["chars_saved"] += chars_saved
            
            # 更新平均压缩率
            current_rate = result.get("compression_rate", 0)
            successful = daily["successful"]
            old_avg = daily["avg_rate"]
            new_avg = ((old_avg * (successful - 1)) + current_rate) / successful
            daily["avg_rate"] = new_avg
        else:
            daily["failed"] += 1
        
        self._save_stats()
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的日志记录
        
        Args:
            limit: 返回的记录数量
        
        Returns:
            List[Dict]: 日志记录列表
        """
        logs = []
        
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 读取最后limit行
                for line in lines[-limit:]:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
        
        return logs
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = self.stats.copy()
        
        # 计算额外统计
        if stats["total_compressions"] > 0:
            stats["success_rate"] = (stats["successful_compressions"] / stats["total_compressions"]) * 100
        else:
            stats["success_rate"] = 0
        
        # 计算平均每次保存的字符数
        if stats["successful_compressions"] > 0:
            stats["avg_chars_saved_per_compression"] = stats["total_chars_saved"] / stats["successful_compressions"]
        else:
            stats["avg_chars_saved_per_compression"] = 0
        
        # 格式化统计信息
        formatted_stats = {
            "总体统计": {
                "总压缩次数": stats["total_compressions"],
                "成功次数": stats["successful_compressions"],
                "失败次数": stats["failed_compressions"],
                "成功率": f"{stats['success_rate']:.1f}%",
                "总节省字符数": f"{stats['total_chars_saved']:,}",
                "平均每次节省": f"{stats['avg_chars_saved_per_compression']:.0f} 字符",
                "平均压缩率": f"{stats['average_compression_rate']*100:.1f}%",
                "首次压缩": stats["first_compression"] or "从未",
                "最后压缩": stats["last_compression"] or "从未"
            },
            "压缩强度分布": stats["compression_by_strength"],
            "每日统计": stats["daily_stats"]
        }
        
        return formatted_stats
    
    def cleanup_old_logs(self, retention_days: Optional[int] = None):
        """清理旧的日志记录
        
        Args:
            retention_days: 保留天数（如果为None则使用配置）
        """
        if retention_days is None:
            retention_days = self.config.get("monitoring", {}).get("log_retention_days", 30)
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
        
        # 清理每日统计
        daily_stats = self.stats["daily_stats"]
        old_dates = [date for date in daily_stats if date < cutoff_date_str]
        
        for date in old_dates:
            del daily_stats[date]
            self.logger.info(f"清理旧统计: {date}")
        
        self._save_stats()
        self.logger.info(f"已清理{len(old_dates)}天的旧统计")
    
    def generate_report(self, format: str = "text") -> str:
        """生成报告
        
        Args:
            format: 报告格式 (text, markdown, json)
        
        Returns:
            str: 生成的报告
        """
        stats = self.get_statistics()
        recent_logs = self.get_recent_logs(5)
        
        if format == "json":
            report = {
                "statistics": stats,
                "recent_logs": recent_logs
            }
            return json.dumps(report, ensure_ascii=False, indent=2)
        
        elif format == "markdown":
            report_lines = []
            report_lines.append("# 🗜️ 上下文压缩系统报告")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # 总体统计
            report_lines.append("## 📊 总体统计")
            overall = stats["总体统计"]
            for key, value in overall.items():
                report_lines.append(f"- **{key}**: {value}")
            report_lines.append("")
            
            # 压缩强度分布
            report_lines.append("## 🎯 压缩强度分布")
            strength_dist = stats["压缩强度分布"]
            for strength, count in strength_dist.items():
                report_lines.append(f"- **{strength}**: {count}次")
            report_lines.append("")
            
            # 最近压缩
            report_lines.append("## 📝 最近5次压缩")
            for i, log in enumerate(recent_logs, 1):
                result = log.get("result", {})
                report_lines.append(f"### #{i} {log.get('timestamp', '')}")
                report_lines.append(f"- 压缩率: {result.get('compression_rate', 0)}%")
                report_lines.append(f"- 强度: {result.get('compression_strength', 'standard')}")
                report_lines.append(f"- 执行时间: {result.get('execution_time', 0):.2f}秒")
                report_lines.append("")
            
            return "\n".join(report_lines)
        
        else:  # text格式
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("🗜️ 上下文压缩系统报告")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("=" * 60)
            report_lines.append("")
            
            # 总体统计
            report_lines.append("📊 总体统计")
            report_lines.append("-" * 40)
            overall = stats["总体统计"]
            for key, value in overall.items():
                report_lines.append(f"  {key}: {value}")
            report_lines.append("")
            
            # 压缩强度分布
            report_lines.append("🎯 压缩强度分布")
            report_lines.append("-" * 40)
            strength_dist = stats["压缩强度分布"]
            for strength, count in strength_dist.items():
                report_lines.append(f"  {strength}: {count}次")
            report_lines.append("")
            
            # 最近压缩
            report_lines.append("📝 最近5次压缩")
            report_lines.append("-" * 40)
            for i, log in enumerate(recent_logs, 1):
                result = log.get("result", {})
                report_lines.append(f"  #{i} {log.get('timestamp', '')}")
                report_lines.append(f"    压缩率: {result.get('compression_rate', 0)}%")
                report_lines.append(f"    强度: {result.get('compression_strength', 'standard')}")
                report_lines.append("")
            
            return "\n".join(report_lines)

# 命令行接口
def main():
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="压缩日志记录器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--logs", type=int, help="显示最近的日志记录", nargs='?', const=10)
    parser.add_argument("--report", action="store_true", help="生成报告")
    parser.add_argument("--format", choices=["text", "markdown", "json"], 
                       default="text", help="报告格式")
    parser.add_argument("--cleanup", action="store_true", help="清理旧日志")
    parser.add_argument("--days", type=int, default=30, help="清理保留天数")
    
    args = parser.parse_args()
    
    # 创建日志记录器
    logger = CompressionLogger(config_path=args.config, debug=args.debug)
    
    if args.stats:
        stats = logger.get_statistics()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    if args.logs is not None:
        logs = logger.get_recent_logs(args.logs)
        print(json.dumps(logs, ensure_ascii=False, indent=2))
    
    if args.report:
        report = logger.generate_report(args.format)
        print(report)
    
    if args.cleanup:
        logger.cleanup_old_logs(args.days)
        print(f"已清理超过{args.days}天的旧日志")
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.stats, args.logs is not None, args.report, args.cleanup]):
        parser.print_help()

if __name__ == "__main__":
    main()