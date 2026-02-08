#!/usr/bin/env python3
"""Groupy Lite - 最简测试版"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

print("1. 导入成功")

class TestWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Groupy Lite 测试")
        self.set_default_size(200, 100)
        
        label = Gtk.Label(label="✅ Groupy Lite 启动成功！\n\n点击 X 关闭")
        self.add(label)
        
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        print("2. 窗口显示成功")

if __name__ == "__main__":
    try:
        print("0. 开始启动...")
        win = TestWindow()
        print("3. 进入主循环...")
        Gtk.main()
        print("4. 退出")
    except Exception as e:
        print("错误:", e)
        sys.exit(1)
