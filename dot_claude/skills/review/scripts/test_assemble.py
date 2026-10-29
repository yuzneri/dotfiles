"""assemble.py の振る舞いのテスト。python3 -m unittest で実行する。"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import assemble

ADVISE = """### 文書の概要
- **文書の種類**: 技術記事

### 改善提案

- #A1 [高] 構成・論理展開
  - 箇所: `book/ch1.md:3`
  - 指摘: 結論の前提が本文にない
  - 提案: 前提を足す
- #A2 [中] LLMっぽい表現の排除
  - 箇所: `book/ch1.md:9`
  - 指摘: 比喩動詞
  - 提案: 普通の動詞にする

### サマリー
- **件数**: [高] 1件 / [中] 1件 / [低] 0件
"""

PROOFREAD = """### 誤字・脱字

- #P1 `book/ch1.md:2`
  - 該当箇所: 以外な結果
  - 修正案: 意外な結果

### 表記揺れ

- #P2 表記パターン: 「サーバ」と「サーバー」の揺れ
  - `book/ch1.md:4` 「サーバ」
  - `book/ch1.md:8` 「サーバー」
  - 推奨: 「サーバー」に統一する

### サマリー
- **件数**: 誤字・脱字 1件
"""

VERIFY = """### 正確な点

- #F1 `book/ch1.md:1`
  - 内容: WebP は2010年に発表された
  - 出典: https://example.com/webp

### 誤りまたは要修正

- #F2 `book/ch1.md:5`
  - 内容: 発表年が違う
  - 正: 2010年
  - 出典: https://example.com/webp

### 未確認

- #F3 `book/ch1.md:7`
  - 内容: 規格書からの引用は原典で確かめられない

### サマリー
- **件数**: 正確 1件 / 誤り 1件 / 未確認 1件
"""

XCHECK = """### 矛盾・不整合

- #X1 種別: 事実の矛盾
  - 箇所A: `book/ch1.md:5` 2011年に発表
  - 箇所B: `book/ch2.md:3` 2010年に発表
  - 説明: 発表年が食い違う
  - 推奨: 2010年にそろえる
- #X2 種別: 用語の不統一
  - 箇所A: `book/ch2.md:4` チャンク
  - 箇所B: `book/ch3.md:8` チャンク
  - 説明: 別の意味で使っている
  - 推奨: 定義をそろえる

