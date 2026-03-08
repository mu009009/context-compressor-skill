#!/usr/bin/env python3
# 🧪 Context Compressor Skill 基础测试

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_loading():
    """测试配置文件加载"""
    print("🧪 测试配置文件加载...")
    
    from scripts.context_monitor import ContextMonitor
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        config = {
            "compression": {
                "threshold_percent": 75,
                "max_context_length": 100000
            }
        }
        json.dump(config, tmp)
        tmp_path = tmp.name
    
    try:
        monitor = ContextMonitor(config_path=tmp_path, debug=False)
        
        # 验证配置加载
        assert monitor.config["compression"]["threshold_percent"] == 75
        assert monitor.config["compression"]["max_context_length"] == 100000
        
        # 验证触发长度计算
        expected_trigger = 100000 * 0.75
        assert monitor.trigger_length == expected_trigger
        
        print("✅ 配置文件加载测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置文件加载测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        os.unlink(tmp_path)

def test_context_monitor():
    """测试上下文监控器"""
    print("🧪 测试上下文监控器...")
    
    from scripts.context_monitor import ContextMonitor
    
    try:
        monitor = ContextMonitor(debug=False)
        
        # 测试状态检查
        status = monitor.check_context_status()
        
        # 验证状态字典结构
        required_keys = [
            "current_length", "max_length", "usage_percent",
            "trigger_length", "needs_compression", "is_critical"
        ]
        
        for key in required_keys:
            assert key in status, f"状态字典缺少键: {key}"
        
        # 验证数据类型
        assert isinstance(status["current_length"], int)
        assert isinstance(status["usage_percent"], (int, float))
        assert isinstance(status["needs_compression"], bool)
        
        # 验证使用率计算
        expected_percent = (status["current_length"] / status["max_length"]) * 100
        assert abs(status["usage_percent"] - expected_percent) < 0.1
        
        print("✅ 上下文监控器测试通过")
        return True
    except Exception as e:
        print(f"❌ 上下文监控器测试失败: {e}")
        return False

def test_smart_compressor():
    """测试智能压缩器"""
    print("🧪 测试智能压缩器...")
    
    from scripts.smart_compressor import SmartCompressor
    
    try:
        compressor = SmartCompressor(debug=False)
        
        # 测试标准压缩
        result = compressor.compress(strength="standard")
        
        # 验证结果结构
        required_keys = [
            "success", "original_length", "compressed_length",
            "compression_rate", "compression_strength"
        ]
        
        for key in required_keys:
            assert key in result, f"结果字典缺少键: {key}"
        
        # 验证数据类型
        assert isinstance(result["success"], bool)
        assert isinstance(result["original_length"], int)
        assert isinstance(result["compressed_length"], int)
        assert isinstance(result["compression_rate"], (int, float))
        assert result["compression_strength"] == "standard"
        
        # 验证压缩率计算
        if result["original_length"] > 0:
            expected_rate = (1 - (result["compressed_length"] / result["original_length"])) * 100
            assert abs(result["compression_rate"] - expected_rate) < 0.1
        
        # 验证压缩后长度不大于原始长度
        assert result["compressed_length"] <= result["original_length"]
        
        print("✅ 智能压缩器测试通过")
        return True
    except Exception as e:
        print(f"❌ 智能压缩器测试失败: {e}")
        return False

def test_compression_logger():
    """测试压缩日志记录器"""
    print("🧪 测试压缩日志记录器...")
    
    from scripts.compression_logger import CompressionLogger
    
    try:
        logger = CompressionLogger(debug=False)
        
        # 创建测试压缩结果
        test_result = {
            "success": True,
            "original_length": 10000,
            "compressed_length": 6000,
            "compression_rate": 40.0,
            "compression_strength": "standard",
            "execution_time": 0.5,
            "preserved_key_info": {
                "important_keywords": ["指令", "决策"],
                "technical_terms": ["API", "数据库"],
                "decisions": ["决定"],
                "total_preserved": 3
            }
        }
        
        # 记录压缩操作
        logger.log_compression(test_result)
        
        # 获取统计信息
        stats = logger.get_statistics()
        
        # 验证统计信息结构
        assert "总体统计" in stats
        assert "压缩强度分布" in stats
        assert "每日统计" in stats
        
        # 验证统计更新
        overall_stats = stats["总体统计"]
        assert overall_stats["总压缩次数"] == 1
        assert overall_stats["成功次数"] == 1
        
        # 获取最近日志
        recent_logs = logger.get_recent_logs(1)
        assert len(recent_logs) > 0
        
        # 验证日志内容
        log_entry = recent_logs[0]
        assert log_entry["type"] == "compression"
        assert log_entry["result"]["compression_rate"] == 40.0
        
        print("✅ 压缩日志记录器测试通过")
        return True
    except Exception as e:
        print(f"❌ 压缩日志记录器测试失败: {e}")
        return False

def test_integration():
    """测试组件集成"""
    print("🧪 测试组件集成...")
    
    from scripts.context_monitor import ContextMonitor
    from scripts.smart_compressor import SmartCompressor
    from scripts.compression_logger import CompressionLogger
    
    try:
        # 创建组件实例
        monitor = ContextMonitor(debug=False)
        compressor = SmartCompressor(debug=False)
        logger = CompressionLogger(debug=False)
        
        # 模拟完整工作流程
        status = monitor.check_context_status()
        
        if status["needs_compression"]:
            # 执行压缩
            result = compressor.compress(strength="standard")
            
            # 记录压缩
            logger.log_compression(result)
            
            # 验证压缩效果
            assert result["success"] == True
            assert result["compressed_length"] < result["original_length"]
            
            # 获取统计报告
            report = logger.generate_report("text")
            assert "上下文压缩系统报告" in report
        
        print("✅ 组件集成测试通过")
        return True
    except Exception as e:
        print(f"❌ 组件集成测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行Context Compressor Skill测试")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_context_monitor,
        test_smart_compressor,
        test_compression_logger,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}通过, {failed}失败")
    
    if failed == 0:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 有测试失败，请检查问题")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)