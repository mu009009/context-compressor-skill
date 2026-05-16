#!/bin/bash
# Conversation Compression Executor
# 对话压缩执行器
# 版本: 1.1.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$SKILL_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/compression_executor_$(date +%Y%m%d_%H%M%S).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 主函数
main() {
    log "🔧 对话压缩执行器启动"
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log "❌ Python3未找到"
        exit 1
    fi
    
    # 执行智能压缩
    log "🔄 执行智能压缩..."
    python3 "$SCRIPT_DIR/smart_compression_main.py" --after-conversation --mode=light
    
    # 记录压缩结果
    if [ $? -eq 0 ]; then
        log "✅ 压缩执行成功"
        exit 0
    else
        log "❌ 压缩执行失败"
        exit 1
    fi
}

# 捕获信号
trap 'log "⚠️  压缩被中断"; exit 1' INT TERM

# 执行主函数
main "$@"