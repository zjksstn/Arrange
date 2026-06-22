# -*- coding: utf-8 -*-
"""
对阵表 PDF 生成模块(跨平台:Windows / macOS)。

输入:报表按钮已生成的 turnNprint.txt，每行 9 字段:
    台号 红签号 红团队 红姓名 红积分 黑签号 黑团队 黑姓名 黑积分
输出:A4 纵向 PDF，11 列标准象棋对阵表(成绩、签名列留空供手填)。

字体:reportlab 自带的 STSong-Light(宋体类 CID 字体)，无需附带字体文件，
      Win/Mac 开箱即用。
"""

import os
import sys
import subprocess

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

FONT = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))

# 11 列表头与列宽(单位 mm，合计需 <= A4 可用宽度约 190mm)
HEADER = ["台号", "签号", "团队", "姓名", "积分", "成绩", "积分", "姓名", "团队", "签号", "签名"]
COL_W = [12, 12, 26, 20, 12, 22, 12, 20, 26, 12, 26]  # 合计 210mm? 见下方按比例缩放


def parse_print_txt(path):
    """解析 turnNprint.txt → 11 列展示行列表。容错处理可能存在的 ':' 分隔符。"""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            toks = [t for t in line.strip().split() if t and t != ":"]
            if len(toks) < 9:
                continue
            tai, fsign, fteam, fname, ffrac, bsign, bteam, bname, bfrac = toks[:9]
            fteam = fteam or "个人"   # 恰当的默认值(纯个人赛事)
            bteam = bteam or "个人"
            # 列顺序:台|红签|红团队|红名|红分|成绩|黑分|黑名|黑团队|黑签|签名
            rows.append([tai, fsign, fteam, fname, ffrac, "",
                         bfrac, bname, bteam, bsign, ""])
    return rows


# 团队列在 11 列中的下标(供 show_team=False 时整列隐藏)
_TEAM_COLS = (2, 8)


def _drop_team(seq):
    return [x for i, x in enumerate(seq) if i not in _TEAM_COLS]


def _scaled_widths(col_w, avail_mm):
    total = sum(col_w)
    return [w / total * avail_mm * mm for w in col_w]


def generate_pairing_pdf(rows, match_name, turn_no, out_path, judge="", show_team=True):
    """生成对阵表 PDF。
    rows: parse_print_txt() 的输出
    match_name: 赛事名称   turn_no: 轮次(从 1 开始)   judge: 裁判长(可空)
    show_team: 是否显示团队列。纯个人排名赛事可设 False 整列隐藏;双项排名赛事保持 True。
    """
    header = HEADER if show_team else _drop_team(HEADER)
    col_w = COL_W if show_team else _drop_team(COL_W)
    rows = rows if show_team else [_drop_team(r) for r in rows]
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title="%s 第%s轮对阵表" % (match_name, turn_no),
    )
    avail_mm = (A4[0] / mm) - 20  # 左右各 10mm
    widths = _scaled_widths(col_w, avail_mm)

    title_style = ParagraphStyle("title", fontName=FONT, fontSize=18,
                                 alignment=TA_CENTER, leading=24, spaceAfter=4)
    sub_style = ParagraphStyle("sub", fontName=FONT, fontSize=13,
                               alignment=TA_CENTER, leading=18, spaceAfter=8)

    story = [Paragraph(match_name, title_style),
             Paragraph("第 %s 轮对阵表" % turn_no, sub_style)]
    if judge:
        story.append(Paragraph("裁判长：%s" % judge, sub_style))

    table_data = [header] + rows
    tbl = Table(table_data, colWidths=widths, repeatRows=1)  # repeatRows=1 → 每页重复表头
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 11),       # 表头
        ("FONTSIZE", (0, 1), (-1, -1), 10),      # 数据
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.85, 0.85, 0.85)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    doc.build(story)
    return out_path


def table_pdf(out_path, title, subtitle, header, col_w, rows, judge=""):
    """通用"长表格"报表 PDF(A4、多页自动重复表头)。新报表只要给 表头/列宽/行 即可。
    title:赛事·组别;subtitle:报表名(如"选手花名册");rows:字符串行列表。"""
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title="%s %s" % (title, subtitle),
    )
    widths = _scaled_widths(col_w, (A4[0] / mm) - 20)
    title_style = ParagraphStyle("title", fontName=FONT, fontSize=18,
                                 alignment=TA_CENTER, leading=24, spaceAfter=4)
    sub_style = ParagraphStyle("sub", fontName=FONT, fontSize=13,
                               alignment=TA_CENTER, leading=18, spaceAfter=8)
    story = [Paragraph(title, title_style), Paragraph(subtitle, sub_style)]
    if judge:
        story.append(Paragraph("裁判长：%s" % judge, sub_style))
    tbl = Table([header] + rows, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.85, 0.85, 0.85)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    doc.build(story)
    return out_path


