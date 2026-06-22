# -*- coding: utf-8 -*-
"""
瑞士制配对算法(纯函数,无 GUI 依赖,可单独单元测试)。

设计要点:
- 强弱排序键:(积分, 对手分, 后手数, 犯规数, -签号),从强到弱。
- 轮空(BYE):选手为奇数时,给"还没轮空过、且排名最低"的选手轮空。
  轮空用对手历史里的 0 标记(真实签号从 1 起,0 不会与任何人冲突),
  保证同一人不会被轮空两次。
- 回溯匹配:从最强选手开始,优先与"尽量强、且没下过"的对手配对;
  配不出时回溯换对手。若整体无解(都互相下过了),退化为相邻强制配对,
  绝不崩溃、绝不丢台。
- 颜色(先后手):后手数多的一方执先(红),后手数少的一方执后(黑),
  黑方本轮后手数 +1,以平衡先后手。
"""

BYE = 0  # 轮空标记(对手签号)


def _strength(s):
    """强弱排序键,越大越强。"""
    return (s["frac"], s["competfrac"], s["backcount"], s["foulcount"], -s["number"])


def _allowed(a, b, forbidden):
    """a、b 能否配对:没下过 且 不在 forbidden(同团队等附加禁配)里。"""
    if b["number"] in a["compets"] or a["number"] in b["compets"]:
        return False
    if forbidden and frozenset((a["number"], b["number"])) in forbidden:
        return False
    return True


def _match(pool, forbidden=None):
    """对已按强弱降序排列的 pool 做回溯匹配,返回 [(a,b),...] 或 None(无解)。"""
    if not pool:
        return []
    a = pool[0]
    for i in range(1, len(pool)):
        b = pool[i]
        if _allowed(a, b, forbidden):
            rest = pool[1:i] + pool[i + 1:]
            sub = _match(rest, forbidden)
            if sub is not None:
                return [(a, b)] + sub
    return None


def _colorize(a, b, color_by_number=False):
    """决定先后手,返回 (white_num, black_num)。
    默认:后手数多的一方执先(红),少者执后(黑),以平衡先后手。
    color_by_number=True(仅用于首轮):签号小者执红先走。"""
    if color_by_number:
        white, black = (a, b) if a["number"] < b["number"] else (b, a)
    elif a["backcount"] >= b["backcount"]:
        white, black = a, b
    else:
        white, black = b, a
    return white["number"], black["number"]


def pair_round(states, forbidden_pairs=None, color_by_number=False):
    """
    states: 选手状态列表,每项为 dict,含键:
        number, frac, competfrac, backcount, foulcount, compets(list[int])
    forbidden_pairs: 额外禁止配对的集合(frozenset({a,b}),如同团队首轮不相遇);仅首轮传入。
    color_by_number: True 时按签号定先后手(签号小者执红),仅首轮用。
    返回: [(white_num, black_num), ...];black_num == 0 表示轮空。
    不修改入参;副作用(对手列表、后手计数)由调用方按返回结果施加。
    """
    pool = sorted(states, key=_strength, reverse=True)

    bye_pair = None
    if len(pool) % 2 == 1:
        # 选还没轮空过、排名最低的选手轮空;若都轮空过则取最低者
        cand = [s for s in pool if BYE not in s["compets"]] or pool
        bye = min(cand, key=_strength)
        pool = [s for s in pool if s["number"] != bye["number"]]
        bye_pair = (bye["number"], BYE)

    matched = _match(pool, forbidden_pairs)
    if matched is None:
        # 无满足约束的完美匹配 → 相邻强制配对(可能违反约束),保证不崩
        matched = [(pool[i], pool[i + 1]) for i in range(0, len(pool), 2)]

    pairs = [_colorize(a, b, color_by_number) for a, b in matched]
    if bye_pair is not None:
        pairs.append(bye_pair)  # 轮空台放在最后
    return pairs


# --------------------------- 自测 ---------------------------
if __name__ == "__main__":
    def mk(num, frac=0, back=0, compets=None):
        return {"number": num, "frac": frac, "competfrac": 0,
                "backcount": back, "foulcount": 0, "compets": list(compets or [])}

    def check(name, cond):
        print(("  OK " if cond else ">>FAIL ") + name)
        assert cond, name

    # 1) 偶数:全部配对,无重复,无轮空
    st = [mk(i, frac=10 - i) for i in range(1, 7)]
    ps = pair_round(st)
    nums = [n for pair in ps for n in pair]
    check("偶数: 3 台", len(ps) == 3)
    check("偶数: 无轮空", BYE not in nums)
    check("偶数: 6 人各一次", sorted(nums) == [1, 2, 3, 4, 5, 6])

    # 2) 奇数:恰好一个轮空,其余正常
    st = [mk(i, frac=10 - i) for i in range(1, 6)]
    ps = pair_round(st)
    byes = [p for p in ps if p[1] == BYE]
    check("奇数: 1 个轮空", len(byes) == 1)
    check("奇数: 共 3 台(含轮空)", len(ps) == 3)
    real = [n for p in ps for n in p if n != BYE]
    check("奇数: 5 人各出现一次", sorted(real) == [1, 2, 3, 4, 5])

    # 3) 不重复对阵:1 已和 2 下过 → 不应再被配到一起
    st = [mk(1, frac=5, compets=[2]), mk(2, frac=5, compets=[1]),
          mk(3, frac=5), mk(4, frac=5)]
    ps = pair_round(st)
    pset = {frozenset(p) for p in ps}
    check("回溯: 1 与 2 不再相遇", frozenset({1, 2}) not in pset)
    check("回溯: 仍是 2 台", len(ps) == 2)

    # 4) 需要回溯:1 下过 2、3、4,只剩 2/3/4 可选其一;强制让算法绕开死路
    st = [mk(1, frac=9, compets=[2, 3]), mk(2, frac=8, compets=[1, 4]),
          mk(3, frac=7, compets=[1, 4]), mk(4, frac=6, compets=[2, 3])]
    ps = pair_round(st)
    pset = {frozenset(p) for p in ps}
    check("回溯2: 1 配到 4", frozenset({1, 4}) in pset)
    check("回溯2: 2 配到 3", frozenset({2, 3}) in pset)

    # 5) 无解退化:2 人已下过 → 仍返回 1 台(强制重复),不崩溃
    st = [mk(1, compets=[2]), mk(2, compets=[1])]
    ps = pair_round(st)
    check("无解退化: 不崩溃且 1 台", len(ps) == 1)

    # 6) 同一人不会轮空两次:已轮空过(compets 含 0)的最低分选手应被跳过
    st = [mk(1, frac=9), mk(2, frac=8), mk(3, frac=1, compets=[BYE])]
    ps = pair_round(st)
    bye_player = [p[0] for p in ps if p[1] == BYE][0]
    check("轮空不重复: 3 号(已轮空)不再轮空", bye_player != 3)

    print("\n全部通过 [PASS]")
