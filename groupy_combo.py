#!/usr/bin/env python3
"""Groupy Lite - 纯 wmctrl 版"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APP_NAME = "Groupy Lite"

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(300, 400)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        vbox.pack_start(Gtk.Label(label="🏷️ Groupy Lite"), False, False, 5)

        # 下拉选择框
        self.combo = Gtk.ComboBoxText()
        self.combo.set_entry_text_column(0)
        self.combo.connect("changed", self.on_select)
        vbox.pack_start(self.combo, False, False, 5)

        # 刷新按钮
        btn = Gtk.Button(label="🔄 刷新列表")
        btn.connect("clicked", self.load_windows)
        vbox.pack_start(btn, False, False, 5)

        # 跳转按钮
        goto_btn = Gtk.Button(label="➡️ 跳转到选中")
        goto_btn.connect("clicked", self.goto_selected)
        vbox.pack_start(goto_btn, False, False, 5)

        # 退出
        quit_btn = Gtk.Button(label="❌ 退出")
        quit_btn.connect("clicked", lambda x: sys.exit(0))
        vbox.pack_start(quit_btn, False, False, 5)

        self.show_all()
        self.load_windows(None)

    def load_windows(self, widget):
        """加载窗口列表"""
        self.combo.remove_all()
        
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
                            count += 1
            
            print(f"加载了 {count} 个窗口")
            
            if count > 0:
                self.combo.set_active(0)
                
        except Exception as e:
            print(f"错误: {e}")
            self.combo.append_text(f"错误: {e}")

    def on_select(self, widget):
        """选择"""
        pass

    def goto_selected(self, widget):
        """跳转到选中"""
        active = self.combo.get_active()
        if active >= 0:
            name = self.combo.get_model()[active][0]
            print(f"跳转: {name}")
            
            try:
                import subprocess
                subprocess.run(['wmctrl', '-a', name], capture_output=True, timeout=1)
                print("成功")
            except Exception as e:
                print(f"失败: {e}")

if __name__ == "__main__":
    try:
        win = GroupyLiteWindow()
        Gtk.main()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