# 最终成绩表(列序同屏幕:姓名→…→名次)
STANDINGS_HEADER = ["姓名", "积分", "对手分", "后手", "犯规", "签号", "备注", "团队", "名次"]
STANDINGS_COL_W = [22, 12, 16, 12, 12, 12, 28, 22, 12]

# 选手花名册
ROSTER_HEADER = ["编号", "姓名", "性别", "团队", "身份证号", "电话", "等级分"]
ROSTER_COL_W = [12, 20, 12, 24, 30, 22, 14]


def generate_standings_pdf(rows, match_name, out_path, judge=""):
    """最终成绩表 PDF。rows 按 STANDINGS_HEADER 列序排好。"""
    return table_pdf(out_path, match_name, "最终成绩表", STANDINGS_HEADER, STANDINGS_COL_W, rows, judge)


def generate_roster_pdf(rows, match_name, out_path, judge=""):
    """选手花名册 PDF。rows 按 ROSTER_HEADER 列序排好。"""
    return table_pdf(out_path, match_name, "选手花名册", ROSTER_HEADER, ROSTER_COL_W, rows, judge)


def _card_grid(out_path, items, draw_card, cols, rows, bg_image=None):
    """通用"小卡网格"PDF:一页 cols×rows 张(可裁剪、自动翻页)。
    draw_card(canvas, x, y, w, h, item) 负责画每张卡的内容。新卡片报表只写 draw_card。"""
    from reportlab.pdfgen import canvas as _canvas
    c = _canvas.Canvas(out_path, pagesize=A4)
    pw, ph = A4
    margin, gap = 10 * mm, 6 * mm
    cw = (pw - 2 * margin - (cols - 1) * gap) / cols
    ch = (ph - 2 * margin - (rows - 1) * gap) / rows
    per_page = cols * rows
    have_bg = bool(bg_image) and os.path.exists(bg_image)
    for idx, item in enumerate(items):
        pos = idx % per_page
        if idx and pos == 0:
            c.showPage()
        col, row = pos % cols, pos // cols
        x = margin + col * (cw + gap)
        y = ph - margin - (row + 1) * ch - row * gap
        if have_bg:
            try:
                c.drawImage(bg_image, x, y, cw, ch, preserveAspectRatio=False, mask="auto")
            except Exception:
                c.roundRect(x, y, cw, ch, 6, stroke=1, fill=0)
        else:
            c.roundRect(x, y, cw, ch, 6, stroke=1, fill=0)
        draw_card(c, x, y, cw, ch, item)
    c.showPage()
    c.save()
    return out_path


def generate_tablecards_pdf(cards, match_name, out_path, bg_image=None, cols=2, rows=4):
    """台号卡:每张=台号 + 红方/黑方。cards:[{"tai","red","black"}, ...]。"""
    from reportlab.lib.colors import HexColor

    def draw(c, x, y, w, h, card):
        cx = x + w / 2
        c.setFillColor(HexColor("#2c2c2a")); c.setFont(FONT, 24)
        c.drawCentredString(cx, y + h - 30, "第 %s 台" % card["tai"])
        c.setFont(FONT, 14); c.setFillColor(HexColor("#c0392b"))
        c.drawCentredString(cx, y + h * 0.50, "红方  %s" % card["red"])
        c.setFont(FONT, 11); c.setFillColor(HexColor("#888880"))
        c.drawCentredString(cx, y + h * 0.38, "对")
        c.setFont(FONT, 14); c.setFillColor(HexColor("#2c2c2a"))
        c.drawCentredString(cx, y + h * 0.24, "黑方  %s" % card["black"])
        c.setFont(FONT, 9); c.setFillColor(HexColor("#888880"))
        c.drawCentredString(cx, y + 6, match_name)
    return _card_grid(out_path, cards, draw, cols, rows, bg_image)


