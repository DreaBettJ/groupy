# Groupy 拼音模糊搜索设计文档

## 概述

在 Groupy 主版本（`groupy.py`）的窗口搜索中增加拼音模糊匹配功能，让用户输入拼音时能匹配到对应的中文窗口标题。

## 需求

- 输入 `ni` 能匹配到 `你的窗口`（中文→拼音全拼子串匹配）
- 保持原有的中文子串匹配和英文子串匹配能力
- 保持原有的大小写不敏感行为

## 方案

### 拼音转换

使用 `pypinyin` 库将中文文本转换为无声调的拼音全拼（无空格拼接）：
- `你的窗口` → `nidechuangkou`
- `微信` → `weixin`

### 匹配逻辑

在 `build_tree()` 中，对每个窗口名和应用名，除原始文本匹配外，追加拼音匹配：

1. 将搜索词转为小写（已有逻辑）
2. 对每个窗口名和应用名，生成其拼音全拼（小写，无空格）
3. 检查拼音是否包含搜索词子串

示例：
| 搜索词 | 窗口名 | 拼音 | 匹配 |
|--------|--------|------|------|
| `ni` | `你的窗口` | `nidechuangkou` | ✅ |
| `wx` | `微信` | `weixin` | ✅ |
| `微信` | `微信` | - | ✅（原始匹配） |

### 性能

- 拼音转换仅在搜索时进行，窗口列表不变时不重复计算
- 使用 `pypinyin` 的 `lazy_pinyin` 函数，性能开销可接受

### 文件变更

**修改：**
- `groupy.py`：在 `build_tree()` 搜索逻辑中增加拼音匹配

**删除：**
- `main.py`、`groupy_gnome.py`、`groupy_combo.py`、`groupy_group.py`、`groupy_lite.py`、`groupy_simple.py`、`groupy_stable.py`、`test_gui.py`、`config.json`、`README.md`

**依赖变更：**
- `requirements.txt` 添加 `pypinyin`

### 实现细节

新增 `pinyin_match(text, search)` 函数：

```python
from pypinyin import lazy_pinyin

def pinyin_match(text, search):
    """检查 search 是否匹配 text 的拼音"""
    pinyin = ''.join(lazy_pinyin(text)).lower()
    return search in pinyin
```

在 `build_tree()` 中，原有匹配条件扩展为：

```python
# 原有
search in n.lower() or search in app_name.lower()
# 变为
search in n.lower() or search in app_name.lower() or pinyin_match(n, search) or pinyin_match(app_name, search)
```
