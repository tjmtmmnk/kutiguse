import json
from janome.tokenizer import Tokenizer

tokenizer = Tokenizer()

with open('words.txt', mode='r') as f:
    raw_words: str = f.read()
    words = raw_words.split(',')
    formatted_words = set()
    for w in words:
        tokens = tokenizer.tokenize(w)
        for t in tokens:
            formatted_words.add(t.surface)

with open('formatted-words.txt', mode='w') as f:
    f.write(json.dumps(list(formatted_words), ensure_ascii=False))
