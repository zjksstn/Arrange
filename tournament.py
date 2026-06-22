# -*- coding: utf-8 -*-
"""
赛事数据模型(与界面无关,可单独测试)
======================================
两层结构:
  Event 赛事   —— 容器:赛事名 + 裁判长 + 多个 Group
  Group 组别   —— 一套独立的瑞士制(选手/轮次/积分/锁定/撤销/打印),互不影响
                  公开组、女子组、少儿组就是同一个 Event 下的三个 Group。

配对算法来自 pairing.py;存档为 events/<赛事名>.json(嵌套各组)。
读取时自动兼容第⑥步的"单组"老格式(包成含一个"公开组"的赛事)。
"""
import os
import json
import random

import pairing

APP_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_DIR = os.path.join(APP_DIR, "events")


class Player:
    def __init__(self, number, name, team="个人"):
        self.number = number
        self.name = name
        self.team = team
        # 报名信息(花名册)
        self.gender = "男"      # 性别,默认男
        self.rating = 0.0       # 等级分,默认 0.0
        self.kvalue = 0         # K值,默认 0
        self.idcard = ""        # 身份证号(可选)
        self.phone = ""         # 电话(可选)
        self.avatar = ""        # 头像路径(预留)
        self.withdrawn = False  # 是否已退赛
        # 赛事过程数据
        self.frac = 0           # 积分
        self.competfrac = 0     # 对手分
        self.backcount = 0      # 后手(执黑)累计数
        self.foulcount = 0      # 犯规数
        self.compets = []       # 已对阵过的对手签号(pairing 用 0 标记轮空)


class Board:
    """一台对局:红方 + 黑方(black 为 None 表示轮空) + 结果。"""
    def __init__(self, tai, red, black):
        self.tai = tai
        self.red = red
        self.black = black      # None = 轮空
        self.result = 0         # 0 未登分 / 1 红胜 / 2 和 / 3 黑胜

    @property
    def is_bye(self):
        return self.black is None


