#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查词库质量问题"""
import json

with open('data/words.json','r',encoding='utf-8') as f:
    data = json.load(f)

print('=== 词库质量问题检查 ===\n')

# 1. 检查重复词（跨分类）
all_words = {}
duplicates = []
for cat in ['cet4', 'cet6', 'custom']:
    for w in data.get(cat, []):
        word = w['word'].lower()
        if word in all_words:
            duplicates.append((word, all_words[word], cat))
        else:
            all_words[word] = cat

print(f'1. 跨分类重复词: {len(duplicates)} 个')
for word, cat1, cat2 in duplicates[:10]:
    print(f'   {word}: {cat1} / {cat2}')

# 2. 检查释义为空的词
empty_meaning = []
for cat in ['cet4', 'cet6']:
    for w in data.get(cat, []):
        if not w.get('meaning', '').strip():
            empty_meaning.append((cat, w['word']))

print(f'\n2. 释义为空的词: {len(empty_meaning)} 个')
for cat, word in empty_meaning[:10]:
    print(f'   {cat}: {word}')

# 3. 检查单词长度异常的词
print(f'\n3. 单词长度分布:')
for cat in ['cet4', 'cet6']:
    words = data.get(cat, [])
    lengths = [len(w['word']) for w in words]
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    min_len = min(lengths) if lengths else 0
    max_len = max(lengths) if lengths else 0
    print(f'   {cat}: 平均 {avg_len:.1f} 字符, 最小 {min_len}, 最大 {max_len}')
    
    # 检查异常短的词（1-2个字符）
    short_words = [w['word'] for w in words if len(w['word']) <= 2]
    if short_words:
        print(f'   异常短的词: {", ".join(short_words[:20])}')

# 4. 检查 custom 分类中的测试词
custom_words = data.get('custom', [])
print(f'\n4. Custom 分类: {len(custom_words)} 词')
test_words = [w['word'] for w in custom_words if 'test' in w['word'].lower()]
if test_words:
    print(f'   测试词: {", ".join(test_words)}')

# 5. 检查音标格式
print(f'\n5. 音标格式检查:')
no_phonetic = 0
for cat in ['cet4', 'cet6']:
    for w in data.get(cat, []):
        if not w.get('phonetic', '').strip():
            no_phonetic += 1
print(f'   无音标的词: {no_phonetic} 个')
