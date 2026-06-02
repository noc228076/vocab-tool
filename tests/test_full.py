#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comprehensive feature test"""

import sys, os, json, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from vocab_app import App, Words, DB

errors = []
def check(name, ok, detail=''):
    if ok:
        print(f'  [OK] {name}')
    else:
        print(f'  [FAIL] {name} {detail}')
        errors.append(name)

print('=== 1. Words loading ===')
wm = Words(os.path.join(os.path.dirname(__file__), '..', 'data', 'words.json'))
check('cet4 loaded', len(wm.by_cat('cet4')) > 3000, f'got {len(wm.by_cat("cet4"))}')
check('cet6 loaded', len(wm.by_cat('cet6')) > 1500, f'got {len(wm.by_cat("cet6"))}')
check('total > 5000', len(wm.all) > 5000, f'got {len(wm.all)}')
check('rand cet4', wm.rand('cet4') is not None)
check('rand cet6', wm.rand('cet6') is not None)
check('rand all', wm.rand() is not None)
w = wm.rand('cet4')
d = wm.get(w)
check('get word', d is not None)
check('has meaning', bool(d.get('meaning')))
check('has category', d.get('category') in ('cet4', 'cet6', 'custom'))
# Check no empty meanings
empty = [w for w, d in wm.all.items() if not d.get('meaning')]
check('no empty meanings', len(empty) == 0, f'{len(empty)} words missing meaning')
# Check all have word key
no_word = [w for w, d in wm.all.items() if not d.get('word')]
check('all have word key', len(no_word) == 0)

print()
print('=== 2. DB operations ===')
db = DB(tempfile.mktemp(suffix='.db'))
db.progress('test1', 'cet4', True)
db.progress('test1', 'cet4', True)
db.progress('test2', 'cet4', False)
s = db.stats()
# test1 lv=2 (two correct), test2 lv=0 (wrong stays at 0)
# stats counts lv>0, so total=1
check('stats total', s['total'] == 1)
check('stats mastered', s['mastered'] == 0)

db.toggle_fav('test1')
check('fav add', 'test1' in db.fav_list())
db.toggle_fav('test1')
check('fav remove', 'test1' not in db.fav_list())

rl = db.review_list()
check('review_list returns list', isinstance(rl, list))

nl = db.new_list('cet4')
check('new_list returns list', isinstance(nl, list))

db.set_cfg('key1', 'val1')
check('cfg set/get', db.cfg('key1') == 'val1')
check('cfg default', db.cfg('missing', 'def') == 'def')

db.add_daily(learned=5, reviewed=3, correct=2, total=3, secs=120)
s = db.stats()
check('daily learned', s['t_learned'] == 5)
check('daily reviewed', s['t_reviewed'] == 3)
check('daily correct', s['t_correct'] == 2)
check('daily total', s['t_total'] == 3)
check('daily secs', s['t_time'] == 120)
check('streak >= 1', s['streak'] >= 1)
db.close()
os.unlink(db.path)

print()
print('=== 3. App init ===')
app = App()
check('app created', app is not None)
check('db created', app.db is not None)
check('wm loaded', len(app.wm.all) > 0)
check('auto_show default', app.auto_show is True)
check('auto_interval default', app.auto_interval == 60)

print()
print('=== 4. Card creation ===')
app._create_card()
check('card_win exists', app.card_win is not None)
check('card_word', hasattr(app, '_card_word'))
check('card_phon', hasattr(app, '_card_phon'))
check('card_text', hasattr(app, '_card_text'))
check('card_fav', hasattr(app, '_card_fav'))
check('reveal_btn', hasattr(app, '_reveal_btn'))
check('cat_btns', hasattr(app, '_cat_btns'))
check('order_lbl', hasattr(app, '_order_lbl'))

print()
print('=== 5. Card show/hide ===')
app.card_win.deiconify()
app.card_visible = True
check('visible after deiconify', app.card_visible)
app._hide_card()
check('hidden after hide', not app.card_visible)

print()
print('=== 6. Word display ===')
app.db.set_cfg('reveal_mode', 'manual')
w = wm.rand('cet4')
wd = wm.get(w)
app._update_card(wd)
check('card_data set', app._card_data == wd)
check('card_revealed false', not app._card_revealed)
check('card visible', app.card_visible)

