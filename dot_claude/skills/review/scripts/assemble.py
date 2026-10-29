#!/usr/bin/env python3
"""/review の部分ファイルを、原稿ごとの報告書と索引（README.md）に組み立てる。

使い方: python3 assemble.py [--check] <出力先>

<出力先>/_meta.json と <出力先>/_parts/ を読み、<出力先>/<原稿名>.md と <出力先>/README.md を書く。
部分ファイルの型が約束から外れていれば、外れたファイルと理由を標準エラーに書き、何も書き出さずに終了コード1で終わる。
--check を付けると、そろっている部分ファイルの型だけを検査し、何も書き出さない（全原稿がそろう前の試行で使う）。
"""
import json
import re
import sys
from pathlib import Path

# 種類ごとの約束。接頭辞・節の名前・### の名前は、各スキル（~/.claude/skills/<種類>/SKILL.md）の報告フォーマットと同じにしておく。
# 部分ファイルを書くサブエージェントが型を崩したときに、ここで検出するため。
KINDS = {
    "advise": {
        "prefix": "A",
        "section": "推敲",
        "headings": ["文書の概要", "良い点", "改善提案", "追加提案", "サマリー"],
        "finding_headings": ["改善提案"],
    },
    "proofread": {
        "prefix": "P",
        "section": "校正",
        "headings": [
            "誤字・脱字", "表記揺れ", "句読点・記号・全角半角の不統一", "不自然な日本語",
            "読みにくい文", "段落の形式", "文体・文末の不統一", "文章規範（整形・表記）", "サマリー",
        ],
        "finding_headings": [
            "誤字・脱字", "表記揺れ", "句読点・記号・全角半角の不統一", "不自然な日本語",
            "読みにくい文", "段落の形式", "文体・文末の不統一", "文章規範（整形・表記）",
        ],
    },
    "verify": {
        "prefix": "F",
        "section": "ファクトチェック",
        "headings": ["正確な点", "誤りまたは要修正", "未確認", "引用・出典の問題", "補足", "サマリー"],
        "finding_headings": ["誤りまたは要修正", "未確認", "引用・出典の問題"],
    },
    "xcheck": {
        "prefix": "X",
        "section": "整合性",
        "headings": ["矛盾・不整合", "問題なし", "補足", "サマリー"],
        "finding_headings": ["矛盾・不整合"],
    },
}
KIND_ORDER = ["advise", "proofread", "verify", "xcheck"]
IMPORTANCE = ["高", "中", "低"]
XCHECK_PART = "_all.xcheck.md"

ITEM_RE = re.compile(r"^- #([A-Z])(\d+)((?: \[[^\]]+\])*)(.*)$")
TAG_RE = re.compile(r" \[([^\]]+)\]")
# 行の書き方（5-6・5〜6・3, 8 など）はサブエージェントごとに揺れるので、コロンの後ろは問わずファイルの部分だけを取る。
LOCATION_RE = re.compile(r"`([^`:]+)(?::[^`]*)?`")
PLACE_FIELD_RE = re.compile(r"^\s*- 箇所[A-Z]?:")
OTHER_LIST_RE = re.compile(r"^(?:[*+]|\d+[.)]) ")


class FormatError(Exception):
    """部分ファイルが約束の型から外れていることを表す。"""


