from janome.tokenizer import Tokenizer, Token
from collections import defaultdict

tokenizer = Tokenizer()

sentences = [
    "変な話今日は雨が降りそう",
    "変な人"
]

MAX_NGRAM_N = 5


def ngram(tokens: list[Token], n: int) -> list[str]:
    grams = []
    for i in range(len(tokens)):
        gram = ""
        for j in range(n):
            idx = i + j
            if idx < len(tokens):
                gram += tokens[idx].surface
        grams.append(gram)
    return grams


def enumerate_ngram_candidates(input_texts: list[str]) -> list[str]:
    ngram_to_text_set = defaultdict(lambda: set())
    for i, text in enumerate(input_texts):
        tokens = list(tokenizer.tokenize(text))
        for j in range(1, MAX_NGRAM_N):
            jgram = ngram(tokens, j)
            for jg in jgram:
                ngram_to_text_set[jg].add(i)  # 同一文章では同じトークンを最大1回しかカウントしないように制限する
    ngram_candidates = []
    for g, texts in ngram_to_text_set.items():
        if len(texts) > 1:
            ngram_candidates.append(g)
    return ngram_candidates


# 筆者が形態素を出現させた頻度
# s_id_to_w_to_count: 筆者idとその筆者の形態素列と回数
# w: 形態素
# s_id: 筆者id
def calc_tf(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str):
    total_w_count = 0
    for s_to_count in s_id_to_w_to_count.values():
        for count in s_to_count.values():
            total_w_count += count
    return s_id_to_w_to_count[s_id][w] / total_w_count


def calc_fp1(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str) -> int:
    all_s_tf = 0
    for _s_id in s_id_to_w_to_count.keys():
        all_s_tf += calc_tf(s_id_to_w_to_count, w, _s_id)
    return pow(calc_tf(s_id_to_w_to_count, w, s_id), 2) / all_s_tf

# print(enumerate_ngram_candidates(sentences))
