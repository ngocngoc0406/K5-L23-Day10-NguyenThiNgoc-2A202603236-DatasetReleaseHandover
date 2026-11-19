"""Ghép các file review_<tên>.csv của từng người thành một review_log.csv (TV2 — gộp review).

  python tools/merge_reviews.py <review_quang.csv> <review_mai.csv> ... --out <review_log.csv>

Bỏ dòng chưa điền verdict; báo dòng có verdict lạ hoặc ghi chú < 20 ký tự để sửa trước khi nộp.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Ghép review_*.csv")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows, problems = [], []
    for f in args.files:
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                v = (row.get("verdict") or "").strip().lower()
                if not v:
                    problems.append(f"{f}: {row.get('image')} chưa điền verdict")
                    continue
                note = (row.get("note") or "").strip()
                if v not in ("confirmed", "rejected"):
                    problems.append(f"{f}: {row.get('image')} verdict '{v}' phải là confirmed/rejected")
                if len(note) < 20:
                    problems.append(f"{f}: {row.get('image')} ghi chú < 20 ký tự: nói rõ thấy gì trong ảnh")
                if v == "confirmed" and row.get("type", "").strip() == "swap":
                    problems.append(f"{f}: {row.get('image')} type 'swap' phải đổi thành class_swap hoặc category_swap")
                rows.append([row["image"].strip(), row["type"].strip(), v, note])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "type", "verdict", "note"])
        w.writerows(rows)
    print(f"{len(rows)} dòng -> {args.out}")
    for p in problems:
        print("  CẦN SỬA:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
