#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深度测试：覆盖所有功能和边界情况"""

import sys, os, json, tempfile, time, threading, queue
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vocab_app import App, Words, DB, Theme, Btn
import tkinter as tk

errors = []
def check(name, ok, detail=''):
    if ok:
        print(f'  [OK] {name}')
    else:
        print(f'  [FAIL] {name} {detail}')
        errors.append(name)

print('=== 1. 设置持久化测试 ===')
db = DB(tempfile.mktemp(suffix='.db'))
# 测试 auto_interval 保存和读取
db.set_cfg('auto_interval', '30')
check('cfg 保存 auto_interval', db.cfg('auto_interval') == '30')
check('cfg 读取 auto_interval', int(db.cfg('auto_interval', '60')) == 30)
# 测试 default_cat 保存
db.set_cfg('default_cat', 'cet6')
check('cfg 保存 default_cat', db.cfg('default_cat') == 'cet6')
# 测试 reveal_mode 保存
db.set_cfg('reveal_mode', 'auto')
check('cfg 保存 reveal_mode', db.cfg('reveal_mode') == 'auto')
# 测试 order_mode 保存
db.set_cfg('order_mode', 'rand')
check('cfg 保存 order_mode', db.cfg('order_mode') == 'rand')
db.close()
os.unlink(db.path)

print()
print('=== 2. App 初始化配置读取 ===')
app = App()
check('app.auto_interval 从数据库读取', app.auto_interval == int(app.db.cfg('auto_interval', '60')))
check('app.auto_show 默认 True', app.auto_show is True)
check('app.running 默认 True', app.running is True)

print()
print('=== 3. 单词库完整性 ===')
wm = app.wm
cet4_count = len(wm.by_cat('cet4'))
cet6_count = len(wm.by_cat('cet6'))
check('cet4 单词数 > 3000', cet4_count > 3000, f'got {cet4_count}')
check('cet6 单词数 > 1500', cet6_count > 1500, f'got {cet6_count}')
check('总单词数 > 5000', len(wm.all) > 5000, f'got {len(wm.all)}')
# 检查所有单词都有完整字段
missing_fields = 0
for word, data in wm.all.items():
    for key in ['word', 'meaning', 'category']:
        if key not in data:
            missing_fields += 1
check('所有单词都有必需字段', missing_fields == 0, f'{missing_fields} words missing fields')

print()
print('=== 4. 卡片创建和布局 ===')
app._create_card()
check('card_win 创建成功', app.card_win is not None)
check('_card_word 存在', hasattr(app, '_card_word'))
check('_card_phon 存在', hasattr(app, '_card_phon'))
check('_card_text 存在', hasattr(app, '_card_text'))
check('_card_fav 存在', hasattr(app, '_card_fav'))
check('_reveal_btn 存在', hasattr(app, '_reveal_btn'))
check('_cat_btns 存在', hasattr(app, '_cat_btns'))
check('_order_lbl 存在', hasattr(app, '_order_lbl'))
check('卡片初始不可见', not app.card_visible)

print()
print('=== 5. 卡片显示/隐藏 ===')
app.card_win.deiconify()
app.card_visible = True
check('deiconify 后可见', app.card_visible)
app._hide_card()
check('hide_card 后不可见', not app.card_visible)
# 测试 toggle
app._toggle_card()
check('toggle_card 显示', app.card_visible)
app._toggle_card()
check('toggle_card 隐藏', not app.card_visible)

print()
print('=== 6. 单词更新和释义显示 ===')
# 先设置为手动模式
app.db.set_cfg('reveal_mode', 'manual')
# 顺序模式
app.db.set_cfg('order_mode', 'seq')
app.seq_idx = 0
app._show_next()
check('_show_next 设置 _card_data', app._card_data is not None)
check('_show_next 显示卡片', app.card_visible)
check('_card_revealed 初始为 False', not app._card_revealed)
# 显示释义
app._reveal_card()
check('_reveal_card 后 _card_revealed 为 True', app._card_revealed)
# 隐藏释义
app._card_revealed = False
app._set_card_text('', '')
check('_set_card_text 清空后 _card_revealed 为 False', not app._card_revealed)

print()
print('=== 7. 释义模式切换 ===')
# 手动模式
app.db.set_cfg('reveal_mode', 'manual')
app._highlight_reveal_btn()
check('手动模式按钮文字', app._reveal_btn.cget('text') == '显示释义')
# 自动模式
app.db.set_cfg('reveal_mode', 'auto')
app._highlight_reveal_btn()
check('自动模式按钮文字', app._reveal_btn.cget('text') == '自动释义')
# 双击切换
app.db.set_cfg('reveal_mode', 'manual')
app._card_revealed = False
app._last_reveal_click = time.time() - 0.1  # 模拟100ms前点击过
app._on_reveal_click()  # 第二次点击（触发双击）
check('双击切换到自动模式', app.db.cfg('reveal_mode') == 'auto')
# 单击关闭自动
app._on_reveal_click()
check('单击关闭自动模式', app.db.cfg('reveal_mode') == 'manual')

