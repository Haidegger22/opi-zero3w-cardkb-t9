#!/usr/bin/env python3
"""Генерация Т9-базы для русского языка из частотного словаря.

Источник: hermitdave/FrequencyWords (ru_50k.txt) — открытая лицензия.
Формат выхода: JSON {"последовательность_цифр": ["слово1", "слово2", ...]}
Слова отсортированы по частоте (лучший кандидат первый).
Ё нормализуется в Е.
"""
import json
import sys

T9_LAYOUT = {
    '2': 'абвг',
    '3': 'дежз',
    '4': 'ийкл',
    '5': 'мноп',
    '6': 'рсту',
    '7': 'фхцч',
    '8': 'шщъы',
    '9': 'ьэюя',
}
KEY_OF = {}
for k, letters in T9_LAYOUT.items():
    for ch in letters:
        KEY_OF[ch] = k
KEY_OF['ё'] = '3'  # ё рядом с е

RU = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ru_50k.txt'
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    out = sys.argv[3] if len(sys.argv) > 3 else '/home/orangepi/.openclaw/workspace/t9/ru_t9.json'

    words = []
    for line in open(src, encoding='utf-8'):
        parts = line.rstrip('\n').split(' ')
        if len(parts) != 2 or not parts[0]:
            continue
        w = parts[0].lower().replace('ё', 'е')
        if w and all(c in RU for c in w):
            words.append((w, int(parts[1])))

    words.sort(key=lambda x: -x[1])
    words = words[:top_n]

    seq_map = {}
    for w, _f in words:
        seq = ''.join(KEY_OF[c] for c in w)
        lst = seq_map.setdefault(seq, [])
        if w not in lst:      # ё→е может дать дубликат ('моё' и 'мое')
            lst.append(w)

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(seq_map, f, ensure_ascii=False, separators=(',', ':'))

    n_coll = sum(1 for v in seq_map.values() if len(v) > 1)
    print(f'слов в базе: {len(words)}')
    print(f'последовательностей: {len(seq_map)}, с коллизиями: {n_coll}')
    print(f'размер файла: {__import__("os").path.getsize(out)} байт -> {out}')


if __name__ == '__main__':
    main()
