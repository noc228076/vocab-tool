#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add new words to the vocabulary database
"""

import json
from pathlib import Path

def add_word(word, phonetic, meaning, example, category="cet4"):
    """Add a single word to the database"""
    tools_dir = Path(__file__).parent
    data_dir = tools_dir.parent / "data"
    words_file = data_dir / "words.json"

    # Load existing words
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create new word entry
    new_word = {
        "word": word,
        "phonetic": phonetic,
        "meaning": meaning,
        "example": example,
        "category": category
    }

    # Check if word already exists
    for existing_word in data.get(category, []):
        if existing_word["word"].lower() == word.lower():
            print(f"Word '{word}' already exists in {category.upper()}")
            return False

    # Add word
    if category not in data:
        data[category] = []

    data[category].append(new_word)

    # Save updated words
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Added word '{word}' to {category.upper()}")
    return True

def add_words_from_file(file_path, category="cet4"):
    """Add words from a text file (one word per line, format: word|phonetic|meaning|example)"""
    tools_dir = Path(__file__).parent
    data_dir = tools_dir.parent / "data"
    words_file = data_dir / "words.json"

    # Load existing words
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if category not in data:
        data[category] = []

    # Read words from file
    added_count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('|')
            if len(parts) >= 3:
                word = parts[0].strip()
                phonetic = parts[1].strip()
                meaning = parts[2].strip()
                example = parts[3].strip() if len(parts) > 3 else ""

                # Check if word already exists
                exists = False
                for existing_word in data.get(category, []):
                    if existing_word["word"].lower() == word.lower():
                        exists = True
                        break

                if not exists:
                    new_word = {
                        "word": word,
                        "phonetic": phonetic,
                        "meaning": meaning,
                        "example": example,
                        "category": category
                    }
                    data[category].append(new_word)
                    print(f"Added: {word}")
                    added_count += 1
                else:
                    print(f"Skipped (exists): {word}")

    # Save updated words
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nAdded {added_count} words to {category.upper()}")
    print(f"Total words: {len(data.get(category, []))}")
    return True

def main():
    print("Add words to the vocabulary database")
    print("=" * 40)
    print("Format: word | phonetic | meaning | example (optional)")
    print("Type 'quit' to exit")
    print()

    while True:
        try:
            line = input("Enter word: ").strip()
            if line.lower() == 'quit':
                break

            parts = line.split('|')
            if len(parts) >= 3:
                word = parts[0].strip()
                phonetic = parts[1].strip()
                meaning = parts[2].strip()
                example = parts[3].strip() if len(parts) > 3 else ""

                category = input("Category (cet4/cet6): ").strip().lower()
                if category not in ['cet4', 'cet6']:
                    category = 'cet4'

                add_word(word, phonetic, meaning, example, category)
            else:
                print("Invalid format. Use: word | phonetic | meaning | example")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
