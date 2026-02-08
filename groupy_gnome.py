#!/usr/bin/env python3
"""Groupy Lite - GNOME 原生版"""

import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Gdk, Wnck

APP_NAME = "Groupy Lite"

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(300, 500)
        self.windows = {}  # name -> window

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

        # 初始化 Wnck
        Wnck.Screen.get_default().force_update()

        # 窗口监控
        screen = Wnck.Screen.get_default()
        screen.connect("window-opened", self.on_window_opened)
        screen.connect("window-closed", self.on_window_closed)

        self.show_all()
        self.refresh(None)
        print("窗口已显示")

    def get_windows(self):
        """获取窗口列表"""
        windows = []
        screen = Wnck.Screen.get_default()
        for win in screen.get_windows():
            if win.get_window_type() == Wnck.WindowType.NORMAL:
                name = win.get_name()
                if name and 'N/A' not in name:
                    windows.append({'name': name, 'win': win})
        return windows

    def refresh(self, widget):
        """刷新"""
        # 清除
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        self.windows.clear()

        search = self.search_entry.get_text().lower()
        wins = self.get_windows()
        print(f"找到 {len(wins)} 个窗口")

        for w in wins:
            name = w['name']
            if search and search not in name.lower():
                continue
            self.windows[name] = w['win']
            self.add_button(name)

    def add_button(self, name):
        """添加按钮"""
        btn = Gtk.Button(label=name[:40] + "..." if len(name) > 40 else name)
        btn.set_halign(Gtk.Align.START)
        btn.connect("clicked", self.on_click, name)
        self.listbox.add(btn)

    def on_click(self, widget, name):
        """点击激活窗口"""
        print(f"点击: {name}")
        win = self.windows.get(name)
        if win:
            try:
                win.activate(Gtk.get_current_event_time())
                print(f"激活成功")
            except Exception as e:
                print(f"激活失败: {e}")

    def on_window_opened(self, screen, window):
        """窗口打开"""
        self.refresh(None)

    def on_window_closed(self, screen, window):
        """窗口关闭"""
        self.refresh(None)

if __name__ == "__main__":
    try:
        # 设置 Wnck 工作区
        Wnck.Screen.get_default().force_update()
        
        app = Gtk.Application(application_id="com.groupy.lite")
        app.connect("activate", lambda app: GroupyLiteWindow().show_all())
        app.run(sys.argv)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
