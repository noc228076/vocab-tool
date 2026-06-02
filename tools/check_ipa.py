import json
data = json.load(open('data/words.json', encoding='utf-8'))
valid_ipa = set('/abcdefghijklmnopqrstuvwxyzˈˌːəɜrʃθŋæɪɒɑɡʒʌʊɔ')
suspicious = []
for cat in ('cet4', 'cet6', 'custom'):
    for w in data.get(cat, []):
        ph = w.get('phonetic', '').strip()
        if not ph:
            continue
        for ch in ph:
            if ch not in valid_ipa and ord(ch) > 127:
                suspicious.append((cat, w['word'], ph, repr(ch), hex(ord(ch))))
with open('tmp_ipa_check.txt', 'w', encoding='utf-8') as f:
    if suspicious:
        f.write(f"Found {len(suspicious)} suspicious chars:\n")
        for s in suspicious:
            f.write(str(s) + '\n')
    else:
        f.write("No suspicious non-IPA chars found")