def split_sections(text):
    """部分ファイルの本文を、### の見出しごとの (見出し, 行のリスト) に分ける。最初の ### より前の行は捨てる。"""
    sections = []
    for line in text.splitlines():
        if line.startswith("### "):
            sections.append((line[4:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    return sections


def parse_items(lines):
    """節の行から指摘を取り出す。各指摘は番号・印のリスト・見出しの残り・入れ子の行を持つ辞書。"""
    items = []
    for line in lines:
        m = ITEM_RE.match(line)
        if m:
            items.append({
                "prefix": m.group(1),
                "number": int(m.group(2)),
                "tags": TAG_RE.findall(m.group(3)),
                "rest": m.group(4).strip(),
                "children": [],
                "head": line,
            })
        elif items and line.startswith("  "):
            items[-1]["children"].append(line)
    return items


def check_part(name, kind, text):
    """部分ファイルの型を確かめ、外れていれば理由のリストを返す。"""
    spec = KINDS[kind]
    errors = []
    for line in text.splitlines():
        if line.startswith("# ") or line.startswith("## "):
            errors.append(f"{name}: ### より上の見出しがある: {line}")
    allowed_tags = set(IMPORTANCE) if kind == "advise" else set()
    sections = split_sections(text)
    # 見出しをすべて求めると、省略してよい節（verify の「引用・出典の問題」）がある正しい部分ファイルまで拒む。
    # どの種類も最後の節はサマリーなので、それだけを求めて、空・見出しの形違い・途中切れを捕まえる。
    if "サマリー" not in [h for h, _ in sections]:
        errors.append(f"{name}: ### サマリー がない（途中で切れたか、見出しの形が違う）")
    numbers = [it["number"] for _, ls in sections for it in parse_items(ls)]
    for n in sorted({n for n in numbers if numbers.count(n) > 1}):
        errors.append(f"{name}: 番号 #{spec['prefix']}{n} が重なっている")
    for heading, lines in sections:
        if heading not in spec["headings"]:
            errors.append(f"{name}: 知らない ### の名前: {heading}")
            continue
        if heading not in spec["finding_headings"]:
            continue
        for line in lines:
            if (line.startswith("- ") and not ITEM_RE.match(line)) or OTHER_LIST_RE.match(line):
                errors.append(f"{name}: 番号の形でない指摘: {line}")
        for item in parse_items(lines):
            label = f"{name}: #{item['prefix']}{item['number']}"
            if item["prefix"] != spec["prefix"]:
                errors.append(f"{label}: 接頭辞は {spec['prefix']} のはず")
            unknown = [t for t in item["tags"] if t not in allowed_tags]
            if unknown:
                errors.append(f"{label}: 知らない印 {unknown}")
            if kind == "advise" and (not item["tags"] or item["tags"][0] not in IMPORTANCE):
                errors.append(f"{label}: 重要度の印が番号の直後にない")
    return errors


def xcheck_places(item):
    """整合性の指摘の箇所欄（箇所A・箇所B・箇所C…）に書かれたファイルを返す。説明や推奨に出てくるファイルは含めない。"""
    return [m.group(1) for c in item["children"] if PLACE_FIELD_RE.match(c) for m in LOCATION_RE.finditer(c)]


def same_file(place, target_path):
    """箇所に書かれたファイルが原稿のパスを指すか。

    ファイル名だけ・パスの末尾・絶対パスのどれで書かれても照合できるよう、短いほうの長さぶんを末尾から比べる。
    """
    a, b = Path(place).parts, Path(target_path).parts
    n = min(len(a), len(b))
    return a[-n:] == b[-n:]


def check_xcheck_places(sections, targets):
    """整合性の各指摘が箇所欄で対象の原稿を1つ以上指し、どの箇所も原稿が1つに決まるかを確かめ、外れの理由のリストを返す。"""
    errors = []
    for heading, lines in sections:
        if heading != "矛盾・不整合":
            continue
        for item in parse_items(lines):
            label = f"{XCHECK_PART}: #X{item['number']}"
            hits = 0
            for place in xcheck_places(item):
                matched = [t["name"] for t in targets if same_file(place, t["path"])]
                if len(matched) > 1:
                    errors.append(f"{label}: 箇所 {place} がどの原稿か決まらない（{', '.join(matched)}）")
                hits += len(matched)
            if not hits:
                errors.append(f"{label}: 箇所欄に対象の原稿がない")
    return errors


def xcheck_items_for(target_path, sections):
    """整合性の部分ファイルから、指定した原稿が箇所欄に出てくる指摘だけを返す。"""
    picked = []
    for heading, lines in sections:
        if heading != "矛盾・不整合":
            continue
        for item in parse_items(lines):
            if any(same_file(p, target_path) for p in xcheck_places(item)):
                picked.append(item)
    return picked


def count_line(kind_items):
    """件数行を作る。kind_items は種類ごとの (節の名前, 指摘) のリスト。"""
    parts = []
    if "advise" in kind_items:
        counts = {lv: 0 for lv in IMPORTANCE}
        for _, item in kind_items["advise"]:
            if item["tags"] and item["tags"][0] in counts:
                counts[item["tags"][0]] += 1
        parts.append("推敲 " + " ".join(f"[{lv}]{counts[lv]}" for lv in IMPORTANCE))
    if "proofread" in kind_items:
        parts.append(f"校正 {len(kind_items['proofread'])}件")
    if "verify" in kind_items:
        by = {"誤りまたは要修正": 0, "未確認": 0, "引用・出典の問題": 0}
        for heading, _ in kind_items["verify"]:
            by[heading] += 1
        parts.append(f"ファクトチェック 誤り{by['誤りまたは要修正']} 未確認{by['未確認']} 引用・出典{by['引用・出典の問題']}")
    if "xcheck" in kind_items:
        parts.append(f"整合性 {len(kind_items['xcheck'])}件")
    return "- 件数: " + " / ".join(parts)


def build_report(target, kinds, parts, xcheck_sections):
    """1つの原稿の報告書の本文と、索引に載せる件数行を返す。"""
    name = target["name"]
    body = []
    kind_items = {}
    for kind in kinds:
        spec = KINDS[kind]
        if kind == "xcheck":
            items = xcheck_items_for(target["path"], xcheck_sections)
            kind_items[kind] = [("矛盾・不整合", it) for it in items]
            body += ["", f"## {spec['section']}", "", "### 矛盾・不整合", ""]
            body += [line for it in items for line in [it["head"], *it["children"]]] or ["なし"]
            continue
        text = parts[kind]
        sections = split_sections(text)
        kind_items[kind] = [(h, it) for h, ls in sections if h in spec["finding_headings"] for it in parse_items(ls)]
        body += ["", f"## {spec['section']}", "", text.strip()]

    counts = count_line(kind_items)
    head = [f"# {name} のレビュー", "", f"- 原稿: `{target['path']}`", counts]
    return "\n".join(head + body) + "\n", counts


def build_readme(meta, counts_by_name):
    """索引 README.md の本文を返す。counts_by_name は原稿の名前から件数行への辞書。"""
    kinds = [k for k in KIND_ORDER if k in meta["kinds"]]
    lines = [f"# レビューの索引（{meta['date']}）", ""]
    lines += [f"- 対象: {len(meta['targets'])}本", f"- かけた種類: {'、'.join(KINDS[k]['section'] for k in kinds)}"]
    for key, value in (meta.get("conditions") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("- 件数は種類ごとに数えている。同じ問題を複数の種類が指すと重ねて数え、整合性の指摘は関係するすべての原稿に載る")
    lines += ["", "## 原稿ごとの件数", "", "| 原稿 | 件数 |", "|---|---|"]
    for target in meta["targets"]:
        counts = counts_by_name[target["name"]].removeprefix("- 件数: ")
        lines.append(f"| [{target['name']}]({target['name']}.md) | {counts} |")
    return "\n".join(lines) + "\n"


def check_targets(targets):
    """原稿の名前が、出力先のほかのファイルや互いと重ならないかを確かめ、外れの理由のリストを返す。

    名前はそのまま出力先のファイル名（<名前>.md）になるので、README.md・_meta.json・_brief.md・_parts/ と重なる名前や、
    出力先の外を指すパス区切りを含む名前は使えない。大文字小文字だけが違う名前は、大文字小文字を区別しない
    ファイルシステムで同じファイルになるので重なりとして扱う。
    """
    errors, seen = [], set()
    for target in targets:
        name = target["name"]
        key = name.casefold()
        if Path(name).name != name or name.startswith("_") or key == "readme":
            errors.append(f"_meta.json: 原稿の名前 {name} は使えない（README・_ で始まる名前・パス区切りは出力先のファイルと重なる）")
        elif key in seen:
            errors.append(f"_meta.json: 原稿の名前 {name} が重なっている")
        seen.add(key)
    return errors


def assemble(outdir, check_only=False):
    """出力先の部分ファイルを検査して組み立てる。型の外れがあれば FormatError を送出し、何も書かない。

    check_only なら、そろっている部分ファイルの型だけを検査し、ない部分ファイルは問わず、何も書かない。
    戻り値は、書き出したファイル名（check_only なら検査した部分ファイル名）の並べ替えたリスト。
    """
    outdir = Path(outdir)
    meta = json.loads((outdir / "_meta.json").read_text(encoding="utf-8"))
    errors = [f"_meta.json: 知らない種類 {k}" for k in meta["kinds"] if k not in KINDS]
    errors += check_targets(meta["targets"])
    kinds = [k for k in KIND_ORDER if k in meta["kinds"]]
    partdir = outdir / "_parts"
    parts = {}
    checked = []
    for target in meta["targets"]:
        for kind in kinds:
            if kind == "xcheck":
                continue
            path = partdir / f"{target['name']}.{kind}.md"
            if not path.exists():
                if not check_only:
                    errors.append(f"{path.name}: 部分ファイルがない")
                continue
            text = path.read_text(encoding="utf-8")
            errors += check_part(path.name, kind, text)
            checked.append(path.name)
            parts[(target["name"], kind)] = text
    xcheck_sections = []
    if "xcheck" in kinds:
        path = partdir / XCHECK_PART
        if not path.exists():
            if not check_only:
                errors.append(f"{XCHECK_PART}: 部分ファイルがない")
        else:
            text = path.read_text(encoding="utf-8")
            errors += check_part(XCHECK_PART, "xcheck", text)
            xcheck_sections = split_sections(text)
            errors += check_xcheck_places(xcheck_sections, meta["targets"])
            checked.append(XCHECK_PART)
    if errors:
        raise FormatError("\n".join(errors))
    if check_only:
        return sorted(checked)

    counts_by_name = {}
    outputs = {}
    for target in meta["targets"]:
        own = {k: parts[(target["name"], k)] for k in kinds if k != "xcheck"}
        report, counts = build_report(target, kinds, own, xcheck_sections)
        outputs[f"{target['name']}.md"] = report
        counts_by_name[target["name"]] = counts
    outputs["README.md"] = build_readme(meta, counts_by_name)
    for filename, text in outputs.items():
        (outdir / filename).write_text(text, encoding="utf-8")
    return sorted(outputs)


def main(argv):
    """コマンドラインの入口。"""
    args = argv[1:]
    check_only = "--check" in args
    args = [a for a in args if a != "--check"]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        names = assemble(args[0], check_only=check_only)
    except FormatError as e:
        print(f"部分ファイルの型が約束から外れています:\n{e}", file=sys.stderr)
        return 1
    print(("型を確かめた: " if check_only else "書き出した: ") + ", ".join(names))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
