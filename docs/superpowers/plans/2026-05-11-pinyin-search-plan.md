# Groupy 拼音模糊搜索实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 groupy.py 的搜索中增加拼音模糊匹配，并清理冗余文件

**Architecture:** 在 groupy.py 中新增 `pinyin_match()` 工具函数，在 `build_tree()` 的过滤逻辑中追加拼音匹配条件。项目结构精简为只保留主版本和相关支持文件。

**Tech Stack:** Python3, GTK3, pypinyin

---

### Task 1: 添加 pypinyin 依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 修改 requirements.txt 添加 pypinyin**

将文件内容改为：

```
pygobject
pypinyin
wnck
```

（移除 `gtk4`，因为该项目使用 GTK3，`gtk4` 是多余的）

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: add pypinyin dependency, remove unused gtk4 dep"
```

---

### Task 2: 实现拼音匹配功能

**Files:**
- Modify: `groupy.py:4-9`（增加 import）
- Modify: `groupy.py:346-356`（增加 pinyin_match 函数和修改搜索逻辑）

- [ ] **Step 1: 在 groupy.py 顶部增加 import**

在 `import os` 后增加：

```python
from pypinyin import lazy_pinyin
```

- [ ] **Step 2: 新增 pinyin_match 函数**

在 `class GroupyLiteWindow` 之前（`get_window_app_name` 函数之后）添加：

```python
def pinyin_match(text, search):
    """检查 search 是否匹配 text 的拼音（无声调全拼）"""
    try:
        pinyin = ''.join(lazy_pinyin(text)).lower()
        return search in pinyin
    except:
        return False
```

- [ ] **Step 3: 修改 build_tree 中的搜索逻辑**

将第 352-356 行：

```python
            if search:
                matched = [n for n in names if search in n.lower() or search in app_name.lower()]
                if not matched:
                    continue
                names = matched
```

改为：

```python
            if search:
                matched = [n for n in names if search in n.lower() or search in app_name.lower()
                           or pinyin_match(n, search) or pinyin_match(app_name, search)]
                if not matched:
                    continue
                names = matched
```

- [ ] **Step 4: 提交**

```bash
git add groupy.py
git commit -m "feat: add pinyin fuzzy matching to search"
```

---

### Task 3: 验证拼音匹配逻辑

**Files:**
- Create: `test_pinyin.py`（简单的验证脚本，运行后删除）

- [ ] **Step 1: 创建验证脚本**

创建 `test_pinyin.py`：

```python
#!/usr/bin/env python3
"""验证拼音匹配逻辑"""
from pypinyin import lazy_pinyin

def pinyin_match(text, search):
    try:
        pinyin = ''.join(lazy_pinyin(text)).lower()
        return search in pinyin
    except:
        return False

# 测试用例
assert pinyin_match("你的窗口", "ni"), "ni 应匹配 你的窗口"
assert pinyin_match("你的窗口", "nide"), "nide 应匹配 你的窗口"
assert pinyin_match("微信", "wx"), "wx 应匹配 微信"
assert pinyin_match("微信", "weixin"), "weixin 应匹配 微信"
assert pinyin_match("谷歌浏览器", "guge"), "guge 应匹配 谷歌浏览器"
assert pinyin_match("腾讯QQ", "tengxun"), "tengxun 应匹配 腾讯QQ"

# 反向：不匹配
assert not pinyin_match("你的窗口", "abc"), "abc 不应匹配 你的窗口"
assert not pinyin_match("微信", "zhifubao"), "zhifubao 不应匹配 微信"

# 原匹配仍工作
assert "ni" in "nidechuangkou", "拼音转换应正确"

print("所有测试通过！")
```

- [ ] **Step 2: 运行验证脚本**

```bash
cd /home/lijiang/code/groupy && python3 test_pinyin.py
```

Expected: `所有测试通过！`

- [ ] **Step 3: 删除验证脚本**

```bash
rm test_pinyin.py
```

- [ ] **Step 4: 验证 groupy.py 语法正确**

```bash
python3 -c "import ast; ast.parse(open('groupy.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "test: verify pinyin matching logic"
```

---

### Task 4: 清理冗余文件

**Files:**
- Delete: `main.py`, `groupy_gnome.py`, `groupy_combo.py`, `groupy_group.py`, `groupy_lite.py`, `groupy_simple.py`, `groupy_stable.py`, `test_gui.py`, `config.json`, `README.md`

- [ ] **Step 1: 删除所有冗余文件**

```bash
cd /home/lijiang/code/groupy && git rm main.py groupy_gnome.py groupy_combo.py groupy_group.py groupy_lite.py groupy_simple.py groupy_stable.py test_gui.py config.json README.md
```

- [ ] **Step 2: 提交**

```bash
git commit -m "cleanup: remove unused variant files"
```

---

### Task 5: 最终验证

- [ ] **Step 1: 验证最终文件列表**

```bash
ls /home/lijiang/code/groupy/
```

Expected: `groupy.py` `run_groupy.sh` `requirements.txt` `docs/` `.git/`

- [ ] **Step 2: 验证 Python 语法**

```bash
python3 -m py_compile groupy.py && echo "Compile OK"
```

Expected: `Compile OK`