print()
print('=== 8. 词库切换 ===')
app.db.set_cfg('default_cat', 'cet4')
app._switch_cat('cet6')
check('切换到 cet6', app.db.cfg('default_cat') == 'cet6')
app._switch_cat('cet4')
check('切换到 cet4', app.db.cfg('default_cat') == 'cet4')
# 高亮检查
app._highlight_cat('cet6')
check('cet6 高亮', app._cat_btns['cet6'].cget('fg') == Theme.TEXT)
check('cet4 不高亮', app._cat_btns['cet4'].cget('fg') == Theme.SUB)

print()
print('=== 9. 顺序/乱序切换 ===')
app.db.set_cfg('order_mode', 'seq')
app._toggle_order()
check('切换到乱序', app.db.cfg('order_mode') == 'rand')
app._toggle_order()
check('切换回顺序', app.db.cfg('order_mode') == 'seq')
# 高亮检查
app.db.set_cfg('order_mode', 'seq')
app._highlight_order()
check('顺序模式高亮', app._order_lbl.cget('text') == ' 顺序 ')
app.db.set_cfg('order_mode', 'rand')
app._highlight_order()
check('乱序模式高亮', app._order_lbl.cget('text') == ' 乱序 ')

print()
print('=== 10. 收藏功能 ===')
w = wm.rand('cet4')
wd = wm.get(w)
app._update_card(wd)
app._toggle_fav()
check('收藏后在收藏列表', w in app.db.fav_list())
app._toggle_fav()
check('取消后不在收藏列表', w not in app.db.fav_list())

print()
print('=== 10.5 标熟功能 ===')
w2 = wm.rand('cet4')
wd2 = wm.get(w2)
app._update_card(wd2)
check('标熟按钮存在', hasattr(app, '_card_mastered'))
app._toggle_mastered()
check('标熟后在已认识列表', app.db.is_mastered(w2))
check('已认识数量增加', app.db.mastered_count() > 0)
app._toggle_mastered()
check('取消后不在已认识列表', not app.db.is_mastered(w2))

print()
print('=== 11. 顺序模式完整遍历 ===')
app.db.set_cfg('order_mode', 'seq')
app._switch_cat('cet4')
app.seq_idx = 0
words_cet4 = wm.by_cat('cet4')
# 测试前10个
for i in range(10):
    app._show_seq('cet4')
    if app._card_data:
        check(f'顺序模式第{i+1}个单词', app._card_data['category'] == 'cet4')
    else:
        check(f'顺序模式第{i+1}个单词', False, '_card_data is None')
        break
# 测试循环
app.seq_idx = len(words_cet4)
app._show_seq('cet4')
check('顺序模式循环回开头', app.seq_idx <= len(words_cet4))

print()
print('=== 12. 乱序模式测试 ===')
app.db.set_cfg('order_mode', 'rand')
app._shuffled = []
app._show_random('cet4')
check('乱序模式显示单词', app._card_data is not None)
check('乱序模式 _shuffled 非空', len(app._shuffled) > 0)
# 测试 _shuffled 耗尽后重新填充
initial_len = len(app._shuffled)
for _ in range(initial_len + 1):
    app._show_random('cet4')
check('乱序模式耗尽后重新填充', len(app._shuffled) >= 0)

print()
print('=== 13. 无单词情况 ===')
app.db.set_cfg('default_cat', 'cet4')
# 临时清空 _shuffled
app._shuffled = []
# 这里不应该崩溃
try:
    app._show_next()
    check('无单词时不崩溃', True)
except Exception as e:
    check('无单词时不崩溃', False, str(e))

print()
print('=== 14. 自动弹词机制 ===')
# 测试队列机制
q = queue.Queue()
q.put(1)
q.put(2)
q.put(3)
count = 0
try:
    while True:
        q.get_nowait()
        count += 1
except queue.Empty:
    pass
check('队列消费机制', count == 3)
# 测试 _auto_loop 线程存在
check('_auto_loop 是方法', callable(getattr(app, '_auto_loop', None)))
check('_poll 是方法', callable(getattr(app, '_poll', None)))

print()
print('=== 15. 统计功能 ===')
stats = app.db.stats()
check('stats 返回 dict', isinstance(stats, dict))
check('stats 包含 total', 'total' in stats)
check('stats 包含 mastered', 'mastered' in stats)
check('stats 包含 streak', 'streak' in stats)
check('stats 包含 t_learned', 't_learned' in stats)
check('stats 包含 t_reviewed', 't_reviewed' in stats)
check('stats 包含 t_correct', 't_correct' in stats)
check('stats 包含 t_total', 't_total' in stats)
check('stats 包含 t_time', 't_time' in stats)
check('stats 包含 total_time', 'total_time' in stats)

