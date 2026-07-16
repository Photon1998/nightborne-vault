#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奈特的秘密金庫 — 密碼推理助手

規則:
  - 密碼為 1~9 之中「互不重複」的 3 位數 (共 9*8*7 = 504 種)
  - 每次輸入 3 個數字後會得到回饋:
      ● (bulls)  : 數字與位置皆完全一致
      ▲ (cows)   : 僅數字一致 (位置不正確)
      X          : 該位置數字完全不在密碼中
    通常回報形式為「幾個● 幾個▲」,X 的數量 = 3 - ● - ▲
  - 累計次數達特定次數時,系統會提示「不包含在密碼中的數字」

使用方式:
  python3 solver.py
  依畫面提示輸入你「實際在遊戲裡猜的 3 位數」與「得到的回饋」,
  程式會幫你篩掉不可能的答案,並建議下一步最佳猜測。
"""

from itertools import permutations
from collections import Counter


def all_candidates():
    """產生所有合法密碼: 1~9 互不重複的 3 位數。"""
    return [p for p in permutations("123456789", 3)]


def score(secret, guess):
    """回傳 (bulls ●, cows ▲)。"""
    bulls = sum(s == g for s, g in zip(secret, guess))
    # cows: 數字有出現但位置不同
    common = sum((Counter(secret) & Counter(guess)).values())
    cows = common - bulls
    return bulls, cows


def filter_candidates(cands, guess, bulls, cows):
    """只保留「若它是答案,對此 guess 也會給出相同回饋」的候選。"""
    return [c for c in cands if score(c, guess) == (bulls, cows)]


def best_guess(cands, pool=None):
    """
    以 minimax 選出資訊量最大的下一步猜測。
    對每個可能的猜測,計算它把候選集切成各種回饋群組後
    「最大群組」的大小,選最小者 (最壞情況剩最少)。
    優先從候選集內挑 (有機會直接猜中)。
    """
    if len(cands) <= 2:
        return cands[0]
    if pool is None:
        pool = cands
    best, best_worst = None, None
    cand_set = set(cands)
    for g in pool:
        buckets = Counter(score(c, g) for c in cands)
        worst = max(buckets.values())
        # tie-break: 優先選還在候選集內的猜測
        key = (worst, 0 if g in cand_set else 1)
        if best_worst is None or key < best_worst:
            best_worst, best = key, g
    return best


def parse_guess(text):
    digits = [ch for ch in text if ch.isdigit()]
    if len(digits) != 3 or len(set(digits)) != 3 or "0" in digits:
        return None
    return tuple(digits)


def parse_feedback(text):
    """
    支援多種輸入:
      '1 1'      -> ●=1, ▲=1
      '1,1'
      '●▲'       -> 用符號數
      '1b1c'
      'X' / 'x'  -> 0 0 (全不中)
    回傳 (bulls, cows) 或 None。
    """
    t = text.strip().lower()
    if t in ("x", "xxx", "0", "0 0"):
        return (0, 0)
    # 符號式
    bulls = t.count("●") + t.count("o") + t.count("b")
    cows = t.count("▲") + t.count("^") + t.count("c")
    if bulls or cows:
        if bulls + cows <= 3:
            return (bulls, cows)
        return None
    # 數字式: 取前兩個數字
    nums = [int(n) for n in "".join(c if c.isdigit() else " " for c in t).split()]
    if len(nums) >= 2 and nums[0] + nums[1] <= 3:
        return (nums[0], nums[1])
    if len(nums) == 1 and nums[0] <= 3:
        return (nums[0], 0)
    return None


def main():
    cands = all_candidates()
    print("=" * 48)
    print("  奈特的秘密金庫 — 密碼推理助手")
    print("=" * 48)
    print("密碼: 1~9 互不重複的 3 位數,共 {} 種可能\n".format(len(cands)))
    print("玩法: 腳本會直接叫你在遊戲裡輸入某組數字,")
    print("      你只要把遊戲回饋的 ● ▲ 告訴腳本即可。\n")
    print("回饋輸入:")
    print("  1 1    → ● 1 個, ▲ 1 個")
    print("  0 2    → ● 0 個, ▲ 2 個")
    print("  X      → 全部不中 (等同 0 0)")
    print("其他指令:")
    print("  no 258 → 系統提示時,排除不在密碼中的數字 2、5、8")
    print("  list   → 列出目前所有可能答案")
    print("  quit   → 離開\n")

    turn = 0
    while True:
        if len(cands) == 0:
            print("⚠️  沒有符合的答案了 — 請檢查先前輸入的回饋是否有誤。")
            break
        if len(cands) == 1:
            print("\n🎯 密碼就是: {} — 直接輸入它!".format("".join(cands[0])))
            break

        # 腳本直接給出這一手要猜的數字
        guess = best_guess(cands)
        turn += 1
        print("─" * 48)
        print("第 {} 手 → 請在遊戲裡輸入: 【 {} 】   (剩 {} 種可能)".format(
            turn, "".join(guess), len(cands)))

        raw = input("回饋 (● ▲,如 '1 1' / 'X') > ").strip()
        low = raw.lower()

        if low in ("quit", "q", "exit"):
            break
        if low in ("list", "l"):
            preview = ["".join(c) for c in cands[:60]]
            print("可能答案 ({}): {}{}".format(
                len(cands), " ".join(preview),
                " ..." if len(cands) > 60 else ""))
            turn -= 1
            continue
        if low.startswith("no"):
            bad = [ch for ch in raw if ch.isdigit()]
            if not bad:
                print("用法: no 258")
                turn -= 1
                continue
            before = len(cands)
            cands = [c for c in cands if not any(b in c for b in bad)]
            print("已排除含 {} 的答案: {} -> {} 種".format(
                "、".join(bad), before, len(cands)))
            turn -= 1
            continue

        fb = parse_feedback(raw)
        if fb is None:
            print("✗ 回饋格式錯誤。範例: 1 1 / 0 2 / X")
            turn -= 1
            continue

        bulls, cows = fb
        if (bulls, cows) == (3, 0):
            print("🎉 猜中了! 密碼就是 {}".format("".join(guess)))
            break

        before = len(cands)
        cands = filter_candidates(cands, guess, bulls, cows)
        print("  {} → ●{} ▲{}  |  候選 {} -> {} 種".format(
            "".join(guess), bulls, cows, before, len(cands)))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n再見!")