class Group:
    """一个组别 = 一套独立瑞士制(原 Tournament,裁判长上移到 Event)。"""

    def __init__(self, name, players, total_rounds=0):
        self.name = name
        self.total_rounds = total_rounds
        self.players = players
        self.rounds = []            # list[list[Board]];最后一项=当前可编辑轮
        self.finished = False       # 是否已结算(计算最终成绩、比赛结束)
        self.opt_same_team = False  # 抽签附加条件(仅作用首轮):同团队不相遇
        self.opt_lower_red = False  # 抽签附加条件(仅作用首轮):签号小者持红先走

    @classmethod
    def from_roster(cls, name, names, total_rounds=0):
        """根据姓名列表创建组别(报名阶段,编号=录入顺序,尚未抽签编排)。"""
        players = [Player(i + 1, nm) for i, nm in enumerate(names)]
        return cls(name, players, total_rounds)

    @property
    def started(self):
        """是否已开赛(已抽签编排首轮)。"""
        return len(self.rounds) > 0

    def add_player(self, name, **fields):
        """报名阶段添加一名选手,自动分配下一个编号。"""
        num = max((p.number for p in self.players), default=0) + 1
        p = Player(num, name)
        for k, v in fields.items():
            setattr(p, k, v)
        self.players.append(p)
        return p

    def remove_player(self, number):
        self.players = [p for p in self.players if p.number != number]

    def draw_lots(self):
        """抽签:给所有选手随机分配签号(只在开赛前有效)。"""
        nums = list(range(1, len(self.players) + 1))
        random.shuffle(nums)
        for p, n in zip(self.players, nums):
            p.number = n
        self.players.sort(key=lambda p: p.number)

    def start(self, same_team_avoid=False, lower_number_red=False):
        """开赛:抽签 + 编排首轮。附加条件仅作用首轮,后续轮完全依算法。"""
        self.opt_same_team = same_team_avoid
        self.opt_lower_red = lower_number_red
        self.draw_lots()
        forbidden = self._same_team_pairs() if same_team_avoid else None
        return self.pair_next_round(forbidden_pairs=forbidden, color_by_number=lower_number_red)

    @property
    def current_round(self):
        return len(self.rounds)

    @property
    def boards(self):
        return self.rounds[-1] if self.rounds else []

    @property
    def done_count(self):
        return sum(1 for b in self.boards if b.is_bye or b.result != 0)

    @property
    def all_scored(self):
        return self.boards and all(b.is_bye or b.result != 0 for b in self.boards)

    @property
    def has_next_round(self):
        return self.current_round < self.total_rounds

    @property
    def active_players(self):
        """在册(未退赛)选手 —— 只有他们参与配对。"""
        return [p for p in self.players if not p.withdrawn]

    def _same_team_pairs(self):
        """在册选手中,所有"同团队(非默认个人)"的两两组合 → 禁配集合。"""
        forbidden = set()
        ps = self.active_players
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                t = ps[i].team
                if t and t != "个人" and t == ps[j].team:
                    forbidden.add(frozenset((ps[i].number, ps[j].number)))
        return forbidden

    def pair_next_round(self, forbidden_pairs=None, color_by_number=False):
        states = [{"number": p.number, "frac": p.frac, "competfrac": p.competfrac,
                   "backcount": p.backcount, "foulcount": p.foulcount,
                   "compets": list(p.compets)} for p in self.active_players]
        pairs = pairing.pair_round(states, forbidden_pairs=forbidden_pairs,
                                   color_by_number=color_by_number)
        by = {p.number: p for p in self.players}
        boards = []
        for tai, (w, b) in enumerate(pairs, start=1):
            red = by[w]
            black = None if b == pairing.BYE else by[b]
            boards.append(Board(tai, red, black))
        self.rounds.append(boards)
        return boards

    def _apply(self, boards):
        for b in boards:
            if b.is_bye:
                b.red.frac += 2
                b.red.compets.append(pairing.BYE)
                continue
            if b.result == 1:
                b.red.frac += 2
            elif b.result == 2:
                b.red.frac += 1
                b.black.frac += 1
            elif b.result == 3:
                b.black.frac += 2
            b.red.compets.append(b.black.number)
            b.black.compets.append(b.red.number)
            b.black.backcount += 1
        self._recompute_competfrac()

    def _unapply(self, boards):
        for b in boards:
            if b.is_bye:
                b.red.frac -= 2
                if b.red.compets and b.red.compets[-1] == pairing.BYE:
                    b.red.compets.pop()
                continue
            if b.result == 1:
                b.red.frac -= 2
            elif b.result == 2:
                b.red.frac -= 1
                b.black.frac -= 1
            elif b.result == 3:
                b.black.frac -= 2
            if b.red.compets:
                b.red.compets.pop()
            if b.black.compets:
                b.black.compets.pop()
            b.black.backcount -= 1
        self._recompute_competfrac()

    def _recompute_competfrac(self):
        by = {p.number: p for p in self.players}
        for p in self.players:
            p.competfrac = sum(by[o].frac for o in p.compets if o != pairing.BYE)

    def record_and_advance(self):
        self._apply(self.boards)
        return self.pair_next_round()

    def undo_last_round(self):
        if len(self.rounds) < 2:
            return False
        self.rounds.pop()
        self._unapply(self.rounds[-1])
        return True

    def re_pair_current(self):
        """重排当前(未结束)轮:丢弃当前轮,按在册选手重新配对。
        仅用于当前轮"未发布/未登分"时(退赛、复赛、首轮重抽后调用)。
        若重排的是首轮,则沿用抽签附加条件(同团队不相遇 / 签号小者持红)。"""
        if self.rounds:
            self.rounds.pop()
        if len(self.rounds) == 0:                 # 即将重排的是首轮
            forbidden = self._same_team_pairs() if self.opt_same_team else None
            return self.pair_next_round(forbidden_pairs=forbidden, color_by_number=self.opt_lower_red)
        return self.pair_next_round()

    def withdraw(self, numbers):
        """退赛:把这些签号标记为退赛,并重排当前轮(把他们移出对阵)。"""
        s = set(numbers)
        for p in self.players:
            if p.number in s:
                p.withdrawn = True
        return self.re_pair_current()

    def reenter(self, numbers):
        """复赛:把这些签号恢复参赛,并重排当前轮。"""
        s = set(numbers)
        for p in self.players:
            if p.number in s:
                p.withdrawn = False
        return self.re_pair_current()

    def redraw_first_round(self):
        """首轮重新抽签:重新洗签号并重排首轮(丢弃当前首轮)。仅 current_round==1 时有效。
        首轮尚未结算,选手对手记录为空,故重抽是干净的。"""
        if self.current_round != 1:
            return None
        self.draw_lots()
        return self.re_pair_current()

    def finish(self):
        """计算最终成绩、结束比赛:计入最后一轮成绩并标记结算。可被 unfinish 撤销。"""
        if self.finished or not self.started:
            return False
        self._apply(self.boards)
        self.finished = True
        return True

    def unfinish(self):
        """撤销结算:把最后一轮成绩从积分中撤回,回到可继续操作的状态。"""
        if not self.finished:
            return False
        self._unapply(self.boards)
        self.finished = False
        return True

    def _round_points(self):
        """每个签号每一轮所得分:{number: [r0, r1, ...]}。胜2/和1/负0/轮空2。"""
        pts = {p.number: [0] * len(self.rounds) for p in self.players}
        for r, rd in enumerate(self.rounds):
            for b in rd:
                if b.is_bye:
                    pts[b.red.number][r] = 2
                elif b.result == 1:
                    pts[b.red.number][r] = 2
                elif b.result == 2:
                    pts[b.red.number][r] = 1
                    pts[b.black.number][r] = 1
                elif b.result == 3:
                    pts[b.black.number][r] = 2
        return pts

    def progressive(self):
        """累进分:每轮累计分逐轮求和(标准破同分法)。{number: 累进分}。"""
        pts = self._round_points()
        prog = {}
        for num, lst in pts.items():
            s = total = 0
            for v in lst:
                s += v          # 该轮结束时的累计分
                total += s      # 累进分 = 各轮累计分之和
            prog[num] = total
        return prog

    def standings(self):
        """最终名次。破同分层级:
        积分 → 对手分 → 后手局数(多者先) → 犯规数(少者先) → 累进分(高者先) → 签号。
        返回 [(名次, player, 备注, 高亮列集合), ...]。高亮列 ∈ {后手, 犯规, 备注},
        即靠这几项破同分时把对应单元格标红,让人一眼看出区别所在。"""
        prog = self.progressive()

        def key(p):
            # reverse=True 下,元组越大名次越前;故犯规取负、签号取负(小号靠前)
            return (p.frac, p.competfrac, p.backcount, -p.foulcount,
                    prog[p.number], -p.number)

        ranked = sorted(self.players, key=key, reverse=True)
        notes = [""] * len(ranked)
        hl = [set() for _ in ranked]

        for i in range(1, len(ranked)):
            a, b = ranked[i - 1], ranked[i]
            if a.frac != b.frac:            # 积分不同 → 无需破同分
                continue
            if a.competfrac != b.competfrac:
                col = "对手分"               # 用户未要求高亮(对手分是常规可见项)
            elif a.backcount != b.backcount:
                col = "后手"
            elif a.foulcount != b.foulcount:
                col = "犯规"
            elif prog[a.number] != prog[b.number]:
                col = "备注"
                notes[i - 1] = notes[i - 1] or "累进分%d" % prog[a.number]
                notes[i] = "累进分%d" % prog[b.number]
            else:
                col = "备注"
                notes[i - 1] = notes[i - 1] or "签号"
                notes[i] = "签号"
            if col in ("后手", "犯规", "备注"):     # 这三类破同分 → 标红高亮(两行都标)
                hl[i].add(col)
                hl[i - 1].add(col)
        return [(i + 1, p, notes[i], hl[i]) for i, p in enumerate(ranked)]

    def pdf_rows(self):
        rows = []
        for b in self.boards:
            if b.is_bye:
                rows.append([str(b.tai), str(b.red.number), b.red.team, b.red.name,
                             str(b.red.frac), "", "—", "轮空", "—", "0", ""])
            else:
                rows.append([str(b.tai), str(b.red.number), b.red.team, b.red.name,
                             str(b.red.frac), "", str(b.black.frac), b.black.name,
                             b.black.team, str(b.black.number), ""])
        return rows


