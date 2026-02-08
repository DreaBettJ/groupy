#!/usr/bin/env python3
"""Groupy Lite - 窗口快速切换工具"""

import sys
import json
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

APP_NAME = "Groupy Lite"
CONFIG_FILE = os.path.expanduser("~/.config/groupy/config.json")

# 简单的窗口信息存储
known_windows = {}

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(300, 500)

        # 加载配置
        self.config = self.load_config()

        # 主布局
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(self.vbox)

        # 标题
        title_label = Gtk.Label(label="🏷️ Groupy Lite - 窗口切换器")
        self.vbox.pack_start(title_label, False, False, 5)

        # 搜索框
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("🔍 搜索窗口...")
        self.search_entry.connect("changed", self.on_search)
        self.vbox.pack_start(self.search_entry, False, False, 5)

        # 窗口列表
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.sw = Gtk.ScrolledWindow()
        self.sw.add(self.listbox)
        self.vbox.pack_start(self.sw, True, True, 0)

        # 按钮区域
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.vbox.pack_start(btn_box, False, False, 5)

        # 刷新按钮
        refresh_btn = Gtk.Button(label="🔄 刷新")
        refresh_btn.connect("clicked", self.refresh_windows)
        btn_box.pack_start(refresh_btn, True, True, 0)

        # 设置按钮
        settings_btn = Gtk.Button(label="⚙️ 设置")
        settings_btn.connect("clicked", self.on_settings_clicked)
        btn_box.pack_start(settings_btn, True, True, 0)

        # 退出按钮
        quit_btn = Gtk.Button(label="❌ 退出")
        quit_btn.connect("clicked", lambda x: sys.exit(0))
        btn_box.pack_start(quit_btn, True, True, 0)

        self.show_all()
        print("窗口已显示，5秒后刷新...")
        
        # 5秒后刷新
        GLib.timeout_add(5000, self.refresh_windows)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"whitelist": [], "tab_position": "top"}

    def save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_windows(self):
        """获取窗口列表 - 使用 wmctrl 或 xdotool"""
        windows = []
        
        # 确保 DISPLAY 设置正确
        display = os.environ.get('DISPLAY', ':0')
        if not display:
            display = ':0'
        os.environ['DISPLAY'] = display
        print(f"DISPLAY={display}")
        
        # 方法1: 使用 wmctrl
        try:
            import subprocess
            env = os.environ.copy()
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, 
                                    timeout=2, env=env)
            print(f"wmctrl 输出: {result.stdout[:100]}")
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        wid = parts[0]
                        name = ' '.join(parts[3:])
                        windows.append({'id': wid, 'name': name})
            if windows:
                return windows, 'wmctrl'
        except Exception as e:
            print(f"wmctrl 错误: {e}")
        
        return windows, 'none'

    def refresh_windows(self, widget):
        """刷新窗口列表"""
        print("刷新窗口列表...")
        
        try:
            # 清除现有项
            for child in self.listbox.get_children():
                self.listbox.remove(child)
            known_windows.clear()

            search_text = self.search_entry.get_text().lower()
            
            # 获取窗口
            windows, method = self.get_windows()
            print(f"找到 {len(windows)} 个窗口 (方法: {method})")
            
            for win in windows:
                name = win['name']
                if not name or name.strip() == '':
                    continue
                
                # 搜索过滤
                if search_text and search_text not in name.lower():
                    continue
                
                known_windows[name] = win['id']
                self.add_window_to_list(name)

            self.show_all()
            print(f"显示 {len(known_windows)} 个窗口")
        except Exception as e:
            print(f"刷新错误: {e}")
            import traceback
            traceback.print_exc()
        
        return False  # 只运行一次

    def add_window_to_list(self, name):
        """添加窗口到列表"""
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add(box)

        # 默认图标
        icon = Gtk.Image.new_from_icon_name("application-default-icon", Gtk.IconSize.MENU)
        box.pack_start(icon, False, False, 5)

        # 标签
        label = Gtk.Label(label=name, xalign=0)
        box.pack_start(label, True, True, 0)

        # 点击激活
        def on_click(widget, event, win_name=name):
            if event.type == Gdk.EventType.BUTTON_PRESS:
                self.activate_window(win_name)

        row.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        row.connect("button-press-event", on_click)

        self.listbox.add(row)

    def activate_window(self, name):
        """激活窗口"""
        wid = known_windows.get(name)
        if not wid:
            return
        
        try:
            import subprocess
            subprocess.run(['wmctrl', '-i', '-a', wid], capture_output=True, timeout=1)
            print(f"激活窗口: {name}")
        except:
            try:
                import subprocess
                subprocess.run(['xdotool', 'windowactivate', wid], capture_output=True, timeout=1)
                print(f"激活窗口 (xdotool): {name}")
            except Exception as e:
                print(f"激活失败: {e}")

    def on_search(self, widget):
        """搜索"""
        self.refresh_windows(None)

    def on_settings_clicked(self, widget):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        dialog.run()
        dialog.destroy()


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title="Groupy Lite 设置", parent=parent, modal=True)
        self.set_default_size(400, 200)
        self.parent = parent

        box = self.get_content_area()

        label = Gtk.Label(label="白名单应用 (逗号分隔，留空显示所有):")
        box.pack_start(label, False, False, 5)

        whitelist_text = ", ".join(parent.config.get("whitelist", []))
        self.entry = Gtk.Entry()
        self.entry.set_text(whitelist_text)
        box.pack_start(self.entry, False, False, 5)

        save_btn = Gtk.Button(label="💾 保存")
        save_btn.connect("clicked", self.save_config)
        box.pack_start(save_btn, False, False, 5)

        self.show_all()

    def save_config(self, widget):
        text = self.entry.get_text()
        if text.strip():
            whitelist = [x.strip() for x in text.split(",") if x.strip()]
            self.parent.config["whitelist"] = whitelist
        else:
            self.parent.config["whitelist"] = []
        self.parent.save_config()
        self.parent.refresh_windows(None)
        self.destroy()


if __name__ == "__main__":
    try:
        app = Gtk.Application(application_id="com.groupy.lite.app")
        app.connect("activate", lambda app: GroupyLiteWindow().show_all())
        app.run(sys.argv)
    except Exception as e:
        print("错误:", e)
        sys.exit(1)
