"""Validator của nhóm 68.

  python validator/validate.py <delivery> --out <errors.json> [--candidates <candidates.json>] [--rules <rules.json>]

--out        : lỗi luật (chưa có lỗi gán nhãn; lỗi gán nhãn chỉ vào sau khi xem ảnh, qua merge_review.py)
--rules      : ghi thêm một bản lỗi luật riêng (dùng cho merge_review.py --rules)
--candidates : ứng viên lỗi gán nhãn để xem ảnh

Chỉ đọc thư mục delivery được truyền vào; chỉ thư viện chuẩn; không mạng.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crosscheck  # noqa: E402
import rules_file  # noqa: E402
import rules_meta  # noqa: E402
from common import Delivery  # noqa: E402


def write(path: str, items: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"errors": items}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def dedupe(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for e in items:
        key = (e["type"], e["target"])
        if key not in seen:
            seen.add(key)
            out.append(e)
    return sorted(out, key=lambda e: (e["type"], e["target"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validator nhóm 68")
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidates")
    ap.add_argument("--rules")
    args = ap.parse_args()

    d = Delivery(args.delivery)
    rules = dedupe(rules_file.check(d) + rules_meta.check(d))
    write(args.out, rules)
    if args.rules:
        write(args.rules, rules)
    msg = f"{len(rules)} lỗi luật -> {args.out}"
    if args.candidates:
        cands = crosscheck.candidates(d)
        write(args.candidates, cands)
        msg += f"; {len(cands)} ứng viên -> {args.candidates}"
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
