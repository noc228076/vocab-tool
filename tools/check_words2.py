#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查词库中可能不是四六级大纲的词"""
import json

with open('data/words.json','r',encoding='utf-8') as f:
    data = json.load(f)

cet4_words = {w['word'].lower(): w for w in data.get('cet4',[])}
cet6_words = {w['word'].lower(): w for w in data.get('cet6',[])}

print('=== CET-4 中可能过于简单的词（初中/高中词汇）===')
# 这些词通常是初中的基础词汇
basic_words = [
    'a', 'an', 'the', 'is', 'are', 'am', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can',
    'could', 'may', 'might', 'must', 'shall', 'should',
    'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'this', 'that', 'these', 'those',
    'what', 'which', 'who', 'whom', 'whose',
    'where', 'when', 'why', 'how',
    'not', 'no', 'yes', 'and', 'but', 'or', 'so', 'if', 'then',
    'cat', 'dog', 'hat', 'pen', 'book', 'cup', 'bag', 'box',
    'boy', 'girl', 'man', 'woman', 'child', 'baby',
    'big', 'small', 'old', 'new', 'good', 'bad', 'hot', 'cold',
    'red', 'blue', 'green', 'black', 'white', 'yellow',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'go', 'come', 'run', 'walk', 'eat', 'drink', 'sleep', 'play',
    'like', 'love', 'want', 'need', 'know', 'think', 'see', 'look',
    'give', 'take', 'make', 'get', 'put', 'set', 'let',
    'up', 'down', 'in', 'out', 'on', 'off', 'at', 'to', 'for',
    'with', 'from', 'by', 'about', 'into', 'through', 'before', 'after',
    'above', 'below', 'between', 'under', 'over',
]

found_basic = []
for w in basic_words:
    if w in cet4_words:
        found_basic.append(w)

print(f'找到 {len(found_basic)} 个基础词汇：')
for w in found_basic[:50]:
    print(f'  {w}: {cet4_words[w]["meaning"]}')

print()
print('=== CET-4 中可能不是大纲的词（检查释义）===')
# 检查一些释义看起来不像四六级词汇的词
suspicious = []
for word, info in cet4_words.items():
    meaning = info.get('meaning', '')
    # 检查是否包含非常专业的术语
    if any(term in meaning.lower() for term in ['化学', '物理', '生物', '医学', '法律', '计算机']):
        suspicious.append((word, meaning))

print(f'找到 {len(suspicious)} 个可能专业的词：')
for w, m in suspicious[:20]:
    print(f'  {w}: {m}')

print()
print('=== CET-6 中可能不是大纲的词 ===')
# 检查一些释义看起来不像六级词汇的词
suspicious_cet6 = []
for word, info in cet6_words.items():
    meaning = info.get('meaning', '')
    # 检查是否包含非常简单的释义
    if any(simple in meaning for simple in ['n. 方式', 'n. 状态', 'v. 做', 'v. 有']):
        suspicious_cet6.append((word, meaning))

print(f'找到 {len(suspicious_cet6)} 个可能简单的词：')
for w, m in suspicious_cet6[:20]:
    print(f'  {w}: {m}')
