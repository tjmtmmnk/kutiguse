import json
import os
import math

from janome.tokenizer import Tokenizer, Token
from collections import defaultdict

tokenizer = Tokenizer()

sentences = [
    'しばくぞお前何してんねん',
    '何してんねん',
    'しばくぞお前何やねん挨拶って',
    'どっか行こか',
    'どこ行く',
    'しばくぞお前。何考えてんねん',
    'しばくぞお前。なんで俺がお前に高級寿司奢らなあかんねん',
    'しばくぞお前。一人で行って来い',
    'なんで俺がお前とハワイ行かなあかんねん。それやったらええ女連れて行くわ。しばくぞお前',
    'おお、行ったん',
    'しばいたろかお前、なんでお前みたいなんがハワイ行けんねん。それやったら俺連れて行け。しばくぞお前',
    'どう良かってん。しばくぞお前',
    'しばくぞお前。彼女おるんかい。俺はおらんっちゅうねん。しばくぞお前',
    'ワイキキ？やっばどんなんやったん',
    'しばくぞお前。包み隠さず言えよ',
    '何泊で行ってん。しばくぞお前ちょっと考えたやろお前。短めで言うたやろ',
    'しばくぞお前。なんやねんテレビで見たままって。ほな俺テレビで見とけって言うんかい',
    '俺はハワイ行かんでええ言うてるんやろ',
    'しばくぞお前。隠すなよ',
    'やっぱ１億くらい？',
    'しばくぞお前。ちゃんと突っ込めよ',
    'お前ボケたときちゃんと突っ込んだってんねんから',
    '俺どこの国が合うかな',
    'しばくぞお前。なんで急にアフリカくんねん',
    'しばくぞお前。どこがやねん',
    '実際どうなん',
    'しばくぞお前。どんだけ厚着して行かなあかんねん。オーロラ見に行くのかよ',
    'しばくぞお前。北極行くやつおるかい。あれ陸ないらしいで',
    '日本やったらどこやねん',
    'しばくぞお前。絶対考えてるやん',
    'しばくぞお前。結局アフリカかい',  # 口癖に突っ込む 2:26 まで
]

MAX_NGRAM_N = 5


def tokenize(text: str) -> list[Token]:
    return list(tokenizer.tokenize(text))


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
        tokens = tokenize(text)
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
def calc_tf(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str) -> float:
    total_w_count = 0
    for s_to_count in s_id_to_w_to_count.values():
        for count in s_to_count.values():
            total_w_count += count
    return s_id_to_w_to_count[s_id][w] / total_w_count


def calc_fp1(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str) -> float:
    all_s_tf = 0
    for _s_id in s_id_to_w_to_count.keys():
        all_s_tf += calc_tf(s_id_to_w_to_count, w, _s_id)
    return pow(calc_tf(s_id_to_w_to_count, w, s_id), 2) / all_s_tf if all_s_tf > 0 else 1


def calc_fp2(s_id_to_w_to_count: dict[str, dict[str, int]], w: str) -> float:
    s_count = 0
    for s_id in s_id_to_w_to_count.keys():
        for _w in s_id_to_w_to_count[s_id].keys():
            if _w == w:
                s_count += 1
                break
    return 1 / (-s_count * ((1 / s_count) * (math.log2(1 / s_count))) + 1) if s_count > 0 else 1


def calc_fp4(s_id_to_w_to_left_right: dict[str, dict[str, list[str, str]]], w: str) -> float:
    left_to_count = defaultdict(lambda: 0)
    right_to_count = defaultdict(lambda: 0)
    for w_to_left_right in s_id_to_w_to_left_right.values():
        try:
            left_to_count[w_to_left_right[w][0]] += 1
            right_to_count[w_to_left_right[w][1]] += 1
        except KeyError:
            continue

    left_total = sum(left_to_count.values())
    left_entropy = 0
    for left_count in left_to_count.values():
        left_entropy -= (left_count / left_total) * math.log2(left_count / left_total)

    right_total = sum(right_to_count.values())
    right_entropy = 0
    for right_count in right_to_count.values():
        right_entropy -= (right_count / right_total) * math.log2(right_count / right_total)

    return math.sqrt(left_entropy * right_entropy)


# print(enumerate_ngram_candidates(sentences))


if __name__ == '__main__':
    filenames = os.listdir('data')
    s_id_to_w_to_count = {}
    s_id_to_w_to_left_right = {}

    for filename in filenames[0:100]:
        with open(os.path.join('data', filename), mode="r") as f:
            saved_list: list = json.loads(f.read())
            for sl in saved_list:
                w_to_count = defaultdict(lambda: 0)
                w_to_left_right = defaultdict(lambda: [''] * 2)
                for grams in sl["ngram_list"]:
                    for i in range(len(grams)):
                        morpheme = grams[i]
                        w_to_count[morpheme] += 1
                        if i - 1 > -1:
                            w_to_left_right[morpheme][0] = grams[i - 1]
                        if i + 1 < len(grams):
                            w_to_left_right[morpheme][1] = grams[i + 1]

                s_id_to_w_to_count[sl["author_id"]] = w_to_count
                s_id_to_w_to_left_right[sl["author_id"]] = w_to_left_right

    candidates = enumerate_ngram_candidates(sentences)

    w_to_count = defaultdict(lambda: 0)
    for text in sentences:
        tokens = tokenize(text)
        for i in range(1, 5):
            for morpheme in ngram(tokens, i):
                w_to_count[morpheme] += 1

    s_id_to_w_to_count["me"] = w_to_count

    cand_with_fp = []
    for cand in candidates:
        fp1 = calc_fp1(s_id_to_w_to_count, cand, "me")
        fp2 = calc_fp2(s_id_to_w_to_count, cand)
        fp4 = calc_fp4(s_id_to_w_to_left_right, cand)
        fp = fp1 * fp2 * (1 / fp4 if fp4 > 1 else fp4 if fp4 > 0 else 1)
        cand_with_fp.append({
            "morpheme": cand,
            "fp": fp,
        })

    for i, c in enumerate(sorted(cand_with_fp, key=lambda x: x["fp"], reverse=True)):
        print(f'{i}位: {c["morpheme"]}')
