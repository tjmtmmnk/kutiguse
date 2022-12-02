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
    '旅費は？',
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


# return
# { morpheme => str, count => int }
def enumerate_ngram_candidates(input_texts: list[str]) -> list[dict]:
    morpheme_to_text_set = defaultdict(lambda: set())
    for i, text in enumerate(input_texts):
        tokens = tokenize(text)
        for j in range(1, MAX_NGRAM_N):
            for m in ngram(tokens, j):
                morpheme_to_text_set[m].add(i)  # 同一文章では同じトークンを最大1回しかカウントしないように制限する
    candidates = []
    for m, texts in morpheme_to_text_set.items():
        if len(texts) > 1:
            candidates.append({
                "morpheme": m,
                "count": len(texts),
            })
    return candidates


# s_id_to_w_to_count: 筆者idとその筆者の形態素列と回数
# w: 形態素
# s_id: 筆者id
def calc_fp1(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str) -> float:
    # 筆者が形態素を出現させた頻度
    def calc_tf(s_id_to_w_to_count: dict[str, dict[str, int]], w: str, s_id: str) -> float:
        total_w_count = sum(s_id_to_w_to_count[s_id].values())
        return s_id_to_w_to_count[s_id][w] / total_w_count

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

    def calc_entropy(x_to_count: dict[str, int]) -> float:
        total = sum(x_to_count.values())
        entropy = 0
        for count in x_to_count.values():
            entropy -= (count / total) * math.log2(count / total)
        return entropy

    left_entropy = calc_entropy(left_to_count)
    right_entropy = calc_entropy(right_to_count)

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
    for cand in candidates:
        w_to_count[cand["morpheme"]] += cand["count"]

    s_id_to_w_to_count["me"] = w_to_count

    # print(s_id_to_w_to_count["me"])

    cand_with_fp = []
    for cand in candidates:
        fp1 = calc_fp1(s_id_to_w_to_count, cand["morpheme"], "me")
        fp2 = calc_fp2(s_id_to_w_to_count, cand["morpheme"])
        fp4 = calc_fp4(s_id_to_w_to_left_right, cand["morpheme"])
        # print(f'{cand["morpheme"]}:\tfp1:{fp1}\tfp2:{fp2}\tfp4:{fp4}')
        fp = fp1 * fp2 * (1 / fp4 if fp4 > 1 else fp4 if fp4 > 0 else 5)
        cand_with_fp.append({
            "morpheme": cand["morpheme"],
            "fp": fp,
        })

    rank = 0
    last_fp = 0
    for c in sorted(cand_with_fp, key=lambda x: (x["fp"], len(x["morpheme"])), reverse=True):
        if c["fp"] != last_fp:
            rank += 1
        print(f'{rank}位:\tfp:{c["fp"]}\t{c["morpheme"]}')
        last_fp = c["fp"]
