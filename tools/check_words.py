#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查词库内容"""
import json

with open('data/words.json','r',encoding='utf-8') as f:
    data = json.load(f)

print(f'CET-4: {len(data.get("cet4",[]))} 词')
print(f'CET-6: {len(data.get("cet6",[]))} 词')
print()

print('=== CET-4 前30个单词 ===')
for w in data.get('cet4',[])[:30]:
    print(f"  {w['word']}: {w['meaning']}")

print()
print('=== CET-6 前30个单词 ===')
for w in data.get('cet6',[])[:30]:
    print(f"  {w['word']}: {w['meaning']}")

print()
print('=== 检查可能不是CET-4的词（简单词）===')
simple_words = ['hat', 'cat', 'dog', 'boy', 'girl', 'mom', 'dad', 'big', 'small', 'red', 'blue']
cet4_words = {w['word'].lower() for w in data.get('cet4',[])}
for w in simple_words:
    if w in cet4_words:
        print(f"  {w} 在CET-4中（可能过于简单）")

print()
print('=== 检查可能不是CET-6的词 ===')
cet6_words = {w['word'].lower() for w in data.get('cet6',[])}
# 检查一些明显不是CET-6的词
for w in data.get('cet6',[])[:50]:
    if len(w['word']) <= 3:
        print(f"  短词: {w['word']}: {w['meaning']}")
