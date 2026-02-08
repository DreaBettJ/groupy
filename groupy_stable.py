#!/usr/bin/env python3
"""Groupy Lite - 稳定版"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APP_NAME = "Groupy Lite"

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(300, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)  # 置顶
        self.set_resizable(True)
        self.windows = []  # 存储窗口名称

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        vbox.pack_start(Gtk.Label(label="🏷️ Groupy Lite"), False, False, 5)

        # 下拉框
        self.combo = Gtk.ComboBoxText()
        self.combo.set_entry_text_column(0)
        self.combo.connect("changed", self.on_select)
        vbox.pack_start(self.combo, False, False, 5)

        # 按钮区域
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(btn_box, False, False, 5)

        # 刷新按钮
        btn = Gtk.Button(label="🔄 刷新")
        btn.connect("clicked", self.load_windows)
        btn_box.pack_start(btn, True, True, 5)

        # 跳转按钮
        goto_btn = Gtk.Button(label="➡️ 跳转")
        goto_btn.connect("clicked", self.goto_selected)
        btn_box.pack_start(goto_btn, True, True, 5)

        # 退出按钮
        quit_btn = Gtk.Button(label="❌")
        quit_btn.connect("clicked", lambda x: sys.exit(0))
        vbox.pack_start(quit_btn, False, False, 5)

        self.show_all()
        self.present()  # 激活并显示在最前面
        
        # 初始加载
        self.load_windows(None)

    def load_windows(self, widget):
        """加载窗口列表"""
        self.combo.remove_all()
        self.windows = []
        
        try:
            import subprocess
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=2)
            
            count = 0
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        name = ' '.join(parts[3:])
                        if name and 'N/A' not in name:
                            self.combo.append_text(name)
                            self.windows.append(name)
                            count += 1
            
            print(f"找到 {count} 个窗口")
            
            if count > 0:
                self.combo.set_active(0)
                
        except Exception as e:
            print(f"错误: {e}")
            self.combo.append_text(f"错误: {e}")

    def on_select(self, widget):
        """选择后自动跳转"""
        active = self.combo.get_active()
        if active >= 0 and active < len(self.windows):
            name = self.windows[active]
            print(f"选择: {name}")
            
            try:
                import subprocess
                result = subprocess.run(['wmctrl', '-a', name], capture_output=True, text=True, timeout=1)
                print(f"跳转成功")
            except Exception as e:
                print(f"失败: {e}")

    def goto_selected(self, widget):
        """跳转到选中"""
        active = self.combo.get_active()
        if active >= 0 and active < len(self.windows):
            name = self.windows[active]
            print(f"跳转: {name}")
            
            try:
                import subprocess
                result = subprocess.run(['wmctrl', '-a', name], capture_output=True, text=True, timeout=1)
                print(f"结果: {result.returncode}")
            except Exception as e:
                print(f"wmctrl 失败: {e}")

if __name__ == "__main__":
    try:
        print("启动...")
        win = GroupyLiteWindow()
        print("进入主循环...")
        Gtk.main()
        print("退出")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