class Event:
    """赛事容器:赛事名 + 裁判长 + 若干组别。"""

    def __init__(self, name, judge="", groups=None):
        self.name = name
        self.judge = judge
        self.groups = groups if groups is not None else []

    def add_group(self, group):
        self.groups.append(group)
        return group

    def remove_group(self, index):
        del self.groups[index]

    def group_names(self):
        return [g.name for g in self.groups]


# ──────────────────────────── 存档(JSON) ────────────────────────────

def events_dir():
    os.makedirs(EVENTS_DIR, exist_ok=True)
    return EVENTS_DIR


def safe_filename(name):
    bad = '\\/:*?"<>|'
    return ("".join("_" if c in bad else c for c in name).strip()) or "未命名"


def event_path(name):
    return os.path.join(events_dir(), safe_filename(name) + ".json")


def _group_to_dict(g):
    return {
        "name": g.name, "total_rounds": g.total_rounds, "finished": g.finished,
        "opt_same_team": g.opt_same_team, "opt_lower_red": g.opt_lower_red,
        "players": [{"number": p.number, "name": p.name, "team": p.team,
                     "gender": p.gender, "rating": p.rating, "kvalue": p.kvalue,
                     "idcard": p.idcard, "phone": p.phone, "avatar": p.avatar,
                     "withdrawn": p.withdrawn,
                     "frac": p.frac, "competfrac": p.competfrac,
                     "backcount": p.backcount, "foulcount": p.foulcount,
                     "compets": list(p.compets)} for p in g.players],
        "rounds": [[{"tai": b.tai, "red": b.red.number,
                     "black": (None if b.is_bye else b.black.number),
                     "result": b.result} for b in rd] for rd in g.rounds],
    }