### サマリー
- **件数**: 矛盾・不整合 2件
"""


class AssembleTest(unittest.TestCase):
    """部分ファイルから報告書と索引を組み立てる振る舞いを確かめる。"""

    def setUp(self):
        self.use_new_outdir()

    def use_new_outdir(self):
        """出力先を空の一時ディレクトリに替える。subTest の回ごとに、前の回の部分ファイルや出力を持ち越さないため。"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name)
        (self.out / "_parts").mkdir()

    def write_meta(self, kinds, targets=None):
        meta = {
            "date": "2026-10-29",
            "targets": targets or [{"name": "ch1", "path": "book/ch1.md"}],
            "kinds": kinds,
            "conditions": {"想定読者": "ソフトウェアエンジニア"},
        }
        (self.out / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    def write_part(self, name, text):
        (self.out / "_parts" / name).write_text(text, encoding="utf-8")

    def report(self, name="ch1"):
        return (self.out / f"{name}.md").read_text(encoding="utf-8")

    def readme(self):
        """索引 README.md の本文を返す。"""
        return (self.out / "README.md").read_text(encoding="utf-8")

    def write_all_kinds_for_three_manuscripts(self):
        """ch1〜ch3 の3本に4種類の部分ファイルを書く。XCHECK の指摘が指す原稿をすべて対象に含めるため。

        種類は報告書の並び（推敲が先）と違う順で渡し、並べ替えも確かめられるようにしておく。
        """
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2", "ch3")]
        self.write_meta(["proofread", "advise", "verify", "xcheck"], targets=targets)
        for n in ("ch1", "ch2", "ch3"):
            self.write_part(f"{n}.advise.md", ADVISE)
            self.write_part(f"{n}.proofread.md", PROOFREAD)
            self.write_part(f"{n}.verify.md", VERIFY)
        self.write_part("_all.xcheck.md", XCHECK)

    def test_report_orders_sections_by_kind(self):
        self.write_all_kinds_for_three_manuscripts()
        assemble.assemble(self.out)
        headings = [l for l in self.report().splitlines() if l.startswith("## ")]
        self.assertEqual(headings, ["## 推敲", "## 校正", "## ファクトチェック", "## 整合性"])

    def test_count_line_reflects_items_in_each_section(self):
        self.write_all_kinds_for_three_manuscripts()
        assemble.assemble(self.out)
        self.assertIn(
            "- 件数: 推敲 [高]1 [中]1 [低]0 / 校正 2件 / ファクトチェック 誤り1 未確認1 引用・出典0 / 整合性 1件",
            self.report(),
        )

    def test_xcheck_findings_go_only_to_the_manuscripts_they_name(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2", "ch3")]
        self.write_meta(["xcheck"], targets=targets)
        self.write_part("_all.xcheck.md", XCHECK)
        assemble.assemble(self.out)
        self.assertIn("#X1", self.report("ch1"))
        self.assertNotIn("#X2", self.report("ch1"))
        self.assertIn("#X1", self.report("ch2"))
        self.assertIn("#X2", self.report("ch2"))
        self.assertIn("#X2", self.report("ch3"))

    def test_xcheck_places_with_line_ranges_or_lists_reach_their_manuscripts(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2", "ch3")]
        self.write_meta(["xcheck"], targets=targets)
        self.write_part("_all.xcheck.md", XCHECK.replace("`book/ch1.md:5`", "`book/ch1.md:5〜6`").replace("`book/ch2.md:3`", "`book/ch2.md:3, 8`"))
        assemble.assemble(self.out)
        self.assertIn("#X1", self.report("ch1"))
        self.assertIn("#X1", self.report("ch2"))

    def test_xcheck_ignores_manuscripts_named_outside_the_place_fields(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2", "ch3")]
        self.write_meta(["xcheck"], targets=targets)
        self.write_part("_all.xcheck.md", XCHECK.replace("  - 説明: 発表年が食い違う", "  - 説明: 発表年が食い違う。`book/ch3.md:2` は年を書いていない"))
        assemble.assemble(self.out)
        self.assertNotIn("#X1", self.report("ch3"))
        self.assertIn("#X2", self.report("ch3"))

    def test_xcheck_tells_apart_manuscripts_with_the_same_file_name(self):
        targets = [{"name": f"{a}-main", "path": f"book/{a}/main.md"} for a in ("alice", "bob", "carol")]
        self.write_meta(["xcheck"], targets=targets)
        only_x1 = XCHECK.split("- #X2")[0] + "### サマリー\n"
        self.write_part("_all.xcheck.md", only_x1.replace("book/ch1.md", "alice/main.md").replace("book/ch2.md", "/abs/book/bob/main.md"))
        assemble.assemble(self.out)
        self.assertIn("#X1", self.report("alice-main"))
        self.assertIn("#X1", self.report("bob-main"))
        self.assertNotIn("#X1", self.report("carol-main"))

    def test_kinds_not_run_are_left_out(self):
        self.write_meta(["proofread"])
        self.write_part("ch1.proofread.md", PROOFREAD)
        assemble.assemble(self.out)
        text = self.report()
        self.assertNotIn("## 推敲", text)
        self.assertIn("- 件数: 校正 2件", text)

    def test_readme_indexes_every_manuscript_with_its_counts(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2")]
        self.write_meta(["proofread"], targets=targets)
        self.write_part("ch1.proofread.md", PROOFREAD)
        self.write_part("ch2.proofread.md", PROOFREAD.split("### 表記揺れ")[0] + "### サマリー\n")
        assemble.assemble(self.out)
        readme = self.readme()
        self.assertIn("| [ch1](ch1.md) | 校正 2件 |", readme)
        self.assertIn("| [ch2](ch2.md) | 校正 1件 |", readme)
        self.assertIn("- 想定読者: ソフトウェアエンジニア", readme)

    def test_readme_lists_kinds_in_report_order(self):
        self.write_meta(["proofread", "advise"])
        self.write_part("ch1.proofread.md", PROOFREAD)
        self.write_part("ch1.advise.md", ADVISE)
        assemble.assemble(self.out)
        self.assertIn("- かけた種類: 推敲、校正\n", self.readme())

    def assert_rejected(self, part_name, text, kinds, expected, targets=None):
        """部分ファイルを1つ書いて組み立て、expected を含む FormatError で止まり、何も書き出さないことを確かめる。"""
        self.write_meta(kinds, targets=targets)
        self.write_part(part_name, text)
        with self.assertRaises(assemble.FormatError) as ctx:
            assemble.assemble(self.out)
        self.assertIn(expected, str(ctx.exception))
        self.assertFalse((self.out / "README.md").exists())

    def test_rejects_wrong_prefix(self):
        self.assert_rejected("ch1.proofread.md", PROOFREAD.replace("#P1", "#A1"), ["proofread"], "接頭辞は P のはず")

    def test_rejects_tags_other_than_advise_importance(self):
        cases = [
            ("ch1.proofread.md", PROOFREAD.replace("#P1", "#P1 [必須]"), ["proofread"], "ch1.proofread.md: #P1: 知らない印 ['必須']"),
            ("ch1.advise.md", ADVISE.replace("#A1 [高]", "#A1 [高] [必須]"), ["advise"], "ch1.advise.md: #A1: 知らない印 ['必須']"),
        ]
        for part_name, text, kinds, expected in cases:
            with self.subTest(part=part_name):
                self.use_new_outdir()
                self.assert_rejected(part_name, text, kinds, expected)

    def test_rejects_unknown_heading(self):
        self.assert_rejected("ch1.proofread.md", PROOFREAD.replace("### 表記揺れ", "### 表記ゆれ"), ["proofread"], "知らない ### の名前")

    def test_rejects_unnumbered_finding(self):
        bad = PROOFREAD.replace("- #P1 `book/ch1.md:2`", "- `book/ch1.md:2`")
        self.assert_rejected("ch1.proofread.md", bad, ["proofread"], "番号の形でない指摘")

    def test_rejects_advise_finding_without_importance_first(self):
        self.assert_rejected("ch1.advise.md", ADVISE.replace("#A1 [高]", "#A1"), ["advise"], "重要度の印")

    def test_rejects_top_level_headings_in_parts(self):
        self.assert_rejected("ch1.proofread.md", "## 校正\n" + PROOFREAD, ["proofread"], "### より上の見出し")

    def test_rejects_part_that_is_empty_cut_short_or_not_in_the_list_format(self):
        cases = [
            ("空", "", "ch1.proofread.md: ### サマリー がない"),
            ("太字の見出し", re.sub(r"^### (.+)$", r"**\1**", PROOFREAD, flags=re.M), "ch1.proofread.md: ### サマリー がない"),
            ("途中で切れた", PROOFREAD.split("### サマリー")[0], "ch1.proofread.md: ### サマリー がない"),
            ("* の箇条書き", PROOFREAD.replace("- #P1", "* #P1"), "ch1.proofread.md: 番号の形でない指摘: * #P1"),
            ("番号付きリスト", PROOFREAD.replace("- #P1", "1. #P1"), "ch1.proofread.md: 番号の形でない指摘: 1. #P1"),
        ]
        for case, text, expected in cases:
            with self.subTest(case=case):
                self.use_new_outdir()
                self.assert_rejected("ch1.proofread.md", text, ["proofread"], expected)

    def test_rejects_duplicate_numbers(self):
        self.assert_rejected("ch1.proofread.md", PROOFREAD.replace("#P2", "#P1"), ["proofread"], "ch1.proofread.md: 番号 #P1 が重なっている")

    def test_rejects_unknown_kind(self):
        self.assert_rejected("ch1.proofread.md", PROOFREAD, ["proofread", "校正"], "_meta.json: 知らない種類 校正")

    def test_rejects_manuscript_names_that_collide_with_output_files(self):
        cases = [
            (["README", "ch2"], "原稿の名前 README は使えない"),
            (["_brief"], "原稿の名前 _brief は使えない"),
            (["../ch1"], "原稿の名前 ../ch1 は使えない"),
            (["ch1", "CH1"], "原稿の名前 CH1 が重なっている"),
        ]
        for names, expected in cases:
            with self.subTest(names=names):
                self.use_new_outdir()
                self.write_meta(["proofread"], targets=[{"name": n, "path": f"book/{n}.md"} for n in names])
                for n in names:
                    self.write_part(f"{n}.proofread.md", PROOFREAD)
                with self.assertRaises(assemble.FormatError) as ctx:
                    assemble.assemble(self.out)
                self.assertIn(expected, str(ctx.exception))
                self.assertFalse((self.out / "README.md").exists())

    def test_rejects_xcheck_finding_whose_places_name_no_manuscript(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2")]
        bad = XCHECK.replace("`book/ch2.md:4`", "ch2.md:4")
        self.assert_rejected("_all.xcheck.md", bad, ["xcheck"], "_all.xcheck.md: #X2: 箇所欄に対象の原稿がない", targets=targets)

    def test_rejects_xcheck_place_that_fits_several_manuscripts(self):
        targets = [{"name": f"{a}-main", "path": f"book/{a}/main.md"} for a in ("alice", "bob", "carol")]
        only_x1 = XCHECK.split("- #X2")[0] + "### サマリー\n"
        bad = only_x1.replace("book/ch1.md", "main.md").replace("book/ch2.md", "bob/main.md")
        self.assert_rejected(
            "_all.xcheck.md", bad, ["xcheck"],
            "_all.xcheck.md: #X1: 箇所 main.md がどの原稿か決まらない（alice-main, bob-main, carol-main）", targets=targets,
        )

    def test_reports_missing_part(self):
        self.write_meta(["proofread", "advise"])
        self.write_part("ch1.proofread.md", PROOFREAD)
        with self.assertRaises(assemble.FormatError) as ctx:
            assemble.assemble(self.out)
        self.assertIn("ch1.advise.md: 部分ファイルがない", str(ctx.exception))

    def test_check_mode_validates_present_parts_without_writing(self):
        targets = [{"name": n, "path": f"book/{n}.md"} for n in ("ch1", "ch2")]
        self.write_meta(["proofread", "advise"], targets=targets)
        self.write_part("ch1.proofread.md", PROOFREAD)
        checked = assemble.assemble(self.out, check_only=True)
        self.assertEqual(checked, ["ch1.proofread.md"])
        self.assertFalse((self.out / "ch1.md").exists())

    def test_check_mode_lists_only_the_parts_it_checked(self):
        self.write_meta(["proofread"])
        self.write_part("ch1.proofread.md", PROOFREAD)
        self.write_part("ch1.proofreading.md", PROOFREAD)
        self.assertEqual(assemble.assemble(self.out, check_only=True), ["ch1.proofread.md"])

    def test_check_mode_still_rejects_broken_parts(self):
        self.write_meta(["proofread"])
        self.write_part("ch1.proofread.md", PROOFREAD.replace("#P1", "#A1"))
        with self.assertRaises(assemble.FormatError):
            assemble.assemble(self.out, check_only=True)

    def test_readme_explains_how_findings_are_counted(self):
        self.write_meta(["proofread"])
        self.write_part("ch1.proofread.md", PROOFREAD)
        assemble.assemble(self.out)
        self.assertIn("同じ問題を複数の種類が指すと重ねて数え", self.readme())

    def run_cli(self, *args):
        """assemble.py をコマンドとして動かす。-B は、テストの実行で __pycache__ を残さないため。"""
        return subprocess.run([sys.executable, "-B", assemble.__file__, *args], capture_output=True, text=True)

    def test_cli_exits_1_and_names_the_part_on_format_error(self):
        self.write_meta(["proofread"])
        self.write_part("ch1.proofread.md", PROOFREAD.replace("#P1", "#A1"))
        result = self.run_cli(str(self.out))
        self.assertEqual(result.returncode, 1)
        self.assertIn("ch1.proofread.md: #A1: 接頭辞は P のはず", result.stderr)
        self.assertFalse((self.out / "README.md").exists())

    def test_cli_exits_2_with_usage_without_an_output_dir(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("使い方:", result.stderr)


if __name__ == "__main__":
    unittest.main()