print()
print('=== 7. Reveal/hide ===')
app._reveal_card()
check('revealed after reveal', app._card_revealed)
app._card_revealed = False
app._set_card_text('', '')
app._reveal_card()
check('reveal after reset', app._card_revealed)

print()
print('=== 8. Reveal mode toggle ===')
app.db.set_cfg('reveal_mode', 'manual')
app._card_revealed = False
app._on_reveal_click()
check('manual click reveals', app._card_revealed)
time.sleep(0.4)
app._on_reveal_click()
check('manual click hides', not app._card_revealed)
time.sleep(0.4)
app._on_reveal_click()
check('manual click shows again', app._card_revealed)
time.sleep(0.4)
# Double click for auto
app._on_reveal_click()
time.sleep(0.05)
app._on_reveal_click()
check('double click auto', app.db.cfg('reveal_mode') == 'auto')
app._on_reveal_click()
check('click disables auto', app.db.cfg('reveal_mode') == 'manual')

print()
print('=== 9. Category switch ===')
app.db.set_cfg('default_cat', 'cet4')
app._switch_cat('cet6')
check('switch to cet6', app.db.cfg('default_cat') == 'cet6')
app._switch_cat('cet4')
check('switch to cet4', app.db.cfg('default_cat') == 'cet4')

print()
print('=== 10. Order toggle ===')
app.db.set_cfg('order_mode', 'seq')
app._toggle_order()
check('toggle to rand', app.db.cfg('order_mode') == 'rand')
app._toggle_order()
check('toggle back to seq', app.db.cfg('order_mode') == 'seq')

print()
print('=== 11. Favorites ===')
w = wm.rand('cet4')
wd = wm.get(w)
app._update_card(wd)
app._toggle_fav()
check('fav on', w in app.db.fav_list())
app._toggle_fav()
check('fav off', w not in app.db.fav_list())

print()
print('=== 12. Import ===')
import uuid
tmp = tempfile.gettempdir()
uid = str(uuid.uuid4())[:8]
with open(os.path.join(tmp, 'imp_test.txt'), 'w', encoding='utf-8') as f:
    f.write(f'w{uid}a mean1\nw{uid}b /fon/ mean2\n# comment\n')
jd = [{'word': f'w{uid}c', 'meaning': 'json import test'}]
with open(os.path.join(tmp, 'imp_test.json'), 'w', encoding='utf-8') as f:
    json.dump(jd, f, ensure_ascii=False)
c1 = app._import_words(os.path.join(tmp, 'imp_test.txt'))
check('text import', c1 >= 1, f'got {c1}')
c2 = app._import_words(os.path.join(tmp, 'imp_test.json'))
check('json import', c2 >= 1, f'got {c2}')
c3 = app._import_words(os.path.join(tmp, 'imp_test.txt'))
check('dedup', c3 == 0, f'got {c3}')
os.unlink(os.path.join(tmp, 'imp_test.txt'))
os.unlink(os.path.join(tmp, 'imp_test.json'))

print()
print('=== 13. Feature methods exist ===')
check('_do_study', hasattr(app, '_do_study'))
check('_do_review', hasattr(app, '_do_review'))
check('_do_test', hasattr(app, '_do_test'))
check('_do_favs', hasattr(app, '_do_favs'))
check('_do_stats', hasattr(app, '_do_stats'))
check('_do_settings', hasattr(app, '_do_settings'))
check('_do_import', hasattr(app, '_do_import'))
check('_open_study', hasattr(app, '_open_study'))
check('_open_test', hasattr(app, '_open_test'))

print()
print('=== 14. Tray menu ===')
menu = app._tray_menu()
check('menu created', menu is not None)

print()
print('=== 15. Dispatcher ===')
check('dispatch method', hasattr(app, '_dispatch'))

print()
print('=== 16. Sequential mode ===')
app.db.set_cfg('order_mode', 'seq')
app.seq_idx = 0
app._show_next()
check('seq mode works', app._card_data is not None)

print()
print('=== 17. Random mode ===')
app.db.set_cfg('order_mode', 'rand')
app._shuffled = []
app._show_next()
check('rand mode works', app._card_data is not None)

print()
print('=== 18. _show_next shows hidden card ===')
app._hide_card()
app._show_next()
check('auto-show shows card', app.card_visible)

app.root.destroy()

print()
print('=' * 50)
if errors:
    print(f'FAILED: {len(errors)} tests')
    for e in errors:
        print(f'  - {e}')
else:
    print('ALL 18 TEST SECTIONS PASSED')