def _group_from_dict(d):
    players = []
    for pd in d["players"]:
        p = Player(pd["number"], pd["name"], pd.get("team", "个人"))
        p.gender = pd.get("gender", "男"); p.rating = pd.get("rating", 0.0)
        p.kvalue = pd.get("kvalue", 0)
        p.idcard = pd.get("idcard", ""); p.phone = pd.get("phone", "")
        p.avatar = pd.get("avatar", ""); p.withdrawn = pd.get("withdrawn", False)
        p.frac = pd["frac"]; p.competfrac = pd["competfrac"]
        p.backcount = pd["backcount"]; p.foulcount = pd["foulcount"]
        p.compets = list(pd["compets"])
        players.append(p)
    g = Group(d["name"], players, d.get("total_rounds", 0))
    g.finished = d.get("finished", False)
    g.opt_same_team = d.get("opt_same_team", False)
    g.opt_lower_red = d.get("opt_lower_red", False)
    by = {p.number: p for p in players}
    for rd in d["rounds"]:
        boards = []
        for bd in rd:
            red = by[bd["red"]]
            black = None if bd["black"] is None else by[bd["black"]]
            b = Board(bd["tai"], red, black); b.result = bd["result"]
            boards.append(b)
        g.rounds.append(boards)
    return g


def event_to_dict(e):
    return {"format": 2, "name": e.name, "judge": e.judge,
            "groups": [_group_to_dict(g) for g in e.groups]}


def event_from_dict(d):
    e = Event(d["name"], d.get("judge", ""))
    if "groups" in d:                       # 新格式(format 2)
        for gd in d["groups"]:
            e.add_group(_group_from_dict(gd))
    else:                                   # 第⑥步单组老格式 → 包成一个默认组
        e.add_group(_group_from_dict({
            "name": "公开组", "total_rounds": d.get("total_rounds", 0),
            "players": d["players"], "rounds": d["rounds"]}))
    return e


def save_event(e, path=None):
    path = path or event_path(e.name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event_to_dict(e), f, ensure_ascii=False, indent=1)
    return path


def load_event(path):
    with open(path, encoding="utf-8") as f:
        return event_from_dict(json.load(f))


def list_events():
    """返回 [(赛事名, 文件路径), ...]。"""
    d = events_dir()
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            p = os.path.join(d, fn)
            try:
                with open(p, encoding="utf-8") as f:
                    name = json.load(f).get("name", fn[:-5])
            except Exception:
                name = fn[:-5]
            out.append((name, p))
    return out


def list_events_with_groups():
    """返回 [(赛事名, 路径, [组别名, ...]), ...],供左栏二级树使用。"""
    out = []
    for name, p in list_events():
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            gnames = [g["name"] for g in d["groups"]] if "groups" in d else ["公开组"]
        except Exception:
            gnames = []
        out.append((name, p, gnames))
    return out


def delete_event(path):
    if os.path.exists(path):
        os.remove(path)


# ──────────────────────────── 历史名单读取 ────────────────────────────

def read_meta(folder):
    meta = {}
    with open(os.path.join(folder, "math_ini.txt"), encoding="utf-8") as f:
        for s in f:
            a = s.strip().split(maxsplit=1)
            if len(a) == 2:
                meta[a[0]] = a[1]
    return meta


def read_roster_names(folder):
    names = []
    with open(os.path.join(folder, "turn0.txt"), encoding="utf-8") as f:
        for line in f:
            a = line.split()
            if a:
                names.append(a[0])
    return names


def load_demo_event(folder):
    """首次运行的示例:从真实名单建一个含单个"公开组"的赛事。"""
    meta = read_meta(folder)
    names = read_roster_names(folder)
    total = int(meta.get("turn_total", "0") or 0)
    e = Event(meta.get("name", os.path.basename(folder)), judge=meta.get("judje", ""))
    g = Group.from_roster("公开组", names, total)
    g.start()                               # 示例直接开赛,首屏即显示对阵卡片
    e.add_group(g)
    return e


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    e = Event("职工比赛", judge="刘同喜")
    e.add_group(Group.from_roster("公开组", ["甲", "乙", "丙", "丁"], 5))
    e.add_group(Group.from_roster("女子组", ["A", "B", "C"], 3))
    for g in e.groups:
        g.pair_next_round()
    print("赛事:", e.name, "| 裁判:", e.judge, "| 组别:", e.group_names())
    for g in e.groups:
        print("  %s: %d人, 第%d轮 %d台" % (g.name, len(g.players), g.current_round, len(g.boards)))
