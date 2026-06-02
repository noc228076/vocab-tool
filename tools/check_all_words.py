#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有词库文件"""
import json

files = ['data/words.json', 'data/words_cet6.json', 'data/words_extended.json']

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        print(f'\n=== {f} ===')
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    print(f'  {key}: {len(data[key])} 词')
                    # 显示前5个词
                    for w in data[key][:5]:
                        if isinstance(w, dict) and 'word' in w:
                            print(f"    {w['word']}: {w.get('meaning', 'N/A')}")
        elif isinstance(data, list):
            print(f'  列表: {len(data)} 词')
            for w in data[:5]:
                if isinstance(w, dict) and 'word' in w:
                    print(f"    {w['word']}: {w.get('meaning', 'N/A')}")
    except Exception as e:
        print(f'\n=== {f} ===')
        print(f'  错误: {e}')
