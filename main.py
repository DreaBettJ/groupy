#!/usr/bin/env python3
"""Groupy - 窗口标签化管理工具"""

import sys
import json
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Gdk, Wnck, GLib

APP_NAME = "Groupy"
CONFIG_FILE = os.path.expanduser("~/.config/groupy/config.json")

class GroupyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_NAME)
        self.set_default_size(1200, 800)
        self.containers = {}  # window_xid -> container
        self.groups = {}  # group_name -> [windows]

        # 加载配置
        self.config = self.load_config()

        # 主布局
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.vbox)

        # 标签栏
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)
        self.notebook.connect("switch-page", self.on_page_switched)
        self.vbox.append(self.notebook)

        # 工具栏
        self.toolbar = Gtk.ActionBar()
        self.vbox.append(self.toolbar)

        # 新建分组按钮
        new_group_btn = Gtk.Button(label="➕ 新建分组")
        new_group_btn.connect("clicked", self.on_new_group_clicked)
        self.toolbar.pack_start(new_group_btn)

        # 设置按钮
        self.settings_btn = Gtk.Button(label="⚙️ 设置")
        self.settings_btn.connect("clicked", self.on_settings_clicked)
        self.toolbar.pack_end(self.settings_btn)

        # 初始化 Wnck
        Wnck.Screen.get_default()

        # 窗口监控
        self.screen = Wnck.Screen.get_default()
        self.screen.connect("window-opened", self.on_window_opened)
        self.screen.connect("window-closed", self.on_window_closed)

        # 定时检查窗口
        GLib.timeout_add(1000, self.check_windows)

        # 快捷键
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+N 新建分组
        ctrl_n = Gtk.ShortcutController.new()
        ctrl_n.set_scope(Gtk.ShortcutScope.GLOBAL)
        ctrl_n.add_shortcut(
            Gtk.Shortcut.new(
                Gtk.Keyval.from_name("n"),
                Gtk.ModifierType.CONTROL_MASK,
                Gtk.CallbackAction.new(self.on_new_group_shortcut),
                None
            )
        )
        self.add_controller(ctrl_n)

        # Ctrl+数字 切换标签页
        for i in range(1, 10):
            self.add_tab_shortcut(i)

    def add_tab_shortcut(self, num):
        """添加标签切换快捷键"""
        controller = Gtk.ShortcutController.new()
        controller.set_scope(Gtk.ShortcutScope.GLOBAL)
        controller.add_shortcut(
            Gtk.Shortcut.new(
                Gtk.Keyval.from_name(str(num)),
                Gtk.ModifierType.CONTROL_MASK,
                Gtk.CallbackAction.new(self.on_tab_switch_shortcut),
                GLib.Variant.new_int32(num)
            )
        )
        self.add_controller(controller)

    def on_new_group_shortcut(self, controller, args, data=None):
        """快捷键新建分组"""
        self.on_new_group_clicked(None)
        return True

    def on_tab_switch_shortcut(self, controller, args, data=None):
        """快捷键切换标签"""
        num = int(data) - 1  # 0-indexed
        if num < self.notebook.get_n_pages():
            self.notebook.set_current_page(num)
        return True
        
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"whitelist": [], "tab_position": "top"}
    
    def save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def on_window_opened(self, screen, window):
        """窗口打开时检查是否在白名单"""
        window_name = window.get_name()
        wm_class = window.get_class_instance_name() or ""
        
        print(f"窗口打开: {window_name} ({wm_class})")
        
        if self.is_whitelisted(window_name, wm_class):
            self.add_window_to_notebook(window)
    
    def on_window_closed(self, screen, window):
        """窗口关闭时移除"""
        window_xid = window.get_xid()
        if window_xid in self.containers:
            page_num = self.notebook.page_num(self.containers[window_xid])
            if page_num >= 0:
                self.notebook.remove_page(page_num)
            del self.containers[window_xid]
    
    def is_whitelisted(self, name, wm_class):
        """检查是否在白名单"""
        whitelist = self.config.get("whitelist", [])
        for item in whitelist:
            if item.lower() in name.lower() or item.lower() in wm_class.lower():
                return True
        return False
    
    def add_window_to_notebook(self, window):
        """将窗口添加到标签页"""
        window_xid = window.get_xid()
        if window_xid in self.containers:
            return

        window_name = window.get_name()
        wm_class = window.get_class_instance_name() or ""

        # 创建容器
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label_text = f"{window_name}"

        # 检查是否支持 XEmbed
        supports_xembed = window.is_skip_pager() or window.is_skip_tasklist()

        if supports_xembed:
            try:
                from gi.repository import GdkX11
                display = Gdk.Display.get_default()
                if display:
                    socket = Gtk.Socket()
                    container.append(socket)

                    # 延迟嵌入，确保 XID 有效
                    GLib.timeout_add(100, self.embed_window, socket, window_xid, container, label_text)
                    label_text = f"📎 {window_name}"
            except Exception as e:
                print(f"XEmbed 初始化失败: {e}")

        # 添加标签页
        label = Gtk.Label(label=label_text)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tab_box.append(label)

        # 关闭按钮
        close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_btn.set_valign(Gtk.Align.CENTER)
        close_btn.set_relief(Gtk.Relief.NONE)
        close_btn.connect("clicked", self.on_close_tab, window, container)
        tab_box.append(close_btn)

        page_num = self.notebook.append_page(container, tab_box)
        self.notebook.set_current_page(page_num)

        # 保存引用
        self.containers[window_xid] = container

    def embed_window(self, socket, window_xid, container, label_text):
        """执行窗口嵌入"""
        try:
            socket.add_id(window_xid)
            print(f"✅ 窗口嵌入成功: {window_xid}")
        except Exception as e:
            print(f"❌ 窗口嵌入失败: {e}")
            # 降级方案：显示占位符
            for child in container:
                container.remove(child)
            placeholder = Gtk.Label(label=f"📦 {label_text}")
            container.append(placeholder)
        return False  # 只执行一次

    def on_close_tab(self, btn, window, container):
        """关闭标签页"""
        page_num = self.notebook.page_num(container)
        if page_num >= 0:
            self.notebook.remove_page(page_num)
        window_xid = window.get_xid()
        if window_xid in self.containers:
            del self.containers[window_xid]
    
    def check_windows(self):
        """定时检查现有窗口"""
        windows = self.screen.get_windows()
        for window in windows:
            if window.get_window_type() == Wnck.WindowType.NORMAL:
                if self.is_whitelisted(window.get_name(), 
                                       window.get_class_instance_name() or ""):
                    self.add_window_to_notebook(window)
        return True

    def on_new_group_clicked(self, widget):
        """新建分组"""
        dialog = Gtk.Dialog(title="新建分组", transient_for=self)
        dialog.set_default_size(300, 100)

        entry = Gtk.Entry()
        entry.set_placeholder_text("分组名称")
        dialog.get_content_area().append(entry)

        def create_group(response):
            if response == Gtk.ResponseType.OK:
                group_name = entry.get_text().strip()
                if group_name:
                    self.add_empty_group(group_name)
            dialog.destroy()

        dialog.add_button("创建", Gtk.ResponseType.OK)
        dialog.add_button("取消", Gtk.ResponseType.CANCEL)
        dialog.connect("response", create_group)
        dialog.present()

    def add_empty_group(self, name):
        """添加空分组"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=f"📁 {name}")

        # 添加标签页
        page_num = self.notebook.append_page(container, label)
        self.notebook.set_current_page(page_num)

    def on_settings_clicked(self, widget):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        dialog.present()


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Groupy 设置", transient_for=parent)
        self.set_default_size(400, 300)
        self.parent = parent

        self.vbox = self.get_content_area()

        # 白名单输入
        label = Gtk.Label(label="白名单应用 (逗号分隔):")
        self.vbox.append(label)

        whitelist_text = ", ".join(parent.config.get("whitelist", []))
        self.entry = Gtk.Entry()
        self.entry.set_text(whitelist_text)
        self.vbox.append(self.entry)

        # 添加按钮
        add_btn = Gtk.Button(label="➕ 添加当前窗口")
        add_btn.connect("clicked", self.add_current_window)
        self.vbox.append(add_btn)

        # 清空按钮
        clear_btn = Gtk.Button(label="🗑️ 清空白名单")
        clear_btn.connect("clicked", self.clear_whitelist)
        self.vbox.append(clear_btn)

        # 保存按钮
        save_btn = Gtk.Button(label="💾 保存")
        save_btn.connect("clicked", self.save_config)
        self.vbox.append(save_btn)

        self.show()

    def add_current_window(self, widget):
        """添加当前活动窗口到白名单"""
        screen = Wnck.Screen.get_default()
        active_window = screen.get_active_window()
        if active_window:
            wm_class = active_window.get_class_instance_name() or ""
            current_text = self.entry.get_text()
            if wm_class and wm_class not in current_text:
                self.entry.set_text(f"{current_text}, {wm_class}" if current_text else wm_class)

    def clear_whitelist(self, widget):
        """清空白名单"""
        self.entry.set_text("")

    def save_config(self, widget):
        text = self.entry.get_text()
        whitelist = [x.strip() for x in text.split(",") if x.strip()]
        self.parent.config["whitelist"] = whitelist
        self.parent.save_config()
        self.destroy()


class GroupyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.groupy.app")
    
    def do_activate(self):
        window = GroupyWindow()
        self.add_window(window)
        window.present()


if __name__ == "__main__":
    from gi.repository import GLib
    app = GroupyApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
