#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download additional words from online sources
"""

import json
from pathlib import Path

def download_cet4_words():
    """Download CET-4 words from online source"""
    print("Downloading CET-4 words...")

    # This is a placeholder - in a real implementation,
    # you would fetch from a reliable API or database
    # For now, we'll just add some sample words

    sample_words = [
        {
            "word": "calculate",
            "phonetic": "/ˈkælkjuleɪt/",
            "meaning": "v. 计算",
            "example": "Can you calculate the total?",
            "category": "cet4"
        },
        {
            "word": "calendar",
            "phonetic": "/ˈkælɪndər/",
            "meaning": "n. 日历",
            "example": "Mark the date on the calendar.",
            "category": "cet4"
        },
        {
            "word": "campaign",
            "phonetic": "/kæmˈpeɪn/",
            "meaning": "n. 运动；战役",
            "example": "The advertising campaign was successful.",
            "category": "cet4"
        },
        {
            "word": "campus",
            "phonetic": "/ˈkæmpəs/",
            "meaning": "n. 校园",
            "example": "The campus is beautiful in autumn.",
            "category": "cet4"
        },
        {
            "word": "candidate",
            "phonetic": "/ˈkændɪdət/",
            "meaning": "n. 候选人",
            "example": "She is a strong candidate for the position.",
            "category": "cet4"
        },
        {
            "word": "capable",
            "phonetic": "/ˈkeɪpəbl/",
            "meaning": "adj. 有能力的",
            "example": "She is capable of handling the task.",
            "category": "cet4"
        },
        {
            "word": "capacity",
            "phonetic": "/kəˈpæsəti/",
            "meaning": "n. 容量；能力",
            "example": "The stadium has a capacity of 50,000.",
            "category": "cet4"
        },
        {
            "word": "capture",
            "phonetic": "/ˈkæptʃər/",
            "meaning": "v. 捕获；夺取",
            "example": "The police captured the thief.",
            "category": "cet4"
        },
        {
            "word": "carbon",
            "phonetic": "/ˈkɑːrbən/",
            "meaning": "n. 碳",
            "example": "Carbon dioxide is a greenhouse gas.",
            "category": "cet4"
        },
        {
            "word": "career",
            "phonetic": "/kəˈrɪr/",
            "meaning": "n. 职业；生涯",
            "example": "She has a successful career.",
            "category": "cet4"
        }
    ]

    return sample_words

def download_cet6_words():
    """Download CET-6 words from online source"""
    print("Downloading CET-6 words...")

    sample_words = [
        {
            "word": "calibrate",
            "phonetic": "/ˈkælɪbreɪt/",
            "meaning": "v. 校准；标定",
            "example": "We need to calibrate the equipment.",
            "category": "cet6"
        },
        {
            "word": "camouflage",
            "phonetic": "/ˈkæməflɑːʒ/",
            "meaning": "n./v. 伪装",
            "example": "The soldiers used camouflage.",
            "category": "cet6"
        },
        {
            "word": "candid",
            "phonetic": "/ˈkændɪd/",
            "meaning": "adj. 坦率的；公正的",
            "example": "She gave a candid assessment.",
            "category": "cet6"
        },
        {
            "word": "capitalize",
            "phonetic": "/ˈkæpɪtəlaɪz/",
            "meaning": "v. 资本化；利用",
            "example": "We need to capitalize on this opportunity.",
            "category": "cet6"
        },
        {
            "word": "catalyst",
            "phonetic": "/ˈkætəlɪst/",
            "meaning": "n. 催化剂；促进因素",
            "example": "The event was a catalyst for change.",
            "category": "cet6"
        },
        {
            "word": "caution",
            "phonetic": "/ˈkɔːʃn/",
            "meaning": "n./v. 谨慎；警告",
            "example": "Proceed with caution.",
            "category": "cet6"
        },
        {
            "word": "census",
            "phonetic": "/ˈsensəs/",
            "meaning": "n. 人口普查",
            "example": "The census is conducted every ten years.",
            "category": "cet6"
        },
        {
            "word": "chronic",
            "phonetic": "/ˈkrɑːnɪk/",
            "meaning": "adj. 慢性的；长期的",
            "example": "He suffers from chronic pain.",
            "category": "cet6"
        },
        {
            "word": "circulation",
            "phonetic": "/ˌsɜːrkjəˈleɪʃn/",
            "meaning": "n. 循环；流通",
            "example": "The newspaper has a large circulation.",
            "category": "cet6"
        },
        {
            "word": "cite",
            "phonetic": "/saɪt/",
            "meaning": "v. 引用；举例",
            "example": "He cited several examples.",
            "category": "cet6"
        }
    ]

    return sample_words

def update_words_file(new_words, category):
    """Update the words.json file with new words"""
    tools_dir = Path(__file__).parent
    data_dir = tools_dir.parent / "data"
    words_file = data_dir / "words.json"

    # Load existing words
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if category not in data:
        data[category] = []

    # Add new words (skip duplicates)
    added = 0
    for word in new_words:
        exists = False
        for existing_word in data[category]:
            if existing_word["word"].lower() == word["word"].lower():
                exists = True
                break

        if not exists:
            data[category].append(word)
            added += 1
            print(f"Added: {word['word']}")

    # Save updated words
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return added

def main():
    print("Download additional words")
    print("=" * 40)

    # Download CET-4 words
    cet4_words = download_cet4_words()
    added_cet4 = update_words_file(cet4_words, "cet4")
    print(f"Added {added_cet4} CET-4 words")

    # Download CET-6 words
    cet6_words = download_cet6_words()
    added_cet6 = update_words_file(cet6_words, "cet6")
    print(f"Added {added_cet6} CET-6 words")

    print("\nDone!")

if __name__ == "__main__":
    main()
