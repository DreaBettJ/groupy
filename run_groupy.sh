#!/bin/bash
# Groupy 启动脚本 - 处理本地和 RDP 环境的 Display 兼容性问题

set -e

echo "🚀 启动 Groupy..."

# 优先级1：使用现有 DISPLAY（本地桌面）
if [ -n "$DISPLAY" ]; then
    echo "✓ 使用现有 DISPLAY: $DISPLAY"
fi

# 优先级2：如果没有 DISPLAY，查找可用的 X11 socket
if [ -z "$DISPLAY" ]; then
    echo "🔧 未检测到 DISPLAY，尝试自动配置..."
    
    # 查找当前用户的 X11 socket
    USER_X11="/tmp/.X11-unix/X${DISPLAY:-:0}"
    
    # 如果 :0 不存在，尝试查找其他 socket
    if [ ! -S "$USER_X11" ]; then
        # 查找所有 socket，按修改时间排序（最新的优先）
        SOCKETS=$(ls -1t /tmp/.X11-unix/X* 2>/dev/null | head -5)
        for sock in $SOCKETS; do
            if [ -S "$sock" ]; then
                DISPLAY_NUM=$(basename "$sock" | sed 's/X//')
                export DISPLAY=":$DISPLAY_NUM"
                echo "✓ 自动配置 DISPLAY: $DISPLAY (from $sock)"
                break
            fi
        done
    fi
fi

# 优先级3：WAYLAND
if [ -z "$DISPLAY" ] && [ -n "$WAYLAND_DISPLAY" ]; then
    export DISPLAY="$WAYLAND_DISPLAY"
    echo "✓ 使用 WAYLAND_DISPLAY: $DISPLAY"
fi

# 最终检查
if [ -z "$DISPLAY" ]; then
    echo "⚠️  警告：未检测到显示环境，尝试使用 :0"
    export DISPLAY=":0"
fi

echo "✅ 最终 DISPLAY: $DISPLAY"

# 启动 Groupy
exec python3 /home/lijiang/code/groupy/groupy.py "$@"
