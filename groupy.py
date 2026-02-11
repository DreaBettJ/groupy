#!/usr/bin/env python3
"""Groupy Lite - 完整版"""

import sys
import os

# Display 兼容层
def setup_display():
    """在导入 GTK 前设置好 DISPLAY"""
    if os.environ.get('DISPLAY'):
        return True
    
    # 查找可用的 X11 socket
    import glob
    sockets = glob.glob('/tmp/.X11-unix/X*')
    for sock in sorted(sockets):
        if os.path.exists(sock) and os.access(sock, os.W_OK):
            display_num = os.path.basename(sock)[1:]
            os.environ['DISPLAY'] = f":{display_num}"
            print(f"🔧 自动配置 DISPLAY: {os.environ['DISPLAY']}")
            return True
    
    return False

setup_display()

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

APP_NAME = "Groupy Lite"
LAST_FILE = os.path.expanduser("~/.config/groupy/last_selection")
LOCK_FILE = os.path.expanduser("~/.config/groupy/groupy.lock")

def check_single_instance():
    """检查是否已有实例运行"""
    import subprocess
    
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid='], 
                                  capture_output=True, text=True)
            if pid and result.stdout.strip():
                try:
                    subprocess.run(['wmctrl', '-a', APP_NAME], capture_output=True, timeout=1)
                except:
                    pass
                print(f"Groupy 已在运行 (PID: {pid})")
                return False
        except:
            pass
    
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass
    
    return True

def get_window_app_name(wid):
    """获取窗口的应用名称"""
    try:
        import subprocess
        result = subprocess.run(
            ['xdotool', 'getwindowclassname', str(wid)],
            capture_output=True, text=True, timeout=1
        )
        return result.stdout.strip()
    except:
        return None

def get_all_windows():
    """获取所有窗口"""
    windows = []
    try:
        import subprocess
        result = subprocess.run(
            ['wmctrl', '-l'],
            capture_output=True, text=True, timeout=2
        )
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                wid = parts[0]
                desktop = parts[1]
                machine = parts[2]
                title = ' '.join(parts[3:])
                
                app_name = get_window_app_name(wid)
                if app_name:
                    windows.append({
                        'wid': wid,
                        'desktop': desktop,
                        'machine': machine,
                        'title': title,
                        'app': app_name
                    })
    except Exception as e:
        print(f"获取窗口列表失败: {e}")
    
    return windows

def group_windows_by_app(windows):
    """按应用分组窗口"""
    groups = {}
    for w in windows:
        app = w['app']
        if app not in groups:
            groups[app] = []
        groups[app].append(w)
    return groups

class GroupyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(400, 500)
        self.set_decorated(False)
        self.set_keep_above(True)
        
        self.selected_windows = []
        self.groups = {}
        
        self.setup_ui()
        self.load_windows()
        self.restore_last_selection()
        
        # 快捷键
        AccelGroup = Gtk.AccelGroup
        self.accel_group = AccelGroup()
        self.add_accel_group(self.accel_group)
        
        self.connect("key-press-event", self.on_key_press)
        
    def setup_ui(self):
        """设置 UI"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)
        
        # 标题栏
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header.set_size_request(-1, 35)
        
        title_label = Gtk.Label(label=f"  {APP_NAME}")
        title_label.set_hexpand(True)
        title_label.set_alignment(0, 0.5)
        header.pack_start(title_label, True, True, 0)
        
        close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.connect("clicked", lambda w: self.hide())
        header.pack_end(close_btn, False, False, 0)
        
        vbox.pack_start(header, False, False, 0)
        
        # 分隔线
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, False, 0)
        
        # 搜索框
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("🔍 搜索窗口...")
        self.search_entry.connect("changed", self.on_search)
        vbox.pack_start(self.search_entry, False, False, 5)
        
        # 滚动窗口
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        vbox.pack_start(scrolled, True, True, 0)
        
        # 列表容器
        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.list_box.set_hexpand(True)
        self.list_box.set_vexpand(True)
        scrolled.add(self.list_box)
        
        # 提示信息
        self.status_label = Gtk.Label(label="↑↓ 导航 | Enter 跳转 | Esc 隐藏")
        self.status_label.set_margin_top(5)
        self.status_label.set_margin_bottom(5)
        vbox.pack_end(self.status_label, False, False, 0)
        
    def load_windows(self):
        """加载窗口"""
        # 清除现有列表
        for child in self.list_box.get_children():
            child.destroy()
        
        self.groups = {}
        self.all_windows = []
        
        windows = get_all_windows()
        self.groups = group_windows_by_app(windows)
        self.all_windows = windows
        
        # 排序
        apps = sorted(self.groups.keys())
        
        # 创建分组
        for app in apps:
            self.create_group(app, self.groups[app])
        
        # 显示所有窗口数
        count = len(windows)
        self.status_label.set_text(f"📊 {count} 个窗口 | ↑↓ 导航 | Enter 跳转 | Esc 隐藏")
    
    def create_group(self, app_name, windows):
        """创建分组"""
        # 分组标题
        expander = Gtk.Expander(label=f" 📂 {app_name} ({len(windows)})")
        expander.set_expanded(True)
        expander.set_hexpand(True)
        self.list_box.pack_start(expander, False, False, 2)
        
        # 容器
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_border_width(0)
        expander.add(vbox)
        
        for w in windows:
            btn = self.create_window_item(w)
            vbox.pack_start(btn, False, False, 0)
    
    def create_window_item(self, window):
        """创建窗口项"""
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_alignment(0, 0.5)
        
        # 显示窗口标题
        label = Gtk.Label(label=f"  {window['title'][:40]}")
        label.set_alignment(0, 0.5)
        label.set_line_wrap(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(label, True, True, 0)
        
        btn.add(box)
        
        def on_clicked(w, wid=window['wid'], title=window['title']):
            self.activate_window(wid)
        
        btn.connect("clicked", on_clicked)
        
        # 右键菜单
        menu = Gtk.Menu()
        
        activate_item = Gtk.MenuItem(label="激活")
        activate_item.connect("activate", lambda w: self.activate_window(window['wid']))
        menu.append(activate_item)
        
        close_item = Gtk.MenuItem(label="关闭")
        close_item.connect("activate", lambda w: self.close_window(window['wid']))
        menu.append(close_item)
        
        menu.show_all()
        btn.connect("button-press-event", lambda w, e: menu.popup_at_pointer(e) if e.button == 3 else None)
        
        return btn
    
    def activate_window(self, wid):
        """激活窗口"""
        import subprocess
        try:
            subprocess.run(['wmctrl', '-i', '-a', wid], capture_output=True, timeout=1)
            self.hide()
        except Exception as e:
            print(f"激活窗口失败: {e}")
    
    def close_window(self, wid):
        """关闭窗口"""
        import subprocess
        try:
            subprocess.run(['wmctrl', '-i', '-c', wid], capture_output=True, timeout=1)
            self.load_windows()
        except Exception as e:
            print(f"关闭窗口失败: {e}")
    
    def on_search(self, entry):
        """搜索"""
        text = entry.get_text().lower()
        for child in self.list_box.get_children():
            if isinstance(child, Gtk.Expander):
                label = child.get_label()
                is_visible = any(text in w['title'].lower() or text in w['app'].lower() 
                               for w in self.groups.get(label.split()[1].split('(')[0].strip(), []))
                child.set_visible(is_visible or not text)
                
                for sub_child in child.get_child().get_children():
                    if isinstance(sub_child, Gtk.Button):
                        w_title = sub_child.get_child().get_children()[0].get_text()
                        app_name = label.split()[1].split('(')[0]
                        sub_child.set_visible(text in w_title.lower() or not text)
    
    def on_key_press(self, widget, event):
        """快捷键处理"""
        key = Gdk.keyval_name(event.keyval)
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        
        # Esc: 隐藏
        if key == "Escape" or (key == "q" and state == Gdk.ModifierType.MOD1_MASK):
            self.hide()
            return True
        
        # Enter: 激活选中的第一个窗口
        elif key == "Return" or key == "KP_Enter":
            self.activate_first_visible()
            return True
        
        # Ctrl+1~9: 快捷跳转
        elif key in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            num = int(key)
            if state == Gdk.ModifierType.CONTROL_MASK:
                self.jump_to_desktop(num - 1)
                return True
        
        return False
    
    def activate_first_visible(self):
        """激活第一个可见窗口"""
        for child in self.list_box.get_children():
            if isinstance(child, Gtk.Expander) and child.get_visible():
                for sub_child in child.get_child().get_children():
                    if isinstance(sub_child, Gtk.Button) and sub_child.get_visible():
                        sub_child.emit("clicked")
                        return
    
    def jump_to_desktop(self, desktop):
        """跳转到指定桌面"""
        import subprocess
        try:
            subprocess.run(['wmctrl', '-s', str(desktop)], capture_output=True, timeout=1)
        except:
            pass
    
    def save_selection(self):
        """保存当前选择"""
        try:
            os.makedirs(os.path.dirname(LAST_FILE), exist_ok=True)
            with open(LAST_FILE, 'w') as f:
                f.write("1")  # 简化：只记录是否开机启动
        except:
            pass
    
    def restore_last_selection(self):
        """恢复上次选择"""
        pass  # 暂时跳过

def main():
    """主函数"""
    if not check_single_instance():
        sys.exit(0)
    
    # GTK 初始化检查
    if not Gtk.init_check():
        print("错误: 无法初始化 GTK。请确保在图形环境中运行。")
        print("提示: 在 RDP 环境中，请确保 DISPLAY 环境变量已设置。")
        print(f"当前 DISPLAY: {os.environ.get('DISPLAY', '未设置')}")
        print(f"当前 WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', '未设置')}")
        
        # 尝试最后一次
        print("\n尝试自动修复...")
        setup_display()
        print(f"重新设置 DISPLAY: {os.environ.get('DISPLAY', '未设置')}")
        
        if not Gtk.init_check():
            sys.exit(1)
    
    win = GroupyWindow()
    
    # 显示窗口
    win.show_all()
    
    # 尝试居中
    screen = win.get_screen()
    monitor = screen.get_primary_monitor()
    geometry = screen.get_monitor_geometry(monitor)
    x = geometry.x + (geometry.width - win.get_default_size()[0]) // 2
    y = geometry.y + (geometry.height - win.get_default_size()[1]) // 2
    win.move(x, y)
    
    print(f"✅ {APP_NAME} 已启动")
    print("快捷键: ↑↓ 导航 | Enter 跳转 | Esc 隐藏 | Super+1 启动")
    
    Gtk.main()

if __name__ == "__main__":
    main()
