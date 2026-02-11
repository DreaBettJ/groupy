#!/bin/bash
# 自动检测当前 DISPLAY 并启动 groupy
export DISPLAY=$(cat /tmp/.X11-unix/X1 2>/dev/null | head -1)
if [ -z "$DISPLAY" ]; then
    # 备用方案：查找可用的 X display
    for d in /tmp/.X11-unix/X*; do
        num=$(basename "$d" | sed 's/X//')
        if [ -S "$d" ]; then
            export DISPLAY=":$num"
            break
        fi
    done
fi
python3 /home/lijiang/code/groupy/groupy.py
