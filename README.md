# 🗜️ Context Compressor Skill

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue.svg)](https://openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

智能上下文压缩系统，解决OpenClaw Agent上下文长度限制问题。自动检测、压缩和优化对话历史，防止上下文溢出导致的回复异常。

## ✨ 特性

### 🚨 问题解决
- **上下文溢出**：自动检测超过98,304字符限制
- **回复异常**：防止`[{`、乱码或表情回复
- **对话中断**：保持长对话连续性
- **记忆丢失**：保护重要信息不被截断

### 🏗️ 智能压缩
- **阈值检测**：70%使用率自动触发（可配置）
- **语义分析**：识别和保留关键信息
- **冗余删除**：智能删除问候、确认、闲聊
- **结构优化**：重新组织对话提升可读性

### 🔧 易于使用
- **即插即用**：简单安装，自动集成
- **配置灵活**：支持自定义阈值和策略
- **完整日志**：详细记录每次压缩操作
- **用户可控**：支持手动触发和预览

## 🚀 快速开始

### 安装
```bash
# 克隆仓库
git clone https://github.com/[你的用户名]/context-compressor-skill.git

# 安装为OpenClaw Skill
cd context-compressor-skill
ln -sf $(pwd) ~/.openclaw/workspace/skills/context-compressor

# 验证安装
ls -la ~/.openclaw/workspace/skills/ | grep context-compressor
```

### 配置
编辑 `config/compression_config.json`：
```json
{
  "compression": {
    "threshold_percent": 70,
    "max_context_length": 98304,
    "check_frequency_messages": 10
  },
  "strategy": {
    "preserve_keywords": ["指令", "决策", "重要", "项目"],
    "compress_keywords": ["你好", "谢谢", "明白了", "哈哈"]
  }
}
```

### 使用示例
```python
from scripts.context_monitor import ContextMonitor

# 监控上下文
monitor = ContextMonitor()
if monitor.needs_compression():
    print("⚠️ 上下文需要压缩")
    
    from scripts.smart_compressor import SmartCompressor
    compressor = SmartCompressor()
    result = compressor.compress()
    
    print(f"✅ 压缩完成: {result['compression_rate']}%")
```

## 📁 项目结构

```
context-compressor-skill/
├── SKILL.md                    # Skill主文档
├── README.md                   # 项目说明
├── LICENSE                     # MIT许可证
├── requirements.txt            # Python依赖
├── config/                     # 配置文件
│   └── compression_config.json # 压缩配置
├── scripts/                    # 核心脚本
│   ├── context_monitor.py     # 上下文监控
│   ├── smart_compressor.py    # 智能压缩器
│   └── compression_logger.py  # 日志记录器
├── assets/                     # 资源文件
├── tests/                      # 测试文件
└── examples/                   # 使用示例
```

## 🔧 核心功能

### 实时监控
- 持续跟踪上下文长度变化
- 预测溢出风险和时间
- 多维度使用率分析

### 智能压缩
- 基于语义的关键信息提取
- 渐进式压缩避免信息丢失
- 保持对话逻辑连贯性

### 完整记录
- 每次压缩的详细日志
- 性能指标统计和分析
- 用户反馈收集

## 🎯 适用场景

### 开发调试
```python
# 开发过程中监控上下文
monitor = ContextMonitor(debug=True)
monitor.start_monitoring()
```

### 生产环境
```yaml
# 在HEARTBEAT.md中集成
- [ ] 检查上下文长度是否超过70%
- [ ] 执行自动压缩（如需要）
- [ ] 记录压缩操作到日志
```

### 用户界面
```
🗜️ 上下文管理系统
────────────────
当前状态: 监控中
使用率: 65% (63,890/98,304)
上次压缩: 2小时前
压缩次数: 3次
平均压缩率: 42%
────────────────
```

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 压缩率 | 30-50% | 保留核心内容的同时减少长度 |
| 执行时间 | < 5秒 | 实时响应，不中断对话 |
| 内存使用 | < 50MB | 轻量级，不影响系统性能 |
| 准确率 | > 95% | 关键信息保留完整性 |
| 用户满意度 | > 90% | 基于用户反馈评分 |

## 🔄 工作流程

1. **监控**：实时监控上下文长度
2. **检测**：达到阈值时触发预警
3. **分析**：分析对话结构和内容
4. **压缩**：执行智能压缩算法
5. **验证**：检查压缩后完整性
6. **记录**：保存压缩日志和统计
7. **通知**：通知用户压缩结果

## 🛡️ 安全与隐私

### 数据安全
- ✅ 所有处理在本地完成
- ✅ 不发送任何数据到外部
- ✅ 加密存储压缩日志
- ✅ 严格的访问权限控制

### 隐私保护
- ✅ 用户完全控制压缩策略
- ✅ 可配置敏感话题保护
- ✅ 透明操作，完整记录
- ✅ 定期清理临时文件

## 👥 社区与支持

### 获取帮助
- **GitHub Issues**: 报告问题或请求功能
- **OpenClaw Discord**: 社区讨论和支持
- **文档网站**: 完整的使用指南

### 贡献代码
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建Pull Request

### 路线图
- **v1.0.0**: 基础压缩功能发布
- **v1.1.0**: 增强语义分析和NLP集成
- **v1.2.0**: 可视化界面和统计面板
- **v2.0.0**: 多Agent协同压缩系统

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和用户的支持，特别感谢：
- **OpenClaw社区**：优秀的AI Agent平台
- **早期测试者**：提供宝贵反馈和改进建议
- **开源贡献者**：让这个项目更加完善

---

**让OpenClaw对话不再受上下文限制！** 🗜️🚀

**问题反馈**: [GitHub Issues](https://github.com/[你的用户名]/context-compressor-skill/issues)
**讨论交流**: [OpenClaw Discord](https://discord.gg/openclaw)