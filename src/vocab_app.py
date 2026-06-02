#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
四六级背单词小工具
"""

import json, os, sys, time, random, sqlite3, threading, queue, re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from pathlib import Path
import pystray
from PIL import Image, ImageDraw

APP_NAME = "四六级背单词"
DB_NAME = "vocab_progress.db"
WORDS_FILE = "words.json"
SR = {0:0, 1:1, 2:3, 3:7, 4:14, 5:30, 6:60}

# ============================================================
# 配色
# ============================================================
class Theme:
    BG = "#111820"
    CARD = "#1a2332"
    BORDER = "#2a3a4e"
    ACCENT = "#2563eb"
    ACCENT_H = "#3b82f6"
    TEXT = "#f0f4f8"
    SUB = "#7b8da0"
    RED = "#ef4444"
    ORANGE = "#f59e0b"
    GREEN = "#22c55e"
    BLUE = "#38bdf8"
    PURPLE = "#a78bfa"
    HOVER = "#1e2d3d"
    FONT = "Microsoft YaHei UI"
    FONT_MONO = "Cascadia Code"
    FONT_PHON = "Segoe UI"

# ============================================================
# 数据库
# ============================================================
class DB:
    def __init__(self, path):
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._init()

    def _init(self):
        self._conn.executescript('''CREATE TABLE IF NOT EXISTS word_progress (
            word TEXT PRIMARY KEY, cat TEXT, lv INTEGER DEFAULT 0,
            next_r TEXT, last_r TEXT, ok INTEGER DEFAULT 0, ng INTEGER DEFAULT 0, fav INTEGER DEFAULT 0, mastered INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS daily (
                d TEXT PRIMARY KEY, learned INTEGER DEFAULT 0, reviewed INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0, total INTEGER DEFAULT 0, secs INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS cfg (k TEXT PRIMARY KEY, v TEXT);''')
        # 迁移：补齐旧表缺失的列
        cols = {r[1] for r in self._conn.execute('PRAGMA table_info(word_progress)').fetchall()}
        for name, typ in [('cat','TEXT'),('lv','INTEGER'),('next_r','TEXT'),('last_r','TEXT'),
                          ('ok','INTEGER'),('ng','INTEGER'),('fav','INTEGER'),('mastered','INTEGER')]:
            if name not in cols:
                self._conn.execute(f'ALTER TABLE word_progress ADD COLUMN {name} {typ} DEFAULT 0')

    def _c(self): return self._conn

    def progress(self, w, cat, ok):
        """记录学习进度。ok=True 认识, ok=None 模糊, ok=False 不认识"""
        c = self._c()
        now = datetime.now().isoformat()
        row = c.execute('SELECT lv,ok,ng FROM word_progress WHERE word=?', (w,)).fetchone()
        if row:
            if ok is None:
                lv = row[0]  # 模糊：等级不变
            else:
                lv = min(row[0]+1,6) if ok else max(row[0]-1,0)
            nr = (datetime.now()+timedelta(days=SR[lv])).isoformat()
            ok_inc = 1 if ok is True else 0
            ng_inc = 1 if ok is False else 0
            c.execute('UPDATE word_progress SET lv=?,next_r=?,last_r=?,ok=ok+?,ng=ng+? WHERE word=?',
                      (lv, nr, now, ok_inc, ng_inc, w))
        else:
            lv = 1 if ok is True else 0
            nr = (datetime.now()+timedelta(days=SR[lv])).isoformat()
            c.execute('INSERT INTO word_progress(word,cat,lv,next_r,last_r,ok,ng,fav) VALUES(?,?,?,?,?,?,?,0)',
                      (w, cat, lv, nr, now, 1 if ok is True else 0, 1 if ok is False else 0))

    def review_list(self, cat=None, n=20):
        c = self._c()
        now = datetime.now().isoformat()
        if cat:
            return [r[0] for r in c.execute('SELECT word FROM word_progress WHERE cat=? AND next_r<=? ORDER BY next_r LIMIT ?',(cat,now,n))]
        return [r[0] for r in c.execute('SELECT word FROM word_progress WHERE next_r<=? ORDER BY next_r LIMIT ?',(now,n))]

    def new_list(self, cat, n=10):
        c = self._c()
        return [r[0] for r in c.execute('SELECT word FROM word_progress WHERE cat=? AND lv=0 LIMIT ?',(cat,n))]

    def stats(self):
        c = self._c()
        tl = c.execute('SELECT COUNT(*) FROM word_progress WHERE lv>0').fetchone()[0]
        ma = c.execute('SELECT COUNT(*) FROM word_progress WHERE lv>=4').fetchone()[0]
        today = datetime.now().strftime('%Y-%m-%d')
        ts = c.execute('SELECT * FROM daily WHERE d=?',(today,)).fetchone() or (today,0,0,0,0,0)
        tt = c.execute('SELECT COALESCE(SUM(secs),0) FROM daily').fetchone()[0]
        dates = [r[0] for r in c.execute('SELECT DISTINCT d FROM daily ORDER BY d DESC')]
        streak = 0
        cd = datetime.now().date()
        for ds in dates:
            d = datetime.strptime(ds,'%Y-%m-%d').date()
            if d == cd or d == cd - timedelta(days=1):
                streak += 1; cd = d
            else: break
        return dict(total=tl, mastered=ma, t_learned=ts[1], t_reviewed=ts[2],
                    t_correct=ts[3], t_total=ts[4], t_time=ts[5], total_time=tt, streak=streak)

    def add_daily(self, learned=0, reviewed=0, correct=0, total=0, secs=0):
        c = self._c()
        today = datetime.now().strftime('%Y-%m-%d')
        if c.execute('SELECT 1 FROM daily WHERE d=?',(today,)).fetchone():
            c.execute('UPDATE daily SET learned=learned+?,reviewed=reviewed+?,correct=correct+?,total=total+?,secs=secs+? WHERE d=?',
                      (learned,reviewed,correct,total,secs,today))
        else:
            c.execute('INSERT INTO daily VALUES(?,?,?,?,?,?)',(today,learned,reviewed,correct,total,secs))

    def toggle_fav(self, w):
        c = self._c()
        row = c.execute('SELECT fav FROM word_progress WHERE word=?',(w,)).fetchone()
        if row:
            c.execute('UPDATE word_progress SET fav=? WHERE word=?', (0 if row[0] else 1, w))
        else:
            c.execute('INSERT INTO word_progress (word,fav) VALUES(?,1)', (w,))

    def fav_list(self):
        c = self._c()
        return [r[0] for r in c.execute('SELECT word FROM word_progress WHERE fav=1')]

    def toggle_mastered(self, w):
        """标记/取消标记单词为已认识"""
        c = self._c()
        row = c.execute('SELECT mastered FROM word_progress WHERE word=?',(w,)).fetchone()
        if row:
            c.execute('UPDATE word_progress SET mastered=? WHERE word=?', (0 if row[0] else 1, w))
        else:
            c.execute('INSERT INTO word_progress (word,mastered) VALUES(?,1)', (w,))

    def mastered_list(self):
        """获取已认识的单词列表"""
        c = self._c()
        return [r[0] for r in c.execute('SELECT word FROM word_progress WHERE mastered=1')]

    def is_mastered(self, w):
        """检查单词是否已认识"""
        c = self._c()
        row = c.execute('SELECT mastered FROM word_progress WHERE word=?',(w,)).fetchone()
        return row and row[0] == 1

    def mastered_count(self):
        """获取已认识单词数量"""
        c = self._c()
        return c.execute('SELECT COUNT(*) FROM word_progress WHERE mastered=1').fetchone()[0]

    def cfg(self, k, d=None):
        c = self._c()
        r = c.execute('SELECT v FROM cfg WHERE k=?',(k,)).fetchone()
        return r[0] if r else d

    def set_cfg(self, k, v):
        c = self._c()
        c.execute('INSERT OR REPLACE INTO cfg VALUES(?,?)',(k,str(v)))

    def close(self):
        """关闭数据库连接"""
        self._conn.close()

# ============================================================
# 单词管理
# ============================================================
class Words:
    def __init__(self, path):
        self.all = {}
        self.path = path
        try:
            with open(path,'r',encoding='utf-8') as f:
                data = json.load(f)
            # 去重并加载
            seen = set()
            for cat, words in data.items():
                unique = []
                for w in words:
                    if isinstance(w, dict) and 'word' in w:
                        key = w['word'].lower()
                        if key not in seen:
                            seen.add(key)
                            w['category'] = cat
                            self.all[w['word']] = w
                            unique.append(w)
                data[cat] = unique
            # 回写去重后的文件
            with open(path,'w',encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Words] 加载词库失败: {e}", file=sys.stderr)

    def get(self, w): return self.all.get(w)
    def rand(self, cat=None):
        pool = [w for w,d in self.all.items() if d['category']==cat] if cat else list(self.all.keys())
        return random.choice(pool) if pool else None
    def by_cat(self, cat): return [w for w,d in self.all.items() if d['category']==cat]

# ============================================================
# 通用按钮
# ============================================================
class Btn(tk.Label):
    def __init__(self, master, text, color=Theme.ACCENT, hover=Theme.ACCENT_H, cmd=None, **kw):
        super().__init__(master, text=text, font=(Theme.FONT, 11), fg=Theme.TEXT,
                         bg=color, cursor="hand2", padx=14, pady=6, **kw)
        self._bg = color; self._hover = hover; self._cmd = cmd
        self.bind('<Enter>', lambda e: self.config(bg=self._hover))
        self.bind('<Leave>', lambda e: self.config(bg=self._bg))
        if cmd: self.bind('<Button-1>', lambda e: cmd())

# ============================================================
# 主程序
# ============================================================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        # PyInstaller 单文件模式判定
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(os.path.dirname(sys.executable))
            self.resource_dir = Path(sys._MEIPASS)
        else:
            self.app_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.resource_dir = self.app_dir
        self.db = DB(str(self.app_dir / DB_NAME))
        self.wm = Words(str(self.resource_dir / "data" / WORDS_FILE))
        self.icon = None
        self.running = True
        self.auto_show = True
        self.auto_interval = int(self.db.cfg('auto_interval', '60'))
        self.auto_q = queue.Queue()
        # 常驻浮动卡片
        self.card_win = None
        self.card_visible = False
        self.seq_idx = 0
        self._shuffled = []

    # ---- 托盘 ----
    def _tray_img(self):
        img = Image.new('RGBA',(64,64),(0,0,0,0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([4,4,60,60], radius=12, fill=Theme.ACCENT)
        d.text((18,12), "词", fill='white')
        return img

    def _tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem("显示/隐藏卡片", self._cb_toggle_card),
            pystray.MenuItem("学习", pystray.Menu(
                pystray.MenuItem("四级词汇", lambda: self._cb('study','cet4')),
                pystray.MenuItem("六级词汇", lambda: self._cb('study','cet6')),
                pystray.MenuItem("混合模式", lambda: self._cb('study','mixed')),
            )),
            pystray.MenuItem("复习", lambda: self._cb('review',None)),
            pystray.MenuItem("测试", pystray.Menu(
                pystray.MenuItem("英译中", lambda: self._cb('test','en_cn')),
                pystray.MenuItem("中译英", lambda: self._cb('test','cn_en')),
            )),
            pystray.MenuItem("导入单词书", lambda: self._cb('import',None)),
            pystray.MenuItem("单词本", pystray.Menu(
                pystray.MenuItem("收藏的单词", lambda: self._cb('favs',None)),
                pystray.MenuItem("已认识的单词", lambda: self._cb('mastered',None)),
            )),
            pystray.MenuItem("学习统计", lambda: self._cb('stats',None)),
            pystray.MenuItem("设置", lambda: self._cb('settings',None)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("自动弹词", self._cb_auto_toggle, checked=lambda i: self.auto_show),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._cb_quit),
        )

    def _cb(self, action, arg):
        self.root.after(0, lambda: self._dispatch(action, arg))

    def _cb_toggle_card(self, *a):
        self.root.after(0, self._toggle_card)

    def _cb_auto_toggle(self, *a):
        self.auto_show = not self.auto_show
        if self.auto_show:
            self.root.after(0, self._show_next)

    def _cb_quit(self, *a):
        self.running = False
        self.icon.stop()
        self.root.after(0, self.root.quit)

    def _dispatch(self, action, arg):
        if action == 'study': self._do_study(arg)
        elif action == 'review': self._do_review()
        elif action == 'test': self._do_test(arg)
        elif action == 'favs': self._do_favs()
        elif action == 'mastered': self._do_mastered()
        elif action == 'stats': self._do_stats()
        elif action == 'settings': self._do_settings()
        elif action == 'import': self._do_import()

    # ---- 启动 ----
    def run(self):
        self.icon = pystray.Icon(APP_NAME, self._tray_img(), APP_NAME, self._tray_menu())
        threading.Thread(target=self.icon.run, daemon=True).start()
        threading.Thread(target=self._auto_loop, daemon=True).start()
        self.root.after(200, self._poll)
        self._create_card()
        self.root.mainloop()

    def _auto_loop(self):
        while self.running:
            try:
                if self.auto_show: self.auto_q.put(1)
                time.sleep(self.auto_interval)
            except Exception:
                time.sleep(1)

    def _poll(self):
        try:
            while True:
                self.auto_q.get_nowait()
                try:
                    self._show_next()
                except Exception:
                    pass
        except queue.Empty: pass
        if self.running: self.root.after(200, self._poll)

    # ============================================================
    # 常驻浮动卡片（不销毁，只更新内容）
    # ============================================================
    def _create_card(self):
        win = tk.Toplevel(self.root)
        self.card_win = win
        win.title(APP_NAME)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.attributes('-alpha', 0.95)
        win.configure(bg=Theme.BORDER)

        # 外层边框
        outer = tk.Frame(win, bg=Theme.BORDER, padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)

        # 主容器
        body = tk.Frame(outer, bg=Theme.BG)
        body.pack(fill=tk.BOTH, expand=True)

        # 标题栏（可拖拽）
        bar = tk.Frame(body, bg=Theme.CARD, height=36)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        title_lbl = tk.Label(bar, text="  四六级背单词", font=(Theme.FONT, 10, 'bold'),
                             fg=Theme.SUB, bg=Theme.CARD, anchor='w')
        title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        close_btn = tk.Label(bar, text=" × ", font=(Theme.FONT, 12), fg=Theme.SUB,
                             bg=Theme.CARD, cursor="hand2", padx=6)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self._hide_card())
        close_btn.bind('<Enter>', lambda e: close_btn.config(fg=Theme.RED))
        close_btn.bind('<Leave>', lambda e: close_btn.config(fg=Theme.SUB))

        for w in (bar, title_lbl):
            w.bind('<Button-1>', self._drag_start)
            w.bind('<B1-Motion>', self._drag_move)

        # 底部按钮栏（先 pack）
        btns = tk.Frame(body, bg=Theme.CARD)
        btns.pack(fill=tk.X, side=tk.BOTTOM)

        # 上排：操作按钮
        act_row = tk.Frame(btns, bg=Theme.CARD)
        act_row.pack(fill=tk.X, padx=8, pady=(8,4))

        self._card_fav = tk.Label(act_row, text="☆ 收藏", font=(Theme.FONT, 12),
                                  fg=Theme.SUB, bg=Theme.HOVER, cursor="hand2",
                                  padx=10, pady=6)
        self._card_fav.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self._card_fav.bind('<Button-1>', self._toggle_fav)
        self._card_fav.bind('<Enter>', lambda e: self._card_fav.config(bg=Theme.BORDER))
        self._card_fav.bind('<Leave>', lambda e: self._card_fav.config(bg=Theme.HOVER))

        self._card_mastered = tk.Label(act_row, text="○ 标熟", font=(Theme.FONT, 12),
                                       fg=Theme.SUB, bg=Theme.HOVER, cursor="hand2",
                                       padx=10, pady=6)
        self._card_mastered.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self._card_mastered.bind('<Button-1>', self._toggle_mastered)
        self._card_mastered.bind('<Enter>', lambda e: self._card_mastered.config(bg=Theme.BORDER))
        self._card_mastered.bind('<Leave>', lambda e: self._card_mastered.config(bg=Theme.HOVER))

        self._reveal_btn = tk.Label(act_row, text="显示释义", font=(Theme.FONT, 12, 'bold'),
                                    fg=Theme.TEXT, bg=Theme.ACCENT, cursor="hand2",
                                    padx=10, pady=6)
        self._reveal_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self._reveal_btn.bind('<Button-1>', lambda e: self._on_reveal_click())
        self._reveal_btn.bind('<Enter>', lambda e: self._reveal_btn.config(bg=Theme.ACCENT_H))
        self._reveal_btn.bind('<Leave>', lambda e: self._highlight_reveal_btn())

        next_btn = tk.Label(act_row, text="下一个", font=(Theme.FONT, 12, 'bold'),
                            fg=Theme.TEXT, bg=Theme.ACCENT, cursor="hand2",
                            padx=10, pady=6)
        next_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        next_btn.bind('<Button-1>', lambda e: self._show_next())
        next_btn.bind('<Enter>', lambda e: next_btn.config(bg=Theme.ACCENT_H))
        next_btn.bind('<Leave>', lambda e: next_btn.config(bg=Theme.ACCENT))

        # 下排：词库/模式切换
        ctrl_row = tk.Frame(btns, bg=Theme.CARD)
        ctrl_row.pack(fill=tk.X, padx=8, pady=(4,8))

        self._cat_btns = {}
        for c in ('cet4','cet6'):
            lbl = tk.Label(ctrl_row, text=c.upper().replace('CET','CET-'),
                           font=(Theme.FONT, 11), fg=Theme.SUB, bg=Theme.HOVER,
                           cursor="hand2", padx=12, pady=6)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            lbl.bind('<Button-1>', lambda e, cat=c: self._switch_cat(cat))
            lbl.bind('<Enter>', lambda e, l=lbl: l.config(bg=Theme.BORDER))
            lbl.bind('<Leave>', lambda e, l=lbl: l.config(bg=Theme.HOVER))
            self._cat_btns[c] = lbl

        self._order_lbl = tk.Label(ctrl_row, text="顺序", font=(Theme.FONT, 11),
                                   fg=Theme.SUB, bg=Theme.HOVER, cursor="hand2",
                                   padx=12, pady=6)
        self._order_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self._order_lbl.bind('<Button-1>', lambda e: self._toggle_order())
        self._order_lbl.bind('<Enter>', lambda e: self._order_lbl.config(bg=Theme.BORDER))
        self._order_lbl.bind('<Leave>', lambda e: self._order_lbl.config(bg=Theme.HOVER))

        # 内容区
        content = tk.Frame(body, bg=Theme.BG, padx=24, pady=12)
        content.pack(fill=tk.BOTH, expand=True)

        self._card_word = tk.Label(content, text="", font=(Theme.FONT, 26, 'bold'),
                                   fg=Theme.TEXT, bg=Theme.BG, anchor='w')
        self._card_word.pack(anchor='w')

        self._card_phon = tk.Label(content, text="", font=(Theme.FONT_PHON, 12),
                                   fg=Theme.SUB, bg=Theme.BG, anchor='w')
        self._card_phon.pack(anchor='w', pady=(2, 0))

        sep = tk.Frame(content, bg=Theme.BORDER, height=1)
        sep.pack(fill=tk.X, pady=8)

        self._card_text = tk.Text(content, font=(Theme.FONT, 12), fg=Theme.TEXT, bg=Theme.BG,
                                  relief=tk.FLAT, height=5, wrap=tk.WORD, highlightthickness=0,
                                  state=tk.DISABLED, cursor="arrow")
        self._card_text.pack(fill=tk.BOTH, expand=True)
        self._card_text.tag_configure('mean', foreground=Theme.BLUE, font=(Theme.FONT, 13))
        self._card_text.tag_configure('exam', foreground=Theme.SUB, font=(Theme.FONT, 10))
        self._card_text.tag_configure('word_highlight', foreground=Theme.ORANGE, font=(Theme.FONT, 10, 'bold'))

        # 当前单词数据
        self._card_data = None
        self._card_revealed = False

        # 应用保存的透明度
        saved_alpha = self.db.cfg('window_alpha', '0.95')
        try: win.attributes('-alpha', float(saved_alpha))
        except: pass

        # 位置：记录过则恢复，否则右下角
        cx = self.db.cfg('card_x')
        cy = self.db.cfg('card_y')
        if cx and cy:
            win.geometry(f"420x360+{cx}+{cy}")
        else:
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"420x360+{sw-440}+{sh-420}")
        self._drag_x = 0; self._drag_y = 0

    def _drag_start(self, e):
        self._drag_x = e.x; self._drag_y = e.y

    def _drag_move(self, e):
        x = self.card_win.winfo_x() + e.x - self._drag_x
        y = self.card_win.winfo_y() + e.y - self._drag_y
        self.card_win.geometry(f"+{x}+{y}")
        # 保存位置
        self.db.set_cfg('card_x', str(x))
        self.db.set_cfg('card_y', str(y))

    def _toggle_card(self):
        if self.card_visible: self._hide_card()
        else:
            self.card_win.deiconify()
            self.card_visible = True
            self._highlight_reveal_btn()
            self._show_next()

    def _hide_card(self):
        self.card_win.withdraw()
        self.card_visible = False

    def _show_next(self):
        cat = self.db.cfg('default_cat', 'cet4')
        self._highlight_cat(cat)
        self._highlight_order()
        self._highlight_reveal_btn()
        mode = self.db.cfg('order_mode', 'seq')
        if mode == 'seq':
            self._show_seq(cat)
        else:
            self._show_random(cat)
        # 自动弹词：卡片隐藏时显示
        if not self.card_visible:
            self.card_win.deiconify()
            self.card_visible = True

    def _show_random(self, cat):
        if not self._shuffled:
            pool = self.wm.by_cat(cat)
            if not pool:
                self._no_word_msg(cat); return
            self._shuffled = pool[:]
            random.shuffle(self._shuffled)
        w = self._shuffled.pop()
        self._update_card(self.wm.get(w))

    def _show_seq(self, cat):
        words = self.wm.by_cat(cat)
        if not words:
            self._no_word_msg(cat); return
        if self.seq_idx >= len(words):
            self.seq_idx = 0
        self._update_card(self.wm.get(words[self.seq_idx]))
        self.seq_idx += 1

    def _no_word_msg(self, cat):
        self._card_word.config(text="暂无单词")
        self._card_phon.config(text="")
        self._set_card_text(f"当前词库 {cat.upper()} 暂无可用单词\n请切换词库或补充词汇", '')

    def _toggle_order(self):
        cur = self.db.cfg('order_mode', 'seq')
        new = 'rand' if cur == 'seq' else 'seq'
        self.db.set_cfg('order_mode', new)
        self.seq_idx = 0
        self._shuffled = []
        self._highlight_order()
        self._show_next()

    def _on_reveal_click(self):
        now = time.time()
        auto = self.db.cfg('reveal_mode', 'manual') == 'auto'
        # 已经是自动模式 → 关闭
        if auto:
            self.db.set_cfg('reveal_mode', 'manual')
            self._highlight_reveal_btn()
            return
        # 双击检测（300ms 内两次点击）→ 开启自动
        if hasattr(self, '_last_reveal_click') and now - self._last_reveal_click < 0.3:
            self.db.set_cfg('reveal_mode', 'auto')
            self._highlight_reveal_btn()
            self._reveal_card()
            self._last_reveal_click = 0
            return
        self._last_reveal_click = now
        # 单击：已显示则隐藏，未显示则显示
        if self._card_revealed:
            self._set_card_text('', '')
            self._card_revealed = False
        else:
            self._reveal_card()

    def _highlight_reveal_btn(self):
        auto = self.db.cfg('reveal_mode', 'manual') == 'auto'
        if auto:
            self._reveal_btn.config(text="自动释义", fg=Theme.TEXT, bg=Theme.GREEN)
        else:
            self._reveal_btn.config(text="显示释义", fg=Theme.TEXT, bg=Theme.ACCENT)

    def _highlight_order(self):
        mode = self.db.cfg('order_mode', 'seq')
        if mode == 'seq':
            self._order_lbl.config(text=" 顺序 ", fg=Theme.TEXT, bg=Theme.ACCENT)
        else:
            self._order_lbl.config(text=" 乱序 ", fg=Theme.TEXT, bg=Theme.PURPLE)

    def _switch_cat(self, cat):
        self.db.set_cfg('default_cat', cat)
        self.seq_idx = 0
        self._shuffled = []
        self._highlight_cat(cat)
        self._show_next()

    def _highlight_cat(self, cat):
        for c, lbl in self._cat_btns.items():
            if c == cat:
                lbl.config(fg=Theme.TEXT, bg=Theme.ACCENT)
            else:
                lbl.config(fg=Theme.SUB, bg=Theme.CARD)

    def _set_card_text(self, meaning, example, word=''):
        self._card_text.config(state=tk.NORMAL)
        self._card_text.delete('1.0', tk.END)
        if meaning:
            self._card_text.insert(tk.END, meaning + '\n', 'mean')
        if example:
            if word:
                # 在例句中高亮显示单词
                self._insert_highlighted_example(example, word)
            else:
                self._card_text.insert(tk.END, example, 'exam')
        self._card_text.config(state=tk.DISABLED)

    def _insert_highlighted_example(self, example, word):
        """在例句中高亮显示单词（支持词形变化）"""
        # 生成词形变化匹配模式
        patterns = self._get_word_patterns(word)
        # 合并所有模式
        combined_pattern = '|'.join(patterns)
        regex = re.compile(combined_pattern, re.IGNORECASE)
        
        last_end = 0
        for match in regex.finditer(example):
            # 插入匹配前的文本
            start, end = match.span()
            if start > last_end:
                self._card_text.insert(tk.END, example[last_end:start], 'exam')
            # 插入高亮的单词
            self._card_text.insert(tk.END, match.group(), 'word_highlight')
            last_end = end
        # 插入剩余的文本
        if last_end < len(example):
            self._card_text.insert(tk.END, example[last_end:], 'exam')

    def _get_word_patterns(self, word):
        """生成单词的各种词形变化模式"""
        word_lower = word.lower()
        
        # 从原形推导变形形式
        forms = set()
        forms.add(word_lower)
        
        # 处理特殊变形（不规则动词）
        special_forms = {
            'be': ['is', 'are', 'am', 'was', 'were', 'been', 'being'],
            'have': ['has', 'had', 'having'],
            'do': ['does', 'did', 'doing', 'done'],
            'go': ['goes', 'went', 'gone', 'going'],
            'fly': ['flies', 'flew', 'flown', 'flying'],
            'run': ['runs', 'ran', 'running'],
            'eat': ['eats', 'ate', 'eaten', 'eating'],
            'see': ['sees', 'saw', 'seen', 'seeing'],
            'come': ['comes', 'came', 'coming'],
            'take': ['takes', 'took', 'taken', 'taking'],
            'give': ['gives', 'gave', 'given', 'giving'],
            'make': ['makes', 'made', 'making'],
            'know': ['knows', 'knew', 'known', 'knowing'],
            'think': ['thinks', 'thought', 'thinking'],
            'say': ['says', 'said', 'saying'],
            'get': ['gets', 'got', 'gotten', 'getting'],
            'find': ['finds', 'found', 'finding'],
            'tell': ['tells', 'told', 'telling'],
            'become': ['becomes', 'became', 'becoming'],
            'leave': ['leaves', 'left', 'leaving'],
            'feel': ['feels', 'felt', 'feeling'],
            'bring': ['brings', 'brought', 'bringing'],
            'begin': ['begins', 'began', 'begun', 'beginning'],
            'keep': ['keeps', 'kept', 'keeping'],
            'hold': ['holds', 'held', 'holding'],
            'write': ['writes', 'wrote', 'written', 'writing'],
            'stand': ['stands', 'stood', 'standing'],
            'hear': ['hears', 'heard', 'hearing'],
            'let': ['lets', 'letting'],
            'mean': ['means', 'meant', 'meaning'],
            'set': ['sets', 'setting'],
            'meet': ['meets', 'met', 'meeting'],
            'pay': ['pays', 'paid', 'paying'],
            'sit': ['sits', 'sat', 'sitting'],
            'speak': ['speaks', 'spoke', 'spoken', 'speaking'],
            'lie': ['lies', 'lay', 'lain', 'lying'],
            'lead': ['leads', 'led', 'leading'],
            'grow': ['grows', 'grew', 'grown', 'growing'],
            'lose': ['loses', 'lost', 'losing'],
            'fall': ['falls', 'fell', 'fallen', 'falling'],
            'send': ['sends', 'sent', 'sending'],
            'build': ['builds', 'built', 'building'],
            'understand': ['understands', 'understood', 'understanding'],
            'draw': ['draws', 'drew', 'drawn', 'drawing'],
            'break': ['breaks', 'broke', 'broken', 'breaking'],
            'spend': ['spends', 'spent', 'spending'],
            'cut': ['cuts', 'cutting'],
            'rise': ['rises', 'rose', 'risen', 'rising'],
            'drive': ['drives', 'drove', 'driven', 'driving'],
            'sell': ['sells', 'sold', 'selling'],
            'choose': ['chooses', 'chose', 'chosen', 'choosing'],
            'wear': ['wears', 'wore', 'worn', 'wearing'],
        }
        
        if word_lower in special_forms:
            for form in special_forms[word_lower]:
                forms.add(form)
        else:
            # 规则变化
            
            # 以 e 结尾：直接加 d, ing
            if word_lower.endswith('e'):
                forms.add(word_lower + 'd')   # like -> liked
                forms.add(word_lower[:-1] + 'ing') # like -> liking
            else:
                forms.add(word_lower + 'ed')   # walk -> walked
                forms.add(word_lower + 'ing')  # walk -> walking
            
            # 以辅音+y结尾：变y为i加es/ed
            if len(word_lower) >= 2 and word_lower[-1] == 'y' and word_lower[-2] not in 'aeiou':
                stem = word_lower[:-1]
                forms.add(stem + 'ies') # study -> studies
                forms.add(stem + 'ied') # study -> studied
            
            # 以 s, x, z, ch, sh 结尾：加 es
            if word_lower.endswith(('s', 'x', 'z', 'ch', 'sh')):
                forms.add(word_lower + 'es') # watch -> watches
            
            # 名词复数
            forms.add(word_lower + 's') # cat -> cats
            
            # 以辅音+元音+辅音结尾的短词：双写末字母加 ed/ing/er
            if len(word_lower) >= 3:
                last3 = word_lower[-3:]
                if (last3[0] not in 'aeiou' and last3[1] in 'aeiou' and last3[2] not in 'aeiouwxy'):
                    forms.add(word_lower + word_lower[-1] + 'ed')   # stop -> stopped
                    forms.add(word_lower + word_lower[-1] + 'ing')  # stop -> stopping
                    forms.add(word_lower + word_lower[-1] + 'er')   # big -> bigger
                    forms.add(word_lower + word_lower[-1] + 'est')  # big -> biggest
            
            # 比较级/最高级
            if word_lower.endswith('e'):
                stem = word_lower[:-1]
                forms.add(stem + 'er')  # nice -> nicer
                forms.add(stem + 'est') # nice -> nicest
            else:
                forms.add(word_lower + 'er')  # tall -> taller
                forms.add(word_lower + 'est') # tall -> tallest
        
        # 未知的短词只匹配原形（避免生成无意义的变形）
        if len(word_lower) <= 2 and word_lower not in special_forms:
            return [r'\b' + re.escape(word) + r'\b']
        
        # 按长度降序排列（长的先匹配），原形放在最后
        sorted_forms = sorted(forms, key=len, reverse=True)
        # 确保原形在最后
        if word_lower in sorted_forms:
            sorted_forms.remove(word_lower)
            sorted_forms.append(word_lower)
        
        return [r'\b' + re.escape(f) + r'\b' for f in sorted_forms]

    def _update_card(self, wd):
        if not wd: return
        self._card_data = wd
        self._card_revealed = False
        self._card_word.config(text=wd['word'])
        self._card_phon.config(text=wd.get('phonetic', ''))
        self._set_card_text('', '')
        self._highlight_cat(wd['category'])
        favs = self.db.fav_list()
        if wd['word'] in favs:
            self._card_fav.config(text="★ 已收藏", fg=Theme.ORANGE)
        else:
            self._card_fav.config(text="☆ 收藏", fg=Theme.SUB)
        # 更新标熟状态
        if self.db.is_mastered(wd['word']):
            self._card_mastered.config(text="● 已熟", fg=Theme.GREEN)
        else:
            self._card_mastered.config(text="○ 标熟", fg=Theme.SUB)
        self.card_win.deiconify()
        self.card_visible = True
        # 常显释义
        if self.db.cfg('reveal_mode', 'manual') == 'auto':
            self._reveal_card()

    def _reveal_card(self):
        if self._card_data and not self._card_revealed:
            self._set_card_text(self._card_data.get('meaning',''), self._card_data.get('example',''), self._card_data.get('word',''))
            self._card_revealed = True

    def _toggle_fav(self, e=None):
        if self._card_data:
            self.db.toggle_fav(self._card_data['word'])
            favs = self.db.fav_list()
            self._card_fav.config(text="★ 已收藏" if self._card_data['word'] in favs else "☆ 收藏",
                                  fg=Theme.ORANGE if self._card_data['word'] in favs else Theme.SUB)

    def _toggle_mastered(self, e=None):
        """切换标熟状态"""
        if self._card_data:
            self.db.toggle_mastered(self._card_data['word'])
            if self.db.is_mastered(self._card_data['word']):
                self._card_mastered.config(text="● 已熟", fg=Theme.GREEN)
            else:
                self._card_mastered.config(text="○ 标熟", fg=Theme.SUB)

    # ============================================================
    # 学习窗口
    # ============================================================
    def _do_study(self, cat):
        if cat == 'mixed':
            c = '混合模式'
            n = int(self.db.cfg('batch_size', '10'))
            words = []
            for sub in ('cet4', 'cet6'):
                sub_words = self.db.new_list(sub, n//2)
                if not sub_words:
                    pool = self.wm.by_cat(sub)
                    if pool:
                        sub_words = random.sample(pool, min(n//2, len(pool)))
                words.extend(sub_words)
            random.shuffle(words)
            if not words:
                messagebox.showinfo("学习", "暂无可用单词", parent=self.card_win)
                return
        else:
            c = cat or self.db.cfg('default_cat', 'cet4')
            n = int(self.db.cfg('batch_size', '10'))
            words = self.db.new_list(c, n)
            if not words:
                pool = self.wm.by_cat(c)
                if not pool:
                    messagebox.showinfo("学习", f"词库 {c.upper()} 暂无单词", parent=self.card_win)
                    return
                words = random.sample(pool, min(n, len(pool)))
        self._open_study(words, c)

    def _do_review(self):
        cat = self.db.cfg('default_cat', 'cet4')
        words = self.db.review_list(cat, n=20)
        if not words:
            messagebox.showinfo("复习", f"{cat.upper()} 暂无需要复习的单词", parent=self.card_win)
            return
        self._open_study(words, cat)

    def _open_study(self, words, cat):
        win = tk.Toplevel(self.root)
        win.title(f"学习 - {'混合模式' if cat=='mixed' else cat.upper()}")
        win.attributes('-topmost', True)
        win.configure(bg=Theme.BG)
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"440x480+{(sw-440)//2}+{(sh-480)//2}")

        st = {'i':0, 'ok':0, 'shown':0}

        # 顶栏
        top = tk.Frame(win, bg=Theme.CARD, height=48)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text=f"  学习模式", font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)
        pv = tk.StringVar(value=f"1/{len(words)}")
        tk.Label(top, textvariable=pv, font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.RIGHT, padx=12)

        # 按钮区（先 pack）
        btf = tk.Frame(win, bg=Theme.CARD)
        btf.pack(fill=tk.X, side=tk.BOTTOM)

        body = tk.Frame(win, bg=Theme.BG, padx=28, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        wl = tk.Label(body, text="", font=(Theme.FONT, 28, 'bold'), fg=Theme.TEXT, bg=Theme.BG)
        wl.pack(anchor='w')
        pl = tk.Label(body, text="", font=(Theme.FONT_PHON, 12), fg=Theme.SUB, bg=Theme.BG)
        pl.pack(anchor='w', pady=(2, 8))

        tk.Frame(body, bg=Theme.BORDER, height=1).pack(fill=tk.X, pady=4)

        stxt = tk.Text(body, font=(Theme.FONT, 12), fg=Theme.TEXT, bg=Theme.BG,
                       relief=tk.FLAT, height=6, wrap=tk.WORD, highlightthickness=0,
                       state=tk.DISABLED, cursor="arrow")
        stxt.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        stxt.tag_configure('mean', foreground=Theme.BLUE, font=(Theme.FONT, 14))
        stxt.tag_configure('exam', foreground=Theme.SUB, font=(Theme.FONT, 10))

        show_b = tk.Label(btf, text="  显示释义  ", font=(Theme.FONT, 13), fg=Theme.TEXT,
                          bg=Theme.ACCENT, cursor="hand2", padx=20, pady=10)
        show_b.pack(side=tk.LEFT, padx=12, pady=10)
        show_b.bind('<Enter>', lambda e: show_b.config(bg=Theme.ACCENT_H))
        show_b.bind('<Leave>', lambda e: show_b.config(bg=Theme.ACCENT))

        rate_f = tk.Frame(btf, bg=Theme.CARD)

        def _set_stxt(meaning, example):
            stxt.config(state=tk.NORMAL)
            stxt.delete('1.0', tk.END)
            if meaning:
                stxt.insert(tk.END, meaning + '\n', 'mean')
            if example:
                stxt.insert(tk.END, example, 'exam')
            stxt.config(state=tk.DISABLED)

        def show_word(i):
            while i < len(words):
                wd = self.wm.get(words[i])
                if wd: break
                i += 1
            if i >= len(words):
                self.db.add_daily(learned=st['shown'], correct=st['ok'], total=st['shown'])
                messagebox.showinfo("完成", f"学习了 {st['shown']} 个单词\n正确 {st['ok']}/{st['shown']}", parent=win)
                win.destroy(); return
            st['shown'] += 1
            wl.config(text=wd['word']); pl.config(text=wd.get('phonetic',''))
            st['i'] = i
            _set_stxt('', '')
            show_b.pack(side=tk.LEFT, padx=12, pady=10)
            rate_f.pack_forget()
            pv.set(f"{i+1}/{len(words)}")

        def reveal():
            wd = self.wm.get(words[st['i']])
            if wd:
                _set_stxt(wd.get('meaning',''), wd.get('example',''))
            show_b.pack_forget()
            rate_f.pack(side=tk.LEFT, padx=8, pady=10)

        def rate(ok):
            self.db.progress(words[st['i']], cat, ok)
            if ok: st['ok'] += 1
            st['i'] += 1
            show_word(st['i'])

        show_b.bind('<Button-1>', lambda e: reveal())

        for txt, clr, val in [("不认识", Theme.RED, False), ("模糊", Theme.ORANGE, None), ("认识", Theme.GREEN, True)]:
            l = tk.Label(rate_f, text=f" {txt} ", font=(Theme.FONT, 13), fg=Theme.TEXT,
                         bg=clr, cursor="hand2", padx=16, pady=8)
            l.pack(side=tk.LEFT, padx=5)
            l.bind('<Button-1>', lambda e, v=val: rate(v))
            l.bind('<Enter>', lambda e, l=l, c=clr: l.config(bg=self._lighten(c)))
            l.bind('<Leave>', lambda e, l=l, c=clr: l.config(bg=c))

        # 快捷键
        def _study_key(e):
            if rate_f.winfo_ismapped():
                if e.keysym == '1': rate(False)
                elif e.keysym == '2': rate(None)
                elif e.keysym == '3': rate(True)
            else:
                if e.keysym in ('Return', 'space'): reveal()
        win.bind('<Key>', _study_key)

        show_word(0)

    # ============================================================
    # 测试窗口
    # ============================================================
    def _do_test(self, ttype):
        cat = self.db.cfg('default_cat', 'cet4')
        n = int(self.db.cfg('batch_size', '10'))
        words = self.db.review_list(cat, n)
        if not words:
            pool = self.wm.by_cat(cat)
            if not pool:
                messagebox.showinfo("测试", f"词库 {cat.upper()} 暂无单词", parent=self.card_win)
                return
            words = random.sample(pool, min(n, len(pool)))
        self._open_test(words, ttype, cat)

    def _open_test(self, words, ttype, cat='cet4'):
        win = tk.Toplevel(self.root)
        titles = {'en_cn':'英译中','cn_en':'中译英'}
        win.title(titles.get(ttype,'测试'))
        win.attributes('-topmost', True)
        win.configure(bg=Theme.BG)
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"440x500+{(sw-440)//2}+{(sh-500)//2}")

        st = {'i':0, 'ok':0}

        top = tk.Frame(win, bg=Theme.CARD, height=48)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text=f"  {titles.get(ttype,'测试')}", font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)
        pv = tk.StringVar(value=f"1/{len(words)}")
        tk.Label(top, textvariable=pv, font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.RIGHT, padx=12)

        # 按钮区（先 pack）
        btf = tk.Frame(win, bg=Theme.CARD)
        btf.pack(fill=tk.X, side=tk.BOTTOM)

        body = tk.Frame(win, bg=Theme.BG, padx=28, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        ql = tk.Label(body, text="", font=(Theme.FONT, 20, 'bold'), fg=Theme.TEXT,
                      bg=Theme.BG, wraplength=380, anchor='w', justify='left')
        ql.pack(anchor='w', pady=(0,12))

        tk.Frame(body, bg=Theme.BORDER, height=1).pack(fill=tk.X, pady=4)

        opts_f = tk.Frame(body, bg=Theme.BG)
        opts_f.pack(fill=tk.X, pady=8)

        rl = tk.Label(body, text="", font=(Theme.FONT, 13), fg=Theme.TEXT, bg=Theme.BG)
        rl.pack(pady=6)

        nb = tk.Label(btf, text="  下一题  ", font=(Theme.FONT, 13), fg=Theme.TEXT,
                      bg=Theme.ACCENT, cursor="hand2", padx=20, pady=10)

        def ask(i):
            if i >= len(words):
                pct = st['ok']/len(words)*100
                messagebox.showinfo("测试完成", f"正确 {st['ok']}/{len(words)}\n正确率 {pct:.0f}%", parent=win)
                win.destroy(); return
            for w in opts_f.winfo_children(): w.destroy()
            rl.config(text=""); nb.pack_forget()
            wd = self.wm.get(words[i])
            if not wd:
                ask(i+1); return
            ans = None
            if ttype == 'en_cn':
                ql.config(text=wd['word']); ans = wd['meaning']
                pool = list({d['meaning'] for d in self.wm.all.values() if d.get('category')==cat and d['meaning']!=ans})
                opts = random.sample(pool, min(3,len(pool))) + [ans]
            elif ttype == 'cn_en':
                ql.config(text=wd['meaning']); ans = wd['word']
                pool = list({k for k in self.wm.by_cat(cat) if k!=ans})
                opts = random.sample(pool, min(3,len(pool))) + [ans]
            else:
                ql.config(text=f"{wd['meaning']}\n{wd.get('phonetic','')}"); ans = wd['word']
                pool = list({k for k in self.wm.by_cat(cat) if k!=ans})
                opts = random.sample(pool, min(3,len(pool))) + [ans]
            random.shuffle(opts)
            def check(sel):
                st['i'] = i
                for b in opts_f.winfo_children(): b.config(state=tk.DISABLED)
                if sel == ans:
                    rl.config(text="  正确!  ", fg=Theme.GREEN)
                    st['ok'] += 1; self.db.progress(words[i], cat, True)
                else:
                    rl.config(text=f"  错误! 答案: {ans}  ", fg=Theme.RED)
                    self.db.progress(words[i], cat, False)
                nb.pack(side=tk.LEFT, padx=12, pady=10)
            for o in opts:
                l = tk.Label(opts_f, text=f"  {o}  ", font=(Theme.FONT, 12), fg=Theme.TEXT,
                             bg=Theme.CARD, cursor="hand2", anchor='w', padx=16, pady=12)
                l.pack(fill=tk.X, pady=3)
                l.bind('<Button-1>', lambda e,v=o: check(v))
                l.bind('<Enter>', lambda e,l=l: l.config(bg=Theme.HOVER))
                l.bind('<Leave>', lambda e,l=l: l.config(bg=Theme.CARD))
            pv.set(f"{i+1}/{len(words)}")
            # 快捷键
            def _test_key(e, opts=opts, ck=check):
                if nb.winfo_ismapped():  # 下一题已显示
                    if e.keysym in ('Return', 'space'):
                        ask(st['i']+1)
                else:
                    idx = {'1':0,'2':1,'3':2,'4':3}.get(e.keysym)
                    if idx is not None and idx < len(opts):
                        ck(opts[idx])
            win.bind('<Key>', _test_key, '+')

        nb.bind('<Button-1>', lambda e: ask(st['i']+1))
        nb.bind('<Enter>', lambda e: nb.config(bg=Theme.ACCENT_H))
        nb.bind('<Leave>', lambda e: nb.config(bg=Theme.ACCENT))
        ask(0)

    # ---- 滚动列表组件 ----
    def _make_scrollable_frame(self, parent):
        """创建可滚动的 Canvas+Scrollbar 容器，返回 (canvas, scrollbar, inner_frame)"""
        canvas = tk.Canvas(parent, bg=Theme.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=Theme.BG)
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return canvas, scrollbar, inner

    def _make_word_row(self, parent, word_data, show_unmark=False, unmark_cb=None):
        """创建一行单词条目，返回 row Frame"""
        wd = word_data
        row = tk.Frame(parent, bg=Theme.CARD, pady=8, padx=12)
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=wd['word'], font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT)
        tk.Label(row, text=wd.get('meaning', ''), font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)
        if show_unmark and unmark_cb:
            btn = tk.Label(row, text="取消标熟", font=(Theme.FONT, 10),
                           fg=Theme.RED, bg=Theme.CARD, cursor="hand2", padx=8)
            btn.pack(side=tk.RIGHT)
            btn.bind('<Button-1>', lambda e, w=wd['word']: unmark_cb(w))
        row.bind('<Button-1>', lambda e, w=wd: self._update_card(w))
        for ch in row.winfo_children():
            if not show_unmark or ch != row.winfo_children()[-1]:
                ch.bind('<Button-1>', lambda e, w=wd: self._update_card(w))
        return row

    # ============================================================
    # 单词本
    # ============================================================
    def _do_favs(self):
        favs = self.db.fav_list()
        if not favs:
            messagebox.showinfo("单词本", "还没有收藏的单词", parent=self.card_win)
            return
        win = self._make_list_window("收藏的单词", "400x440")
        body = tk.Frame(win, bg=Theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        _, _, inner = self._make_scrollable_frame(body)
        for word in favs:
            wd = self.wm.get(word)
            if not wd: continue
            self._make_word_row(inner, wd)

    def _make_list_window(self, title, geometry_fmt):
        """创建列表窗口通用框架，返回 win"""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.attributes('-topmost', True)
        win.configure(bg=Theme.BG)
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h = geometry_fmt.split('x')
        win.geometry(f"{w}x{h}+{(sw-int(w))//2}+{(sh-int(h))//2}")
        top = tk.Frame(win, bg=Theme.CARD, height=48)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text=f"  {title}", font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)
        return win

    def _do_mastered(self):
        """显示已认识单词列表"""
        if not self.db.mastered_list():
            messagebox.showinfo("已认识", "还没有标记为已认识的单词", parent=self.card_win)
            return
        win = self._make_list_window("已认识的单词", "400x440")
        body = tk.Frame(win, bg=Theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        _, _, inner = self._make_scrollable_frame(body)

        def refresh():
            for widget in inner.winfo_children():
                widget.destroy()
            for w in self.db.mastered_list():
                wd = self.wm.get(w)
                if not wd: continue
                self._make_word_row(inner, wd, show_unmark=True, unmark_cb=lambda word, r=refresh: (self.db.toggle_mastered(word), r()))

        refresh()

    # ============================================================
    # 统计
    # ============================================================
    def _do_stats(self):
        s = self.db.stats()
        mastered_count = self.db.mastered_count()
        win = tk.Toplevel(self.root)
        win.title("学习统计")
        win.attributes('-topmost', True)
        win.configure(bg=Theme.BG)
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"400x520+{(sw-400)//2}+{(sh-520)//2}")

        top = tk.Frame(win, bg=Theme.CARD, height=48)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text="  学习统计", font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)

        body = tk.Frame(win, bg=Theme.BG, padx=24, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        items = [("已学单词", f"{s['total']} 个", Theme.BLUE),
                 ("已掌握", f"{s['mastered']} 个", Theme.GREEN),
                 ("已认识", f"{mastered_count} 个", Theme.PURPLE),
                 ("今日学习", f"{s['t_learned']} 个", Theme.TEXT),
                 ("今日复习", f"{s['t_reviewed']} 个", Theme.TEXT),
                 ("今日正确率", f"{s['t_correct']}/{s['t_total']}" if s['t_total'] else "-", Theme.ORANGE),
                 ("今日学习时间", f"{s['t_time']//60} 分钟", Theme.TEXT),
                 ("累计学习", f"{s['total_time']//60} 分钟" if s['total_time'] < 3600 else f"{s['total_time']//3600} 小时", Theme.TEXT),
                 ("连续学习", f"{s['streak']} 天", Theme.PURPLE)]

        for label, value, color in items:
            row = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, font=(Theme.FONT, 11), fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=(Theme.FONT, 12, 'bold'), fg=color, bg=Theme.CARD).pack(side=tk.RIGHT)

    # ============================================================
    # 设置
    # ============================================================
    def _do_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.attributes('-topmost', True)
        win.configure(bg=Theme.BG)
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"400x400+{(sw-400)//2}+{(sh-400)//2}")

        top = tk.Frame(win, bg=Theme.CARD, height=48)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text="  设置", font=(Theme.FONT, 13, 'bold'),
                 fg=Theme.TEXT, bg=Theme.CARD).pack(side=tk.LEFT, padx=12)

        body = tk.Frame(win, bg=Theme.BG, padx=20, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        # 弹词间隔
        r1 = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="弹词间隔（秒）", font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
        iv = tk.StringVar(value=str(self.auto_interval))
        tk.Entry(r1, textvariable=iv, font=(Theme.FONT, 11), bg=Theme.BG,
                 fg=Theme.TEXT, insertbackground=Theme.TEXT, width=8, relief=tk.FLAT).pack(side=tk.RIGHT)

        # 默认词库
        r2 = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="默认词库", font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
        default_cat = self.db.cfg('default_cat', 'cet4')
        cv = tk.StringVar(value={'cet4': 'CET-4', 'cet6': 'CET-6'}.get(default_cat, 'CET-4'))
        cv_menu = tk.OptionMenu(r2, cv, 'CET-4', 'CET-6')
        cv_menu.config(bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
                       activeforeground=Theme.TEXT, relief=tk.FLAT, highlightthickness=0,
                       font=(Theme.FONT, 10), padx=8, bd=0, indicatoron=True)
        cv_menu['menu'].config(bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
                               activeforeground=Theme.TEXT, font=(Theme.FONT, 10), bd=0)
        cv_menu.pack(side=tk.RIGHT)
        cat_map = {'CET-4': 'cet4', 'CET-6': 'cet6'}

        # 显示模式
        r3 = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
        r3.pack(fill=tk.X, pady=3)
        tk.Label(r3, text="显示模式", font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
        rm = tk.StringVar()
        rm_menu = tk.OptionMenu(r3, rm, '手动', '自动')
        rm_menu.config(bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
                       activeforeground=Theme.TEXT, relief=tk.FLAT, highlightthickness=0,
                       font=(Theme.FONT, 10), padx=8, bd=0, indicatoron=True)
        rm_menu['menu'].config(bg=Theme.CARD, fg=Theme.TEXT, activebackground=Theme.ACCENT,
                               activeforeground=Theme.TEXT, font=(Theme.FONT, 10), bd=0)
        rm_menu.pack(side=tk.RIGHT)
        mode_map = {'manual': '手动', 'auto': '自动'}
        rev_mode = {v: k for k, v in mode_map.items()}
        rm.set(mode_map.get(self.db.cfg('reveal_mode', 'manual'), '手动'))

        # 每批数量
        r4 = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
        r4.pack(fill=tk.X, pady=3)
        tk.Label(r4, text="每批数量", font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
        bs = tk.StringVar(value=self.db.cfg('batch_size', '10'))
        tk.Entry(r4, textvariable=bs, font=(Theme.FONT, 11), bg=Theme.BG,
                 fg=Theme.TEXT, insertbackground=Theme.TEXT, width=8, relief=tk.FLAT).pack(side=tk.RIGHT)

        # 窗口透明度
        r5 = tk.Frame(body, bg=Theme.CARD, pady=10, padx=16)
        r5.pack(fill=tk.X, pady=3)
        tk.Label(r5, text="窗口透明度", font=(Theme.FONT, 11),
                 fg=Theme.SUB, bg=Theme.CARD).pack(side=tk.LEFT)
        op = tk.DoubleVar(value=float(self.db.cfg('window_alpha', '0.95')))
        def update_alpha(v):
            self.card_win.attributes('-alpha', float(v))
            op_lbl.config(text=f"{float(v):.2f}")
        op_scale = tk.Scale(r5, from_=0.3, to=1.0, resolution=0.05, orient=tk.HORIZONTAL,
                            variable=op, showvalue=False, length=100, bg=Theme.BG, fg=Theme.TEXT,
                            highlightthickness=0, troughcolor=Theme.CARD, sliderlength=20,
                            command=update_alpha)
        op_scale.pack(side=tk.LEFT, padx=(0, 4))
        op_lbl = tk.Label(r5, text=f"{op.get():.2f}", font=(Theme.FONT, 11, 'bold'),
                          fg=Theme.BLUE, bg=Theme.CARD, width=4)
        op_lbl.pack(side=tk.RIGHT)

        def save():
            try:
                self.auto_interval = max(5, int(iv.get()))
                self.db.set_cfg('auto_interval', self.auto_interval)
                self.db.set_cfg('default_cat', cat_map.get(cv.get(), 'cet4'))
                self.db.set_cfg('reveal_mode', rev_mode.get(rm.get(), 'manual'))
                self.db.set_cfg('window_alpha', f"{op.get():.2f}")
                self.db.set_cfg('batch_size', bs.get())
                messagebox.showinfo("设置", "已保存", parent=win)
                win.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入数字", parent=win)

        btn = tk.Label(body, text="  保存  ", font=(Theme.FONT, 12), fg=Theme.TEXT,
                       bg=Theme.ACCENT, cursor="hand2", padx=20, pady=8)
        btn.pack(pady=12)
        btn.bind('<Button-1>', lambda e: save())
        btn.bind('<Enter>', lambda e: btn.config(bg=Theme.ACCENT_H))
        btn.bind('<Leave>', lambda e: btn.config(bg=Theme.ACCENT))

    # ============================================================
    # 导入单词书
    # ============================================================
    def _do_import(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="选择单词文件",
            filetypes=[("JSON 文件","*.json"),("文本文件","*.txt"),("所有文件","*.*")])
        if not path: return
        try:
            count = self._import_words(path)
            messagebox.showinfo("导入完成", f"成功导入 {count} 个单词", parent=self.card_win)
            # 重载词库
            self.wm = Words(str(self.app_dir / "data" / WORDS_FILE))
        except Exception as e:
            messagebox.showerror("导入失败", str(e), parent=self.card_win)

    def _import_words(self, path):
        path = Path(path)
        ext = path.suffix.lower()
        words = []
        if ext == '.json':
            words = self._import_json(path)
        else:
            words = self._import_text(path)
        if not words:
            raise ValueError("未解析到有效单词")
        # 合并到 words.json
        data_file = self.app_dir / "data" / WORDS_FILE
        existing = {}
        if data_file.exists():
            with open(data_file,'r',encoding='utf-8') as f:
                existing = json.load(f)
        # 全局去重
        existing_words = set()
        for cat, cat_words in existing.items():
            unique = []
            for w in cat_words:
                if isinstance(w, dict) and 'word' in w:
                    key = w['word'].lower()
                    if key not in existing_words:
                        existing_words.add(key)
                        unique.append(w)
            existing[cat] = unique
        added = 0
        for w in words:
            if w['word'].lower() not in existing_words:
                cat = w.get('category', 'cet4')
                if cat not in existing:
                    existing[cat] = []
                existing[cat].append(w)
                existing_words.add(w['word'].lower())
                added += 1
        with open(data_file,'w',encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return added

    def _import_json(self, path):
        with open(path,'r',encoding='utf-8') as f:
            data = json.load(f)
        words = []
        # 支持两种格式：1) 和 words.json 一样的 {cet4:[],cet6:[]}  2) 直接是 [{word,meaning},...]
        if isinstance(data, dict):
            for cat in ('cet4','cet6','custom'):
                for w in data.get(cat,[]):
                    if isinstance(w, dict) and 'word' in w:
                        w.setdefault('category', cat)
                        w.setdefault('phonetic','')
                        w.setdefault('meaning','')
                        w.setdefault('example','')
                        words.append(w)
        elif isinstance(data, list):
            for w in data:
                if isinstance(w, dict) and 'word' in w:
                    w.setdefault('category', 'custom')
                    w.setdefault('phonetic','')
                    w.setdefault('meaning','')
                    w.setdefault('example','')
                    words.append(w)
        return words

    def _import_text(self, path):
        words = []
        with open(path,'r',encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                # 支持格式：
                # word
                # word 释义
                # word /phonetic/ 释义
                parts = line.split(None, 1)
                word = parts[0]
                meaning = parts[1] if len(parts) > 1 else ''
                # 检查是否有音标
                phonetic = ''
                if meaning.startswith('/') or meaning.startswith('['):
                    end = meaning.find('/', 1) if meaning.startswith('/') else meaning.find(']', 1)
                    if end > 0:
                        phonetic = meaning[:end+1]
                        meaning = meaning[end+1:].strip()
                words.append({
                    'word': word,
                    'phonetic': phonetic,
                    'meaning': meaning,
                    'example': '',
                    'category': 'custom'
                })
        return words

    # ---- 工具 ----
    def _lighten(self, hex_color):
        """稍微提亮颜色"""
        try:
            r, g, b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
            r = min(255, r+20); g = min(255, g+20); b = min(255, b+20)
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return hex_color

def main():
    App().run()

if __name__ == "__main__":
    main()
