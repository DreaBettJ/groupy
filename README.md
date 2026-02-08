# Groupy

窗口标签化管理工具 - 类似 Windows Groupy 的 Linux 实现

## 功能

- 🏷️ 窗口标签化 - 将多个应用窗口分组到标签页中
- ✅ 白名单机制 - 只对指定应用进行标签化处理
- ⚙️ GUI 配置 - 简单设置界面，支持"添加当前窗口"
- 📍 顶部标签栏 - 默认标签显示在屏幕顶部
- ⌨️ 快捷键支持
  - `Ctrl+N` - 新建分组
  - `Ctrl+1~9` - 切换标签页

## 安装依赖

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-wnck-3.0 libgtk-4-dev

# Fedora
sudo dnf install python3-gobject gtk4 libwnck3
```

## 使用方法

```bash
# 运行 Groupy
python3 /home/lijiang/code/groupy/main.py

# 或从应用菜单启动（需要重新登录）
```

## 配置

配置文件位置: `~/.config/groupy/config.json`

```json
{
  "whitelist": ["WeChat", "Spotify", "Terminal"],
  "tab_position": "top"
}
```

## 添加白名单

1. 点击右上角 ⚙️ 按钮
2. 在输入框中添加应用名称（逗号分隔）
3. 或点击「➕ 添加当前窗口」快速添加活动窗口
4. 点击 💾 保存

## 快捷键

| 快捷键 | 功能 |
|-------|------|
| `Ctrl+N` | 新建分组 |
| `Ctrl+1~9` | 切换到对应标签页 |

## 项目结构

```
groupy/
├── main.py              # 主程序
├── config.json          # 配置文件 (~/.config/groupy/)
├── requirements.txt     # Python 依赖
└── README.md            # 文档
```

## 当前已知问题

- XEmbed 窗口嵌入在 Wayland 下不可用（显示为占位符）
- 部分应用可能不支持窗口嵌入
- X11 环境窗口嵌入效果最佳
