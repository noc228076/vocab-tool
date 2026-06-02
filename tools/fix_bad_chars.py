"""Fix actual corrupted characters in phonetics (fullwidth semicolon, etc.)"""
import json
from pathlib import Path

words_file = Path(__file__).parent.parent / "data" / "words.json"
data = json.load(open(words_file, 'r', encoding='utf-8'))

fixed = 0
for cat in ('cet4', 'cet6', 'custom'):
    for w in data.get(cat, []):
        ph = w.get('phonetic', '')
        if not ph:
            continue
        new_ph = ph.replace('\uff1b', ';')
        # also check for any truly non-IPA characters
        if new_ph != ph:
            w['phonetic'] = new_ph
            fixed += 1
            print(f"Fixed: {w['word']}")

json.dump(data, open(words_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"Fixed {fixed} words")
Path('tmp_bad_fixed.txt').write_text(str(fixed), encoding='utf-8')
