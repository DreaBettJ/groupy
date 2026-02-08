#!/usr/bin/env python3
"""Groupy Lite - 极简版"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

APP_NAME = "Groupy Lite"

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(300, 500)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        # 标题
        vbox.pack_start(Gtk.Label(label="🏷️ Groupy Lite"), False, False, 5)

        # 搜索框
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("🔍 搜索...")
        vbox.pack_start(self.search_entry, False, False, 5)

        # 窗口列表
        self.listbox = Gtk.ListBox()
        sw = Gtk.ScrolledWindow()
        sw.add(self.listbox)
        vbox.pack_start(sw, True, True, 0)

        # 刷新按钮
        btn = Gtk.Button(label="🔄 刷新")
        btn.connect("clicked", self.refresh)
        vbox.pack_start(btn, False, False, 5)

        # 退出按钮
        quit_btn = Gtk.Button(label="❌")
        quit_btn.connect("clicked", lambda x: sys.exit(0))
        vbox.pack_start(quit_btn, False, False, 5)

        self.show_all()
        self.refresh(None)
        print("窗口已显示")

    def get_windows(self):
        """获取窗口"""
        try:
            import subprocess
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=2)
            windows = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        name = ' '.join(parts[3:])
                        if name and 'N/A' not in name:
                            windows.append(name)
            return windows
        except Exception as e:
            print(f"wmctrl 错误: {e}")
            return []

    def refresh(self, widget):
        """刷新"""
        # 清除
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        search = self.search_entry.get_text().lower()
        windows = self.get_windows()
        print(f"找到 {len(windows)} 个窗口")

        for name in windows:
            if search and search not in name.lower():
                continue
            self.add_button(name)

    def add_button(self, name):
        """添加按钮"""
        btn = Gtk.Button(label=name[:50] + "..." if len(name) > 50 else name)
        btn.set_alignment(0, 0)
        btn.connect("clicked", self.on_click, name)
        self.listbox.add(btn)

    def on_click(self, widget, name):
        """点击"""
        print(f"点击: {name}")
        try:
            import subprocess
            # 尝试多种方法激活窗口
            subprocess.run(['wmctrl', '-a', name], capture_output=True, timeout=1)
            print(f"激活成功")
        except Exception as e:
            print(f"wmctrl 失败: {e}")
            # 备选方案
            try:
                subprocess.run(['xdotool', 'search', '--name', name, 'windowactivate'], 
                              capture_output=True, timeout=1)
            except:
                pass

if __name__ == "__main__":
    try:
        win = GroupyLiteWindow()
        Gtk.main()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
