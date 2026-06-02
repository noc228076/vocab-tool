#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理词库：移除明显不是四六级大纲的词
注意：执行前会备份原文件
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

WORDS_FILE = Path(__file__).parent.parent / "data" / "words.json"

# 基础词汇（初中/高中基础，通常不在四六级大纲中）
BASIC_WORDS = {
    # 冠词/代词/介词/连词等基础词
    'a', 'an', 'the', 'is', 'are', 'am', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can',
    'could', 'may', 'might', 'must', 'shall', 'should',
    'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'this', 'that', 'these', 'those',
    'what', 'which', 'who', 'whom', 'whose',
    'where', 'when', 'why', 'how',
    'not', 'no', 'yes', 'and', 'but', 'or', 'so', 'if', 'then',
    # 基础名词
    'cat', 'dog', 'hat', 'pen', 'book', 'cup', 'bag', 'box',
    'boy', 'girl', 'man', 'woman', 'child', 'baby',
    'mom', 'dad', 'mum', 'father', 'mother',
    # 基础形容词
    'big', 'small', 'old', 'new', 'good', 'bad', 'hot', 'cold',
    'red', 'blue', 'green', 'black', 'white', 'yellow',
    'long', 'short', 'tall', 'high', 'low',
    'fast', 'slow', 'hard', 'easy', 'happy', 'sad',
    # 基础动词
    'go', 'come', 'run', 'walk', 'eat', 'drink', 'sleep', 'play',
    'like', 'love', 'want', 'need', 'know', 'think', 'see', 'look',
    'give', 'take', 'make', 'get', 'put', 'set', 'let',
    'say', 'tell', 'ask', 'help', 'try', 'use', 'find',
    # 基础介词/副词
    'up', 'down', 'in', 'out', 'on', 'off', 'at', 'to', 'for',
    'with', 'from', 'by', 'about', 'into', 'through', 'before', 'after',
    'above', 'below', 'between', 'under', 'over',
    'here', 'there', 'now', 'then', 'very', 'too', 'also',
    # 基础数词
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'hundred', 'thousand', 'million',
}

def clean_words():
    """清理词库"""
    # 备份原文件
    backup_file = WORDS_FILE.parent / f"words_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(WORDS_FILE, backup_file)
    print(f"已备份原文件到: {backup_file}")
    
    # 读取词库
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 清理 CET-4
    cet4_before = len(data.get('cet4', []))
    data['cet4'] = [w for w in data.get('cet4', []) if w['word'].lower() not in BASIC_WORDS]
    cet4_after = len(data['cet4'])
    print(f"\nCET-4: {cet4_before} -> {cet4_after} (移除 {cet4_before - cet4_after} 个基础词)")
    
    # 清理 CET-6
    cet6_before = len(data.get('cet6', []))
    data['cet6'] = [w for w in data.get('cet6', []) if w['word'].lower() not in BASIC_WORDS]
    cet6_after = len(data['cet6'])
    print(f"CET-6: {cet6_before} -> {cet6_after} (移除 {cet6_before - cet6_after} 个基础词)")
    
    # 清理 custom 中的测试词
    custom_before = len(data.get('custom', []))
    data['custom'] = [w for w in data.get('custom', []) if 'test' not in w['word'].lower()]
    custom_after = len(data['custom'])
    print(f"Custom: {custom_before} -> {custom_after} (移除 {custom_before - custom_after} 个测试词)")
    
    # 保存清理后的词库
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n清理完成！已保存到: {WORDS_FILE}")

if __name__ == "__main__":
    print("=== 词库清理工具 ===\n")
    print("将移除以下类型的词:")
    print("1. 基础词汇（初中/高中基础词汇）")
    print("2. 测试词（包含 'test' 的词）")
    print("\n注意：执行前会自动备份原文件\n")
    
    response = input("是否继续？(y/n): ").strip().lower()
    if response == 'y':
        clean_words()
    else:
        print("已取消")
