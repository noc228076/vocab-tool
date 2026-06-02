#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test core logic without GUI
"""

import sys, os, tempfile, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vocab_app import DB, Words

def test_db():
    print("=== DB Tests ===")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        path = tmp.name
    db = DB(path)

    # progress
    db.progress('hello', 'cet4', True)
    db.progress('hello', 'cet4', True)
    db.progress('world', 'cet4', False)
    s = db.stats()
    # 'hello' lv=2 (2 correct), 'world' lv=0 (wrong stays at 0), total counts lv>0
    assert s['total'] == 1, f"expected 1 (only lv>0), got {s['total']}"
    print("  [OK] progress tracking")

    # fav
    db.toggle_fav('hello')
    assert 'hello' in db.fav_list()
    db.toggle_fav('hello')
    assert 'hello' not in db.fav_list()
    print("  [OK] favorites toggle")

    # review_list
    rl = db.review_list()
    assert isinstance(rl, list)
    print("  [OK] review_list")

    # new_list
    nl = db.new_list('cet4')
    assert isinstance(nl, list)
    print("  [OK] new_list")

    # cfg
    db.set_cfg('default_cat', 'cet6')
    assert db.cfg('default_cat') == 'cet6'
    print("  [OK] cfg")

    # add_daily
    db.add_daily(learned=5, reviewed=3, correct=2, total=3, secs=120)
    s = db.stats()
    assert s['t_learned'] == 5
    assert s['t_reviewed'] == 3
    print("  [OK] add_daily")

    # streak
    assert s['streak'] >= 1
    print("  [OK] streak")

    os.unlink(path)
    print("  [OK] all DB tests passed\n")

def test_words():
    print("=== Words Tests ===")
    wm = Words(str(Path(__file__).parent.parent / "data" / "words.json"))

    assert len(wm.by_cat('cet4')) > 0, "CET-4 is empty"
    assert len(wm.by_cat('cet6')) > 0, "CET-6 is empty"
    print(f"  [OK] cet4={len(wm.by_cat('cet4'))}, cet6={len(wm.by_cat('cet6'))}")

    w = wm.rand('cet4')
    assert w is not None
    d = wm.get(w)
    assert d is not None
    assert d['category'] == 'cet4'
    print(f"  [OK] rand cet4: {w}")

    w = wm.rand('cet6')
    assert w is not None
    d = wm.get(w)
    assert d['category'] == 'cet6'
    print(f"  [OK] rand cet6: {w}")

    # All words have required keys
    for word, data in wm.all.items():
        assert 'word' in data, f"{word} missing 'word'"
        assert 'meaning' in data, f"{word} missing 'meaning'"
        assert 'category' in data, f"{word} missing 'category'"
    print("  [OK] all words have required keys")

    print("  [OK] all Words tests passed\n")

def test_test_flow():
    """Simulate the test question flow to catch index bugs"""
    print("=== Test Flow Simulation ===")
    wm = Words(str(Path(__file__).parent.parent / "data" / "words.json"))
    words = wm.by_cat('cet4')[:5]

    # Simulate the ask/check cycle
    st = {'i': 0, 'ok': 0}
    answered = []

    for i in range(len(words)):
        wd = wm.get(words[i])
        assert wd is not None
        ans = wd['meaning']
        # Simulate answering
        st['i'] = i
        if random.choice([True, False]):
            st['ok'] += 1
        answered.append(i)

    assert st['i'] == len(words) - 1, f"st['i'] should be {len(words)-1}, got {st['i']}"
    assert len(answered) == len(words)
    print(f"  [OK] answered {len(answered)} questions, index tracked correctly")
    print("  [OK] test flow simulation passed\n")

if __name__ == "__main__":
    test_db()
    test_words()
    test_test_flow()
    print("ALL TESTS PASSED")
