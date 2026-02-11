#!/bin/bash
# Groupy 启动脚本 - 处理本地和 RDP 环境的 Display 兼容性问题

set -e

echo "🚀 启动 Groupy..."

# 优先级1：使用现有 DISPLAY（本地桌面或 RDP 转发）
if [ -n "$DISPLAY" ]; then
    echo "✓ 使用现有 DISPLAY: $DISPLAY"
else
    # 查找可用的 X11 socket
    SOCKETS=$(ls -1t /tmp/.X11-unix/X* 2>/dev/null | head -5)
    for sock in $SOCKETS; do
        if [ -S "$sock" ]; then
            DISPLAY_NUM=$(basename "$sock" | sed 's/X//')
            export DISPLAY=":$DISPLAY_NUM"
            echo "✓ 自动配置 DISPLAY: $DISPLAY"
            break
        fi
    done
fi

# 设置 xhost 权限（RDP 环境需要）
xhost +local: >/dev/null 2>&1 || true

# 最终检查
if [ -z "$DISPLAY" ]; then
    echo "⚠️  未检测到显示环境"
    export DISPLAY=":0"
fi

echo "✅ 最终 DISPLAY: $DISPLAY"

# 启动 Groupy
exec python3 /home/lijiang/code/groupy/groupy.py "$@"
