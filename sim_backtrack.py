# -*- coding: utf-8 -*-
"""
回溯需求分析 / 配对算法回归测试脚本
====================================

用途
----
模拟瑞士制赛事,实测每一轮里:
  1) 贪心(无回溯)会"卡住"的比例 —— 即:强者优先取最强的"没下过"对手时,
     是否会走到某个选手已无任何合法对手的死胡同(此时就需要回溯)。
  2) 是否存在"无重复对阵"的完美匹配 —— 由 Dirac 定理,r <= N/2 时必然存在;
     若不存在,则连回溯也只能被迫安排一次重复对阵(属赛制轮数过多)。

结论速览(随机赛果下):前 2~3 轮用不到回溯;之后急剧上升,赛事后半程
绝大多数轮次都需要回溯。这解释了为何旧代码"从没触发回溯"——它的回溯
触发条件几乎不可达,真正该回溯的局面被静默地配成了重复对阵。

运行
----
    venv\\Scripts\\python.exe sim_backtrack.py

依赖本目录的 pairing.py(正式使用的配对算法,带可用的回溯)。
本脚本既是分析工具,也可当作 pairing.py 的回归测试:
若哪天改了配对算法,"无解(被迫重复)%"在 r <= N/2 时应始终为 0。
"""
import random
import copy
import sys

import pairing

# Windows 控制台中文输出兼容
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def strength(s):
    return pairing._strength(s)


def _drop_bye(pool):
    """与 pairing.pair_round 一致的轮空处理:奇数时摘掉排名最低、且未轮空过的人。"""
    pool = sorted(pool, key=strength, reverse=True)
    if len(pool) % 2 == 1:
        cand = [s for s in pool if pairing.BYE not in s["compets"]] or pool
        bye = min(cand, key=strength)
        pool = [s for s in pool if s["number"] != bye["number"]]
    return pool


def greedy_stuck(states):
    """贪心(无回溯):强者优先取最强的'没下过'对手。返回 True 表示中途卡住。"""
    pool = list(_drop_bye(states))
    while pool:
        a = pool.pop(0)
        chosen = None
        for i, b in enumerate(pool):  # pool 已按强弱降序 → 第一个合法者即最强合法对手
            if b["number"] not in a["compets"] and a["number"] not in b["compets"]:
                chosen = i
                break
        if chosen is None:
            return True
        pool.pop(chosen)
    return False


def clean_matching_exists(states):
    """是否存在无重复对阵的完美匹配(回溯能否找到干净解)。"""
    return pairing._match(_drop_bye(states)) is not None


def _new_players(n):
    return [{"number": i, "frac": 0, "competfrac": 0, "backcount": 0,
             "foulcount": 0, "compets": []} for i in range(1, n + 1)]


def simulate(n, rounds, trials):
    """返回每轮 (贪心卡住次数, 无解次数, 样本数)。"""
    stuck = [0] * (rounds + 1)
    impossible = [0] * (rounds + 1)
    cnt = [0] * (rounds + 1)
    for _ in range(trials):
        players = _new_players(n)
        for r in range(1, rounds + 1):
            cnt[r] += 1
            if greedy_stuck(copy.deepcopy(players)):
                stuck[r] += 1
            if not clean_matching_exists(copy.deepcopy(players)):
                impossible[r] += 1
            # 用正式的回溯算法配对并推进赛事(随机赛果)
            pairs = pairing.pair_round(players)
            by = {p["number"]: p for p in players}
            for w, b in pairs:
                if b == pairing.BYE:
                    by[w]["frac"] += 2
                    by[w]["compets"].append(pairing.BYE)
                    continue
                res = random.choice([1, 2, 3])  # 1红胜 2和 3黑胜
                by[w]["frac"] += {1: 2, 2: 1, 3: 0}[res]
                by[b]["frac"] += {1: 0, 2: 1, 3: 2}[res]
                by[w]["compets"].append(b)
                by[b]["compets"].append(w)
                by[b]["backcount"] += 1
            for p in players:  # 重算对手分
                p["competfrac"] = sum(by[o]["frac"] for o in p["compets"]
                                      if o != pairing.BYE)
    return stuck, impossible, cnt


def report(n, rounds, trials):
    stuck, imp, cnt = simulate(n, rounds, trials)
    print(f"\n==== N={n} 选手, R={rounds} 轮, {trials} 次模拟 (N/2={n / 2:.0f}) ====")
    print(" 轮次 | 贪心需回溯% | 无解(被迫重复)%")
    for r in range(1, rounds + 1):
        s = 100 * stuck[r] / cnt[r]
        i = 100 * imp[r] / cnt[r]
        mark = "  <<<" if s > 0 else ""
        print(f"  {r:>3} |   {s:6.2f}   |   {i:6.2f}{mark}")


# 可按需增删:数量级覆盖小到大的赛事
CONFIGS = [
    (8, 7, 5000),
    (16, 9, 3000),
    (30, 11, 2000),
    (60, 11, 800),
    (100, 13, 300),
]

if __name__ == "__main__":
    random.seed(42)  # 固定随机种子,结果可复现
    for n, rounds, trials in CONFIGS:
        report(n, rounds, trials)
