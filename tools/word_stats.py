#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate statistics about the word database
"""

import json
from pathlib import Path
from collections import Counter

def analyze_words():
    """Analyze the word database"""
    tools_dir = Path(__file__).parent
    data_dir = tools_dir.parent / "data"
    words_file = data_dir / "words.json"

    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Word Database Statistics")
    print("=" * 50)

    # CET-4 words
    cet4_words = data.get('cet4', [])
    print(f"\nCET-4 Words: {len(cet4_words)}")

    # CET-6 words
    cet6_words = data.get('cet6', [])
    print(f"CET-6 Words: {len(cet6_words)}")

    print(f"Total Words: {len(cet4_words) + len(cet6_words)}")

    # Word length distribution
    print("\nWord Length Distribution:")
    all_words = cet4_words + cet6_words
    lengths = [len(w['word']) for w in all_words]
    length_counts = Counter(lengths)

    for length in sorted(length_counts.keys()):
        count = length_counts[length]
        bar = '#' * (count // 2)
        print(f"  {length:2d} chars: {count:3d} {bar}")

    # Most common first letters
    print("\nMost Common First Letters:")
    first_letters = [w['word'][0].lower() for w in all_words]
    letter_counts = Counter(first_letters)

    for letter, count in letter_counts.most_common(10):
        bar = '#' * (count // 2)
        print(f"  {letter}: {count:3d} {bar}")

    # Word categories
    print("\nWord Categories:")
    categories = Counter(w.get('category', 'unknown') for w in all_words)
    for category, count in categories.most_common():
        print(f"  {category}: {count}")

    # Sample words
    print("\nSample CET-4 Words:")
    for word in cet4_words[:5]:
        print(f"  {word['word']}: {word['meaning']}")

    print("\nSample CET-6 Words:")
    for word in cet6_words[:5]:
        print(f"  {word['word']}: {word['meaning']}")

if __name__ == "__main__":
    analyze_words()
