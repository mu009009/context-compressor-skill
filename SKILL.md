---
name: context-compressor
description: 智能上下文压缩系统，解决OpenClaw Agent上下文长度限制问题。自动检测、压缩和优化对话历史，防止上下文溢出导致的回复异常。
---

# 🗜️ Context Compressor Skill

## 概述

Context Compressor Skill 是一个为OpenClaw AI Agent设计的智能上下文管理系统，专门解决Agent上下文长度限制导致的对话中断、回复异常和记忆丢失问题。当上下文接近最大限制时，系统自动执行智能压缩，保留关键信息，删除冗余内容，确保对话连续性。

## 🎯 适用场景

当出现以下情况时，应使用本Skill：

1. **上下文溢出错误**：收到 "Input length exceeds the maximum length" 错误
2. **回复异常**：Agent回复变成乱码、`[{` 或只有表情
3. **对话截断**：重要信息在长对话中被丢失
4. **频繁重启**：需要频繁重启会话来清理上下文
5. **长期对话**：需要维持跨多天的持续对话

## 🏗️ 系统架构

### 核心组件
```
context-compressor-skill/
├── SKILL.md                    # Skill主文档
├── README.md                   # 项目说明
├── config/                     # 配置文件
│   └── compression_config.json # 压缩配置
├── scripts/                    # 核心脚本
│   ├── context_monitor.py     # 上下文监控
│   ├── smart_compressor.py    # 智能压缩器
│   └── compression_logger.py  # 日志记录器
├── assets/                     # 资源文件
└── tests/                      # 测试文件
```

### 工作流程
1. **监控阶段**：实时监控上下文长度和使用率
2. **预警阶段**：达到阈值时预警并准备压缩
3. **压缩阶段**：执行智能压缩算法
4. **验证阶段**：验证压缩后上下文完整性
5. **记录阶段**：记录压缩操作和效果

## 🔧 核心功能

### 1. 智能阈值检测
- **动态阈值**：支持自定义触发百分比（默认70%）
- **实时监控**：持续监控上下文长度变化
- **预测预警**：基于对话速度预测溢出时间
- **多重触发**：阈值触发 + 时间触发 + 手动触发

### 2. 智能压缩算法
- **主题提取**：识别对话核心主题和关键信息
- **冗余删除**：自动删除问候、确认、重复内容
- **结构优化**：重新组织对话结构，提升可读性
- **语义保持**：确保压缩后语义连贯性

### 3. 安全压缩策略
- **关键保留**：用户指令、系统决策、重要信息
- **智能删除**：日常问候、重复确认、闲聊内容
- **可恢复性**：保留压缩记录，支持内容追溯
- **渐进压缩**：多次轻度压缩优于单次重度压缩

### 4. 完整监控系统
- **实时日志**：记录每次压缩操作详情
- **性能指标**：监控压缩率、执行时间、效果
- **错误处理**：优雅处理压缩失败情况
- **用户通知**：及时通知用户压缩状态

## 🚀 快速开始

### 安装方式
```bash
# 方式1: 作为OpenClaw Skill安装
git clone https://github.com/[用户名]/context-compressor-skill.git
cd context-compressor-skill
ln -sf $(pwd) ~/.openclaw/workspace/skills/context-compressor

# 方式2: 集成到现有系统
cp -r context-compressor-skill/config/ ~/.openclaw/workspace/
cp context-compressor-skill/scripts/*.py ~/.openclaw/workspace/scripts/
```

### 配置示例
```json
{
  "compression": {
    "threshold_percent": 70,
    "max_context_length": 98304,
    "check_frequency_messages": 10,
    "min_interval_minutes": 30
  },
  "strategy": {
    "preserve_keywords": ["指令", "决策", "重要", "项目", "约定"],
    "compress_keywords": ["问候", "确认", "闲聊", "表情"],
    "compression_ratio_target": 0.6
  }
}
```