def generate_scorecards_pdf(cards, match_name, out_path, cols=2, rows=3):
    """记分卡:每张=台号 + 红/黑方 + 成绩勾选 + 签名栏(供现场手工记录)。"""
    from reportlab.lib.colors import HexColor
    INK, GRAY, RED = HexColor("#2c2c2a"), HexColor("#888880"), HexColor("#c0392b")

    def draw(c, x, y, w, h, card):
        c.setFillColor(INK); c.setFont(FONT, 17)
        c.drawCentredString(x + w / 2, y + h - 26, "第 %s 台  记分卡" % card["tai"])
        c.setFont(FONT, 13)
        c.setFillColor(RED); c.drawString(x + 12, y + h * 0.60, "红方:%s" % card["red"])
        c.setFillColor(INK); c.drawString(x + 12, y + h * 0.44, "黑方:%s" % card["black"])
        c.drawString(x + 12, y + h * 0.27, "成绩:   红胜 □     和 □     黑胜 □")
        c.setFont(FONT, 11); c.setFillColor(GRAY)
        c.drawString(x + 12, y + h * 0.12, "裁判/选手签名:________________")
        c.setFont(FONT, 8)
        c.drawRightString(x + w - 8, y + 6, match_name)
    return _card_grid(out_path, cards, draw, cols, rows, None)


def generate_certificates_pdf(winners, event_name, group_name, out_path,
                              bg_image=None, judge="", date_str=""):
    """荣誉证书:每位获奖者一页(A4 竖版)。winners=[(名次, 姓名), ...]。
    bg_image:证书底图(竖版);没有则白底+简边框。文字叠印在底图留白中央。"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor

    c = canvas.Canvas(out_path, pagesize=A4)
    pw, ph = A4
    have_bg = bool(bg_image) and os.path.exists(bg_image)
    DARK = HexColor("#5c2e16")     # 古铜色,呼应花纹
    INK = HexColor("#2c2c2a")
    cx = pw / 2

    for rank, name in winners:
        if have_bg:
            try:
                c.drawImage(bg_image, 0, 0, pw, ph, preserveAspectRatio=False, mask="auto")
            except Exception:
                c.rect(15 * mm, 15 * mm, pw - 30 * mm, ph - 30 * mm)
        else:
            c.setStrokeColor(DARK); c.setLineWidth(2)
            c.rect(15 * mm, 15 * mm, pw - 30 * mm, ph - 30 * mm)

        c.setFillColor(DARK); c.setFont(FONT, 40)
        c.drawCentredString(cx, ph * 0.72, "荣  誉  证  书")
        c.setFillColor(INK); c.setFont(FONT, 30)
        c.drawCentredString(cx, ph * 0.56, name)
        c.setFont(FONT, 15)
        c.drawCentredString(cx, ph * 0.47, "在 %s「%s」中" % (event_name, group_name))
        c.setFillColor(DARK); c.setFont(FONT, 22)
        c.drawCentredString(cx, ph * 0.40, "荣获第 %d 名" % rank)
        c.setFillColor(INK); c.setFont(FONT, 14)
        c.drawCentredString(cx, ph * 0.33, "特发此证,以资鼓励")

        c.setFont(FONT, 13)
        if judge:
            c.drawRightString(pw * 0.80, ph * 0.24, "裁判长：%s" % judge)
        if date_str:
            c.drawRightString(pw * 0.80, ph * 0.205, date_str)
        c.showPage()
    c.save()
    return out_path


def open_in_viewer(path):
    """用系统默认 PDF 阅读器打开(跨平台)。"""
    if sys.platform.startswith("win"):
        os.startfile(path)                       # Windows
    elif sys.platform == "darwin":
        subprocess.run(["open", path])           # macOS
    else:
        subprocess.run(["xdg-open", path])       # Linux


def print_round(mathdir, print_txt_path, turn_no, out_path=None, auto_open=True, show_team=True):
    """供主程序调用的便捷入口:从赛事目录读 math_ini 取赛事名/裁判长，
    解析 print_txt 生成 PDF，并(可选)打开预览。"""
    ini = {}
    with open(os.path.join(mathdir, "math_ini.txt"), encoding="utf-8") as f:
        for s in f:
            a = s.strip().split(maxsplit=1)
            if len(a) == 2:
                ini[a[0]] = a[1]
    rows = parse_print_txt(print_txt_path)
    if out_path is None:
        out_path = os.path.join(mathdir, "turn%s对阵表.pdf" % turn_no)
    generate_pairing_pdf(rows, ini.get("name", ""), turn_no, out_path,
                         judge=ini.get("judje", ""), show_team=show_team)
    if auto_open:
        open_in_viewer(out_path)
    return out_path


if __name__ == "__main__":
    # 样张:用真实第 35 轮数据
    mathdir = os.path.join("mathdate", "2013nzjkzgxqs")
    ptxt = os.path.join(mathdir, "turn35print.txt")
    out = os.path.join(mathdir, "sample_对阵表.pdf")
    print_round(mathdir, ptxt, 35, out_path=out, auto_open=False)
    print("已生成样张:", os.path.abspath(out))
