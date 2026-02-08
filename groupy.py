#!/usr/bin/env python3
"""Groupy Lite - 完整版"""

import sys
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

APP_NAME = "Groupy Lite"
LAST_FILE = os.path.expanduser("~/.config/groupy/last_selection")

def get_window_app_name(wid):
    """获取窗口的应用名称"""
    try:
        import subprocess
        result = subprocess.run(
            ['xprop', '-id', wid, 'WM_CLASS'],
            capture_output=True, text=True, timeout=1
        )
        output = result.stdout.strip()
        if 'WM_CLASS' in output:
            parts = output.split('=')
            if len(parts) >= 2:
                classes = parts[1].strip().strip('"').split('", "')
                if len(classes) >= 2:
                    return classes[1]
                elif len(classes) >= 1:
                    return classes[0]
    except:
        pass
    return None

class GroupyLiteWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(320, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)  # 不显示在任务栏
        self.stick()  # 始终可见
        
        self.groups = {}
        self.visible = True
        self.started = False
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        vbox.pack_start(Gtk.Label(label="🏷️ Groupy Lite"), False, False, 5)

        # 实时搜索
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("🔍 搜索...")
        self.search_entry.connect("changed", self.on_search)
        vbox.pack_start(self.search_entry, False, False, 5)

        self.store = Gtk.TreeStore(str, str)
        self.tree = Gtk.TreeView(model=self.store)
        
        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("应用 / 窗口", renderer, text=0)
        col.set_expand(True)
        self.tree.append_column(col)
        
        selection = self.tree.get_selection()
        selection.connect("changed", self.on_select)
        self.tree.connect("row-activated", self.on_double_click)
        
        sw = Gtk.ScrolledWindow()
        sw.add(self.tree)
        vbox.pack_start(sw, True, True, 5)

        self.status_label = Gtk.Label(label="💡 Alt+Q 启动 | Enter/双击 跳转 | Esc 隐藏")
        vbox.pack_start(self.status_label, False, False, 5)

        # 快捷键
        self.setup_accelerators()
        
        self.show_all()
        self.started = True
        
        # 确保窗口激活
        self.present()
        self.grab_focus()
        
        self.load_windows(None)

    def setup_accelerators(self):
        """设置快捷键"""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        # Alt+1 切换显示
        accel_group.connect(Gdk.KEY_1, Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE,
                           self.on_toggle)
        
        # Enter 跳转
        accel_group.connect(Gdk.KEY_Return, Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE,
                           self.on_enter)
        
        # Esc 隐藏
        accel_group.connect(Gdk.KEY_Escape, 0, Gtk.AccelFlags.VISIBLE,
                           self.on_escape)

    def on_toggle(self, accel_group, window, keyval, modifier):
        """Alt+1 切换显示"""
        self.toggle_visible()
        return True

    def on_enter(self, accel_group, window, keyval, modifier):
        """Alt+Enter 跳转选中"""
        if self.visible:
            selection = self.tree.get_selection()
            model, treeiter = selection.get_selected()
            if treeiter:
                name = model[treeiter][1]
                if name:
                    self.goto_window(name)
                    self.hide()
                    self.visible = False
        return True

    def on_escape(self, accel_group, window, keyval, modifier):
        """Esc 隐藏"""
        self.hide()
        self.visible = False
        return True

    def toggle_visible(self):
        """切换显示"""
        if self.visible:
            self.hide()
            self.visible = False
        else:
            self.present_and_focus()
            self.visible = True
            self.load_windows(None)

    def load_windows(self, widget):
        """加载窗口"""
        self.store.clear()
        self.groups = {}
        
        try:
            import subprocess
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=2)
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    wid = parts[0]
                    name = ' '.join(parts[3:])
                    
                    if not name or 'N/A' in name:
                        continue
                    
                    app_name = get_window_app_name(wid)
                    if not app_name:
                        app_name = "Unknown"
                    
                    app_name = self.simplify_app_name(app_name)
                    
                    if app_name not in self.groups:
                        self.groups[app_name] = []
                    self.groups[app_name].append(name)
            
            print(f"找到 {len(self.groups)} 个应用")
            self.build_tree()
                
        except Exception as e:
            print(f"错误: {e}")

    def simplify_app_name(self, name):
        """简化应用名"""
        name = name.lower()
        
        mappings = {
            'google-chrome': 'Chrome',
            'chromium-browser': 'Chrome',
            'firefox': 'Firefox',
            'nautilus': 'Files',
            'org.gnome.Nautilus': 'Files',
            'gnome-terminal-server': 'Terminal',
            'org.gnome.Terminal': 'Terminal',
            'guake': 'Guake',
            'code': 'VS Code',
            'jetbrains-idea-ce': 'IDEA',
            'jetbrains-idea': 'IDEA',
            'pycharm': 'PyCharm',
            'wechat': 'WeChat',
            'qq': 'QQ',
            'chrome': 'Chrome',
            'spotify': 'Spotify',
            'slack': 'Slack',
            'discord': 'Discord',
        }
        
        for key, value in mappings.items():
            if key in name:
                return value
        
        return name.capitalize()

    def build_tree(self):
        """构建分组树"""
        search = self.search_entry.get_text().lower()
        piter_list = []  # 保存所有分 iter 以便展开
        
        for app_name, names in sorted(self.groups.items()):
            if search:
                matched = [n for n in names if search in n.lower() or search in app_name.lower()]
                if not matched:
                    continue
                names = matched
            
            if not names:
                continue
            
            piter = self.store.append(None, [f"📁 {app_name}", ""])
            piter_list.append(piter)
            
            for name in names:
                display_name = name[:45] + "..." if len(name) > 45 else name
                self.store.append(piter, [f"  {display_name}", name])
        
        # 默认展开所有分组
        for piter in piter_list:
            path = self.store.get_path(piter)
            self.tree.expand_row(path, False)
        
        # 自动选中上次选择的窗口
        self.select_last()

    def select_last(self):
        """选中上次选择的窗口"""
        if not os.path.exists(LAST_FILE):
            return
        
        try:
            with open(LAST_FILE, "r") as f:
                last_name = f.read().strip()
            if not last_name:
                return
            
            # 在树中查找并选中
            def find_and_select(model, path, iter, data):
                name = model[iter][1]
                if name == last_name:
                    self.tree.get_selection().select_iter(iter)
                    # 滚动到该行
                    self.tree.scroll_to_cell(path, None, True, 0, 0)
                    return True
                return False
            
            self.store.foreach(find_and_select, None)
            
        except:
            pass

    def on_search(self, widget):
        """实时搜索"""
        self.load_windows(None)

    def on_select(self, selection):
        """选择"""
        model, treeiter = selection.get_selected()
        if treeiter:
            name = model[treeiter][1]
            if name:
                pass  # 准备好跳转

    def on_double_click(self, tree, path, column):
        """双击跳转"""
        model = tree.get_model()
        treeiter = model.get_iter(path)
        if treeiter:
            name = model[treeiter][1]
            if name:
                self.goto_window(name)
                self.hide()
                self.visible = False

    def goto_window(self, name):
        """跳转并退出"""
        print(f"跳转: {name}")
        
        # 保存选择
        try:
            with open(LAST_FILE, "w") as f:
                f.write(name)
        except:
            pass
        
        try:
            import subprocess
            subprocess.run(['wmctrl', '-a', name], capture_output=True, timeout=1)
            print("成功，退出")
            Gtk.main_quit()
            sys.exit(0)
        except Exception as e:
            print(f"失败: {e}")

if __name__ == "__main__":
    try:
        print("启动 Groupy Lite...")
        print("快捷键: Alt+Q 启动/显示 | Enter/双击 跳转 | Esc 隐藏")
        print("记住上次选择，开机自动选中")
        win = GroupyLiteWindow()
        Gtk.main()
        print("退出")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