### 基本使用
```python
from scripts.context_monitor import ContextMonitor

# 初始化监控器
monitor = ContextMonitor()

# 检查上下文状态
status = monitor.check_context_status()
if status["needs_compression"]:
    print(f"⚠️ 需要压缩: {status['usage_percent']}% 使用率")
    
# 执行智能压缩
from scripts.smart_compressor import SmartCompressor
compressor = SmartCompressor()
result = compressor.compress_context()
print(f"✅ 压缩完成: {result['compression_rate']}% 压缩率")
```

## 🔧 配置说明

### 主要配置项
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `threshold_percent` | 70 | 触发压缩的上下文使用率百分比 |
| `max_context_length` | 98304 | OpenClaw最大上下文长度 |
| `check_frequency` | 10 | 每多少条消息检查一次 |
| `min_interval` | 30 | 最小压缩间隔（分钟） |
| `preserve_list` | [...] | 必须保留的关键词列表 |
| `compress_list` | [...] | 可以压缩/删除的关键词列表 |

### 高级配置
- **自适应阈值**：根据对话类型动态调整阈值
- **学习模式**：学习用户偏好，优化压缩策略
- **多语言支持**：支持中英文混合对话压缩
- **插件架构**：支持自定义压缩算法插件

## 📊 性能指标

### 目标指标
- **压缩率**：30-50%（保留核心内容）
- **执行时间**：< 5秒（实时响应）
- **内存使用**：< 50MB（轻量级）
- **准确率**：> 95%（关键信息保留）

### 监控指标
- **上下文使用率**：实时监控和预警
- **压缩频率**：统计压缩操作次数
- **用户满意度**：基于反馈优化算法
- **错误率**：监控和处理异常情况

## 👥 用户交互

### 压缩通知
```
🗜️ 上下文压缩通知
────────────────
检测到上下文使用率已超过 75%
正在执行智能压缩...
────────────────
压缩完成！
• 压缩前：84,200 字符 (85%)
• 压缩后：49,300 字符 (50%)
• 压缩率：41%
• 关键信息：100% 保留
────────────────
对话连续性已保持 ✅
```

### 用户选项
- **通知级别**：静默、简要、详细
- **压缩强度**：轻度、标准、重度
- **手动触发**：随时手动请求压缩
- **预览模式**：压缩前预览效果

## 🔄 集成方式

### 与OpenClaw集成
```yaml
# 在HEARTBEAT.md中添加
- [ ] 检查上下文长度是否超过阈值
- [ ] 执行自动上下文压缩（如需要）
- [ ] 记录压缩操作到记忆文件
- [ ] 验证压缩后上下文连续性
```

### 与记忆系统集成
```python
# 压缩后自动更新记忆索引
from scripts.compression_logger import CompressionLogger
logger = CompressionLogger()
logger.log_compression(result)
logger.update_memory_index()
```

## 🛡️ 安全与隐私

### 数据安全
- **本地处理**：所有压缩在本地完成
- **无数据上传**：不发送任何对话内容到外部
- **加密日志**：压缩日志本地加密存储
- **权限控制**：严格的文件访问权限

### 隐私保护
- **选择性压缩**：可配置不压缩敏感话题
- **用户控制**：用户可随时禁用或调整
- **透明操作**：完整记录所有压缩操作
- **数据清理**：定期清理临时文件

## 📞 支持与贡献

### 问题报告
- GitHub Issues: 报告bug或功能请求
- 社区讨论: OpenClaw Discord频道
- 邮件支持: 通过GitHub联系维护者

### 贡献指南
1. Fork项目并创建功能分支
2. 编写测试确保功能正常
3. 提交Pull Request并描述更改
4. 等待代码审查和合并

### 路线图
- **v1.1.0**: 增强语义分析，集成NLP模型
- **v1.2.0**: 可视化压缩效果和统计
- **v1.3.0**: 多Agent上下文共享优化
- **v2.0.0**: 完全重构，支持插件化架构

---

**让OpenClaw对话更加流畅，不再受上下文限制困扰！** 🗜️🚀