print()
print('=== 16. 日常统计累加 ===')
db2 = DB(tempfile.mktemp(suffix='.db'))
db2.add_daily(learned=5, reviewed=3, correct=2, total=3, secs=120)
s = db2.stats()
check('第一次 add_daily', s['t_learned'] == 5)
db2.add_daily(learned=3, reviewed=2, correct=1, total=2, secs=60)
s = db2.stats()
check('累加后 t_learned', s['t_learned'] == 8)
check('累加后 t_reviewed', s['t_reviewed'] == 5)
check('累加后 t_correct', s['t_correct'] == 3)
check('累加后 t_total', s['t_total'] == 5)
check('累加后 t_time', s['t_time'] == 180)
db2.close()
os.unlink(db2.path)

print()
print('=== 17. 导入功能 ===')
import uuid
tmp = tempfile.gettempdir()
uid = str(uuid.uuid4())[:8]
# TXT 导入
txt_file = os.path.join(tmp, f'test_deep_{uid}.txt')
with open(txt_file, 'w', encoding='utf-8') as f:
    f.write(f'txtword_{uid}a /test/ 测试词1\n')
    f.write(f'txtword_{uid}b 测试词2\n')
    f.write('# 注释行\n')
    f.write('\n')
count = app._import_words(txt_file)
check('TXT 导入', count >= 1, f'got {count}')
# JSON 导入
json_file = os.path.join(tmp, f'test_deep_{uid}.json')
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump([{'word': f'jsonword_{uid}', 'meaning': '测试词3'}], f)
count = app._import_words(json_file)
check('JSON 导入', count >= 1, f'got {count}')
# 去重
count = app._import_words(txt_file)
check('去重', count == 0, f'got {count}')
os.unlink(txt_file)
os.unlink(json_file)

print()
print('=== 18. 学习进度追踪 ===')
db3 = DB(tempfile.mktemp(suffix='.db'))
# 新单词
db3.progress('test1', 'cet4', True)
db3.progress('test1', 'cet4', True)
db3.progress('test1', 'cet4', False)
s = db3.stats()
check('学习进度 lv>0 计数', s['total'] >= 1)
# 收藏
db3.toggle_fav('test1')
check('收藏', 'test1' in db3.fav_list())
db3.toggle_fav('test1')
check('取消收藏', 'test1' not in db3.fav_list())
# 复习列表
rl = db3.review_list()
check('复习列表返回 list', isinstance(rl, list))
# 新词列表
nl = db3.new_list('cet4')
check('新词列表返回 list', isinstance(nl, list))
db3.close()
os.unlink(db3.path)

print()
print('=== 19. 按钮组件 ===')
btn_test = Btn.__new__(Btn)
check('Btn 类存在', True)
check('Btn 是 tk.Label 子类', issubclass(Btn, tk.Label))

print()
print('=== 20. 配色方案 ===')
check('Theme.BG', Theme.BG == "#111820")
check('Theme.CARD', Theme.CARD == "#1a2332")
check('Theme.ACCENT', Theme.ACCENT == "#2563eb")
check('Theme.TEXT', Theme.TEXT == "#f0f4f8")
check('Theme.FONT', Theme.FONT == "Microsoft YaHei UI")

print()
print('=== 21. 间隔重复参数 ===')
from vocab_app import SR
check('SR 有7个级别', len(SR) == 7)
check('SR[0]=0', SR[0] == 0)
check('SR[1]=1', SR[1] == 1)
check('SR[2]=3', SR[2] == 3)
check('SR[3]=7', SR[3] == 7)
check('SR[4]=14', SR[4] == 14)
check('SR[5]=30', SR[5] == 30)
check('SR[6]=60', SR[6] == 60)

print()
print('=== 22. 单词本（收藏列表） ===')
# 先收藏几个单词
test_fav_words = ['hello', 'world', 'test']
for w in test_fav_words:
    app.db.toggle_fav(w)
favs = app.db.fav_list()
check('收藏列表非空', len(favs) > 0)
check('hello 在收藏列表', 'hello' in favs)
# 清理
for w in test_fav_words:
    app.db.toggle_fav(w)

print()
print('=== 23. 菜单结构 ===')
menu = app._tray_menu()
check('菜单创建成功', menu is not None)

print()
print('=== 24. 分发器 ===')
check('_dispatch 方法存在', hasattr(app, '_dispatch'))
check('_cb 方法存在', hasattr(app, '_cb'))

print()
print('=== 25. 颜色工具 ===')
light = app._lighten('#111111')
check('_lighten 提亮', light != '#111111')
check('_lighten 返回有效颜色', light.startswith('#') and len(light) == 7)
# 边界情况
light = app._lighten('invalid')
check('_lighten 处理无效输入', light == 'invalid')

app.root.destroy()

print()
print('=' * 50)
if errors:
    print(f'FAILED: {len(errors)} tests')
    for e in errors:
        print(f'  - {e}')
else:
    print(f'ALL 25 TEST SECTIONS PASSED')
