#!/usr/bin/env python3
"""Groupy Lite - 分组版 v2"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APP_NAME = "Groupy Lite"

def get_window_app_name(wid):
    """获取窗口的应用名称"""
    try:
        import subprocess
        # 使用 xprop 获取 WM_CLASS
        result = subprocess.run(
            ['xprop', '-id', wid, 'WM_CLASS'],
            capture_output=True, text=True, timeout=1
        )
        output = result.stdout.strip()
        if 'WM_CLASS' in output:
            # 格式: WM_CLASS(STRING) = "instance", "Class"
            parts = output.split('=')
            if len(parts) >= 2:
                classes = parts[1].strip().strip('"').split('", "')
                if len(classes) >= 2:
                    return classes[1]  # 返回类名
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
        
        self.groups = {}  # {app_name: [window_names]}
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        vbox.pack_start(Gtk.Label(label="🏷️ Groupy Lite"), False, False, 5)

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

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(btn_box, False, False, 5)

        btn = Gtk.Button(label="🔄 刷新")
        btn.connect("clicked", self.load_windows)
        btn_box.pack_start(btn, True, True, 5)

        quit_btn = Gtk.Button(label="❌")
        quit_btn.connect("clicked", lambda x: sys.exit(0))
        vbox.pack_start(quit_btn, False, False, 5)

        self.show_all()
        self.present()
        self.load_windows(None)

    def load_windows(self, widget):
        """加载窗口，按应用分组"""
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
                    
                    # 获取应用名
                    app_name = get_window_app_name(wid)
                    if not app_name:
                        app_name = "Unknown"
                    
                    # 简化应用名
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
        
        # 常见应用映射
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
            'dingtalk': 'DingTalk',
            'lark': 'Lark',
            'feishu': 'FeiShu',
            'chrome': 'Chrome',
            'spotify': 'Spotify',
            'slack': 'Slack',
            'discord': 'Discord',
        }
        
        for key, value in mappings.items():
            if key in name:
                return value
        
        # 首字母大写
        return name.capitalize()

    def build_tree(self):
        """构建分组树"""
        search = self.search_entry.get_text().lower()
        
        for app_name, names in sorted(self.groups.items()):
            # 过滤
            if search:
                matched = [n for n in names if search in n.lower() or search in app_name.lower()]
                if not matched:
                    continue
                names = matched
            
            if not names:
                continue
            
            # 添加分组
            piter = self.store.append(None, [f"📁 {app_name}", ""])
            
            # 添加窗口
            for name in names:
                display_name = name[:45] + "..." if len(name) > 45 else name
                self.store.append(piter, [f"  {display_name}", name])

    def on_search(self, widget):
        self.load_windows(None)

    def on_select(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter:
            name = model[treeiter][1]
            if name:
                self.goto_window(name)

    def on_double_click(self, tree, path, column):
        model = tree.get_model()
        treeiter = model.get_iter(path)
        if treeiter:
            name = model[treeiter][1]
            if name:
                self.goto_window(name)

    def goto_window(self, name):
        print(f"跳转: {name}")
        try:
            import subprocess
            subprocess.run(['wmctrl', '-a', name], capture_output=True, timeout=1)
            print(f"成功")
        except Exception as e:
            print(f"失败: {e}")

if __name__ == "__main__":
    try:
        print("启动...")
        win = GroupyLiteWindow()
        print("运行中...")
        Gtk.main()
        print("退出")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
