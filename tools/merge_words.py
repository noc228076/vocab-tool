#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Merge word files into a single words.json
"""

import json
from pathlib import Path

def merge_word_files():
    """Merge all word JSON files into words.json"""
    tools_dir = Path(__file__).parent
    data_dir = tools_dir.parent / "data"
    merged = {"cet4": [], "cet6": []}

    # Find all JSON files in data directory
    for json_file in data_dir.glob("words*.json"):
        if json_file.name == "words.json":
            continue

        print(f"Loading {json_file.name}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Merge CET4 words
        if "cet4" in data:
            merged["cet4"].extend(data["cet4"])

        # Merge CET6 words
        if "cet6" in data:
            merged["cet6"].extend(data["cet6"])

    # Remove duplicates by word
    for category in ["cet4", "cet6"]:
        seen = set()
        unique_words = []
        for word_data in merged[category]:
            word = word_data["word"]
            if word not in seen:
                seen.add(word)
                unique_words.append(word_data)
        merged[category] = unique_words

    # Save merged file
    output_file = data_dir / "words.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\nMerge complete!")
    print(f"CET-4 words: {len(merged['cet4'])}")
    print(f"CET-6 words: {len(merged['cet6'])}")
    print(f"Total words: {len(merged['cet4']) + len(merged['cet6'])}")
    print(f"\nSaved to: {output_file}")

if __name__ == "__main__":
    merge_word_files()
