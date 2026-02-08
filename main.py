#!/usr/bin/env python3
"""Groupy - 窗口标签化管理工具"""

import sys
import json
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Gdk, Wnck, GLib, GdkX11

APP_NAME = "Groupy"
CONFIG_FILE = os.path.expanduser("~/.config/groupy/config.json")

class GroupyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(1200, 800)
        self.containers = {}  # window_xid -> container
        self.groups = {}  # group_name -> [windows]

        # 加载配置
        self.config = self.load_config()

        # 主布局
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        # 标签栏
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)
        self.notebook.connect("switch-page", self.on_page_switched)
        self.vbox.pack_start(self.notebook, True, True, 0)

        # 工具栏
        self.toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.vbox.pack_start(self.toolbar, False, False, 0)

        # 新建分组按钮
        new_group_btn = Gtk.Button(label="➕ 新建分组")
        new_group_btn.connect("clicked", self.on_new_group_clicked)
        self.toolbar.pack_start(new_group_btn, False, False, 0)

        # 设置按钮
        self.settings_btn = Gtk.Button(label="⚙️ 设置")
        self.settings_btn.connect("clicked", self.on_settings_clicked)
        self.toolbar.pack_end(self.settings_btn, False, False, 0)

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
        """设置快捷键 - GTK 3 使用 AccelGroup"""
        # Super+G 新建分组
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        accel_group.connect(Gdk.KEY_g, Gdk.ModifierType.SUPER_MASK, Gtk.AccelFlags.VISIBLE,
                           self.on_new_group_shortcut)

        # Super+数字 切换标签页 - 使用闭包捕获 num
        for i in range(1, 10):
            self.add_tab_accel(i, accel_group)

    def add_tab_accel(self, num, accel_group):
        """添加标签切换快捷键 - 使用闭包"""
        callback = self.make_tab_callback(num)
        accel_group.connect(Gdk.KEY_0 + num, Gdk.ModifierType.SUPER_MASK, Gtk.AccelFlags.VISIBLE,
                           callback)

    def make_tab_callback(self, num):
        """创建闭包回调"""
        def callback(accel_group, window, keyval, modifier):
            target_num = num - 1  # 0-indexed
            if target_num < self.notebook.get_n_pages():
                self.notebook.set_current_page(target_num)
            return True
        return callback

    def on_new_group_shortcut(self, accel_group, window, keyval, modifier):
        """快捷键新建分组"""
        self.on_new_group_clicked(None)
        return True

    def on_page_switched(self, notebook, page, page_num):
        """页面切换时更新"""
        pass

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

        print("窗口打开: {} ({})".format(window_name, wm_class))

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
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        label_text = "{}".format(window_name)

        # 检查是否支持 XEmbed
        supports_xembed = window.is_skip_pager() or window.is_skip_tasklist()

        if supports_xembed:
            try:
                display = Gdk.Display.get_default()
                if display:
                    socket = Gtk.Socket()
                    container.pack_start(socket, True, True, 0)

                    # 延迟嵌入，确保 XID 有效
                    GLib.timeout_add(100, self.embed_window, socket, window_xid, container, label_text)
                    label_text = "📎 {}".format(window_name)
            except Exception as e:
                print("XEmbed 初始化失败: {}".format(e))

        # 添加标签页
        label = Gtk.Label(label=label_text)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_box.pack_start(label, False, False, 0)

        # 关闭按钮
        close_btn = Gtk.Button()
        close_btn.set_image(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        close_btn.set_relief(Gtk.Relief.NONE)
        close_btn.connect("clicked", self.on_close_tab, window, container)
        tab_box.pack_start(close_btn, False, False, 0)

        page_num = self.notebook.append_page(container, tab_box)
        self.notebook.set_current_page(page_num)

        # 保存引用
        self.containers[window_xid] = container

    def embed_window(self, socket, window_xid, container, label_text):
        """执行窗口嵌入"""
        try:
            socket.add_id(window_xid)
            print("✅ 窗口嵌入成功: {}".format(window_xid))
        except Exception as e:
            print("❌ 窗口嵌入失败: {}".format(e))
            # 降级方案：显示占位符
            for child in container.get_children():
                container.remove(child)
            placeholder = Gtk.Label(label="📦 {}".format(label_text))
            container.pack_start(placeholder, True, True, 0)
            placeholder.show()
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
        dialog = Gtk.Dialog(title="新建分组", parent=self, modal=True)
        dialog.set_default_size(300, 100)

        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("分组名称")
        box.pack_start(entry, False, False, 0)

        def create_group(button, response):
            if response == Gtk.ResponseType.OK:
                group_name = entry.get_text().strip()
                if group_name:
                    self.add_empty_group(group_name)
            dialog.destroy()

        dialog.add_button("创建", Gtk.ResponseType.OK)
        dialog.add_button("取消", Gtk.ResponseType.CANCEL)
        dialog.connect("response", create_group)
        dialog.show_all()

    def add_empty_group(self, name):
        """添加空分组"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        label = Gtk.Label(label="📁 {}".format(name))

        # 添加标签页
        page_num = self.notebook.append_page(container, label)
        self.notebook.set_current_page(page_num)

    def on_settings_clicked(self, widget):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        dialog.run()
        dialog.destroy()


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title="Groupy 设置", parent=parent, modal=True)
        self.set_default_size(400, 300)
        self.parent = parent

        box = self.get_content_area()

        # 白名单输入
        label = Gtk.Label(label="白名单应用 (逗号分隔):")
        box.pack_start(label, False, False, 5)

        whitelist_text = ", ".join(parent.config.get("whitelist", []))
        self.entry = Gtk.Entry()
        self.entry.set_text(whitelist_text)
        box.pack_start(self.entry, False, False, 5)

        # 添加按钮
        add_btn = Gtk.Button(label="➕ 添加当前窗口")
        add_btn.connect("clicked", self.add_current_window)
        box.pack_start(add_btn, False, False, 5)

        # 清空按钮
        clear_btn = Gtk.Button(label="🗑️ 清空白名单")
        clear_btn.connect("clicked", self.clear_whitelist)
        box.pack_start(clear_btn, False, False, 5)

        # 保存按钮
        save_btn = Gtk.Button(label="💾 保存")
        save_btn.connect("clicked", self.save_config)
        box.pack_start(save_btn, False, False, 5)

        self.show_all()

    def add_current_window(self, widget):
        """添加当前活动窗口到白名单"""
        screen = Wnck.Screen.get_default()
        active_window = screen.get_active_window()
        if active_window:
            wm_class = active_window.get_class_instance_name() or ""
            current_text = self.entry.get_text()
            if wm_class and wm_class not in current_text:
                self.entry.set_text("{}, {}".format(current_text, wm_class) if current_text else wm_class)

    def clear_whitelist(self, widget):
        """清空白名单"""
        self.entry.set_text("")

    def save_config(self, widget):
        text = self.entry.get_text()
        whitelist = [x.strip() for x in text.split(",") if x.strip()]
        self.parent.config["whitelist"] = whitelist
        self.parent.save_config()
        self.destroy()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.groupy.app")
    app.connect("activate", lambda app: GroupyWindow().show_all())
    app.run(sys.argv)
