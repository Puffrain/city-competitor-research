#!/usr/bin/env python3
"""Build an editable Word competitor report from a city JSON dump."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x1D, 0x4E, 0xD8)
BLACK = RGBColor(0x11, 0x11, 0x11)
GRAY = RGBColor(0x55, 0x55, 0x55)
YELLOW = "FFF8E7"
LABEL = "EEF3F8"
HEADER = "1D4ED8"


def set_run_font(run, size=11, bold=False, color=BLACK, name="Microsoft YaHei"):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = name
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:eastAsia"), name)


def shade(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_border(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D9D9D9")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def write_cell(cell, text, header=False, size=10, fill=None, bold=False, yellow=False, links=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text or "")
    set_run_font(run, size=size, bold=bold or header, color=RGBColor(0xFF, 0xFF, 0xFF) if header else BLACK)
    if header:
        shade(cell, HEADER)
    elif yellow:
        shade(cell, YELLOW)
    elif fill:
        shade(cell, fill)
    set_cell_border(cell)
    if links:
        for label, url in links:
            p2 = cell.add_paragraph()
            add_hyperlink(p2, label, url)


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1D4ED8")
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(color)
    rPr.append(u)
    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def add_title(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Title"]
    p.clear()
    run = p.add_run(text)
    set_run_font(run, size=22, bold=True)


def add_heading(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 1"]
    p.clear()
    run = p.add_run(text)
    set_run_font(run, size=16, bold=True)


def add_body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    set_run_font(run, size=11)


def make_table(doc, headers, rows, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        write_cell(table.rows[0].cells[i], h, header=True, size=9, bold=True)
    for row in rows:
        r = table.add_row()
        for i, val in enumerate(row):
            yellow = isinstance(val, str) and ("未查到" in val)
            write_cell(r.cells[i], str(val), size=9, yellow=yellow)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Cm(widths[idx])
    return table


def pcode(priority: str) -> str:
    return str(priority).split()[0] if priority else "P2"


def baidu_url(city: str, name: str) -> str:
    from urllib.parse import quote
    return "https://www.baidu.com/s?wd=" + quote(f"{city} {name}")


def dianping_url(name: str) -> str:
    from urllib.parse import quote
    return "https://www.dianping.com/search/keyword/2/0_" + quote(name)


def build(data: dict, out: Path) -> None:
    city = data.get("city_name") or data.get("city") or "目标城市"
    industry = data.get("industry") or "目标行业"
    items = data.get("items") or []
    as_of = date.today().isoformat()
    p1 = [x for x in items if str(x.get("priority", "")).startswith("P1")]
    p2 = [x for x in items if str(x.get("priority", "")).startswith("P2")]
    p3 = [x for x in items if str(x.get("priority", "")).startswith("P3")]

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(1.8)
        section.right_margin = Cm(1.8)

    add_title(doc, f"{city}{industry}在营业竞品详细搜集")
    add_body(
        doc,
        f"搜集日期 {as_of}。只收高德上仍能搜到的在营机构。没查到的价格、班额、点评条数写未查到，黄底格子可改。不要把高德评分当教学质量。",
    )
    add_body(
        doc,
        f"关键词：{'、'.join(data.get('keywords') or [])}。原始命中 {data.get('total_raw', 0)} 条，清洗后保留 {len(items)} 家。P1 {len(p1)} 家写单店卡，P2 {len(p2)} 家写核心简表，P3 {len(p3)} 家只看家长入口。",
    )

    add_heading(doc, "1. 口径")
    make_table(
        doc,
        ["项目", "做法"],
        [
            ["营业状态", "只考虑在营业；高德仍有点即收入"],
            ["优先级", "P1 品牌或课程最接近，P2 其余核心，P3 学科/学习机等相邻入口"],
            ["没查到", "写未查到，不编价格、许可和口碑"],
            ["链接", "每家保留高德地点页、点评检索、百度检索"],
        ],
        [4.0, 13.8],
    )

    add_heading(doc, "2. 名单总表")
    rows = []
    for it in items:
        rows.append(
            [
                it.get("no"),
                pcode(it.get("priority")),
                it.get("name"),
                it.get("adname") or it.get("business_area") or "",
                it.get("address") or "",
                it.get("tel") or "未查到",
                it.get("rating") or "未查到",
            ]
        )
    make_table(doc, ["编号", "级", "门店", "区域", "地址", "电话", "高德评分"], rows, [1.4, 1.4, 4.4, 2.4, 5.0, 2.4, 1.8])

    add_heading(doc, "3. P1 单店卡")
    add_body(doc, "P1 按公开信息尽量写全。官网、价格、班额查不到就留黄底，不空判真 AI 课。")
    for it in p1:
        p = doc.add_paragraph()
        run = p.add_run(f"{it.get('no')}. {it.get('name')}")
        set_run_font(run, size=13, bold=True)
        card_rows = [
            ("品牌 / 类型", f"{it.get('brand') or ''}    {it.get('relevance') or ''}"),
            ("地址 / 区域", f"{it.get('address') or '未查到'}    {it.get('adname') or ''}"),
            ("电话 / 营业时间", f"{it.get('tel') or '未查到'}    {it.get('opentime') or '未查到'}"),
            ("还在营业", it.get("status") or "在营"),
            ("课程关键词", "、".join(it.get("keywords") or []) or "未查到"),
            ("高德类型", it.get("type") or "未查到"),
            ("正课价格", "未查到"),
            ("班型 / 班额", "未查到"),
            ("点评星级和条数", "未查到，不当口碑结论"),
            ("可借鉴点", "待补"),
            ("差异化机会", "待补"),
        ]
        table = doc.add_table(rows=1, cols=2)
        write_cell(table.rows[0].cells[0], "项目", header=True, size=9)
        write_cell(table.rows[0].cells[1], "填写", header=True, size=9)
        for label, value in card_rows:
            r = table.add_row()
            write_cell(r.cells[0], label, size=9, fill=LABEL, bold=True)
            write_cell(r.cells[1], value, size=9, yellow=("未查到" in value or value == "待补"))
        r = table.add_row()
        write_cell(r.cells[0], "相关链接", size=9, fill=LABEL, bold=True)
        write_cell(
            r.cells[1],
            "可点开链接",
            size=9,
            links=[
                ("高德", it.get("amap") or ""),
                ("点评", dianping_url(it.get("name") or "")),
                ("百度", baidu_url(city, it.get("name") or "")),
            ],
        )

    add_heading(doc, "4. P2 核心简表")
    rows = []
    for it in p2:
        rows.append(
            [
                it.get("no"),
                it.get("name"),
                it.get("address") or "",
                it.get("tel") or "未查到",
                "、".join(it.get("keywords") or []),
                "未查到",
            ]
        )
    make_table(doc, ["编号", "门店", "地址", "电话", "关键词", "价格"], rows, [1.4, 4.6, 5.4, 2.4, 2.8, 1.8])

    add_heading(doc, "5. P3 相邻入口")
    add_body(doc, "这些不一定是同业课程对手，但可能抢走家长入口。只记位置和是否还在招生。")
    rows = []
    for it in p3:
        rows.append([it.get("no"), it.get("name"), it.get("address") or "", it.get("tel") or "未查到"])
    make_table(doc, ["编号", "门店", "地址", "电话"], rows, [1.6, 5.6, 8.0, 2.6])

    add_heading(doc, "6. 待补")
    add_body(doc, "价格、班额、点评条数、公司全称、直营或加盟，需要官网、电话或到店后再填。地图文件可同时打开，用来看镇区和周边小学。")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    print(f"SAVED {out} items={len(items)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = json.loads(Path(args.in_json).read_text(encoding="utf-8"))
    build(data, Path(args.out))


if __name__ == "__main__":
    main()
