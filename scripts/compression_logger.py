#!/usr/bin/env python3
"""
压缩日志记录器
记录上下文压缩操作和效果
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

class CompressionLogger:
    """压缩日志记录器"""
    
    def __init__(self, log_dir="./logs"):
        """初始化日志记录器"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志配置
        self.setup_logging()
        
        # 日志文件路径
        self.log_file = self.log_dir / f"compression_log_{datetime.now().strftime('%Y%m%d')}.json"
        self.event_log = self.log_dir / f"compression_events_{datetime.now().strftime('%Y%m%d')}.log"
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "compression_system.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_compression_event(self, event_type, data):
        """记录压缩事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # 写入JSON日志
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"写入JSON日志失败: {e}")
        
        # 写入文本日志
        try:
            with open(self.event_log, 'a', encoding='utf-8') as f:
                f.write(f"{event['timestamp']} [{event_type}] {json.dumps(data, ensure_ascii=False)}\n")
        except Exception as e:
            self.logger.error(f"写入文本日志失败: {e}")
        
        # 输出到控制台
        self.logger.info(f"[{event_type}] {json.dumps(data, ensure_ascii=False)}")
        
        return event
    
    def log_context_overflow(self, context_length, max_length, error_id):
        """记录上下文超限事件"""
        data = {
            "context_length": context_length,
            "max_length": max_length,
            "usage_percentage": round((context_length / max_length) * 100, 2),
            "error_id": error_id,
            "status": "overflow"
        }
        return self.log_compression_event("CONTEXT_OVERFLOW", data)
    
    def log_compression_start(self, trigger, attempt, max_attempts):
        """记录压缩开始事件"""
        data = {
            "trigger": trigger,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "start_time": datetime.now().isoformat()
        }
        return self.log_compression_event("COMPRESSION_START", data)
    
    def log_compression_end(self, start_event, outcome, duration_ms, compressed_to=None, error=None):
        """记录压缩结束事件"""
        data = {
            "outcome": outcome,
            "duration_ms": duration_ms,
            "compressed_to": compressed_to,
            "error": error,
            "end_time": datetime.now().isoformat()
        }
        
        if start_event and "data" in start_event:
            data["start_time"] = start_event["data"].get("start_time")
        
        return self.log_compression_event("COMPRESSION_END", data)
    
    def log_compression_skipped(self, reason, context_usage=None):
        """记录压缩跳过事件"""
        data = {
            "reason": reason,
            "context_usage": context_usage,
            "skipped_time": datetime.now().isoformat()
        }
        return self.log_compression_event("COMPRESSION_SKIPPED", data)
    
    def get_recent_events(self, event_type=None, limit=10):
        """获取最近的事件"""
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            if event_type:
                events = [e for e in events if e.get("event_type") == event_type]
            
            return events[-limit:]
        except Exception as e:
            self.logger.error(f"获取最近事件失败: {e}")
            return []
    
    def get_overflow_stats(self, hours=24):
        """获取超限统计"""
        events = self.get_recent_events("CONTEXT_OVERFLOW", limit=100)
        
        if not events:
            return {"total_overflows": 0, "average_usage": 0}
        
        total_usage = 0
        for event in events:
            if "data" in event and "usage_percentage" in event["data"]:
                total_usage += event["data"]["usage_percentage"]
        
        return {
            "total_overflows": len(events),
            "average_usage": round(total_usage / len(events), 2) if events else 0,
            "latest_overflow": events[-1] if events else None
        }
    
    def log_system_status(self, status_data):
        """记录系统状态"""
        return self.log_compression_event("SYSTEM_STATUS", status_data)

# 单例实例
_logger_instance = None

def get_logger():
    """获取日志记录器实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = CompressionLogger()
    return _logger_instance

if __name__ == "__main__":
    # 测试日志记录器
    logger = CompressionLogger()
    
    # 测试记录各种事件
    logger.log_context_overflow(103933, 98304, "test_error_id")
    logger.log_compression_start("overflow", 1, 3)
    time.sleep(0.1)
    logger.log_compression_end(None, "success", 100, compressed_to=50000)
    logger.log_compression_skipped("below_threshold", 45.5)
    
    # 获取统计
    stats = logger.get_overflow_stats()
    print(f"超限统计: {stats}")