"""Truy vết ticket của team AI (TV4 — Nguyễn Thị Ngọc).

  python tools/trace_query.py <delivery> --out <trace.json>

Tự đọc từ lô (không ghi cứng tên lớp/cảnh):
  - guideline/changelog.md : bản mới nhất (mục "## vX.Y" đầu tiên) và lớp bị đổi quy tắc (tên trong `...`)
  - incoming/ticket.md     : các scene_xxx team AI nêu

tier_a : ảnh trong các cảnh ticket nêu, job theo guideline CŨ (lấy ở jobs.csv, không lấy ở ảnh),
         có ít nhất một box detection thuộc lớp bị đổi quy tắc trong labels/
tier_b : các ảnh khác (ngoài các cảnh đó) cùng điều kiện
notify : annotator + reviewer của các job chứa ảnh tầng a và b
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validator"))
from common import Delivery  # noqa: E402


def parse_changelog(text: str, class_names: set[str]) -> tuple[str, set[str]]:
    """Trả về (phiên bản mới nhất, các lớp bị đổi quy tắc trong bản đó)."""
    sections = re.split(r"^##\s+", text, flags=re.M)[1:]

    def key(sec: str) -> tuple[int, ...]:
        return tuple(int(n) for n in re.findall(r"\d+", sec.split()[0]))

    newest = max(sections, key=key)  # bản có số phiên bản lớn nhất, không phụ thuộc thứ tự viết
    version = newest.split()[0].strip()
    changed = {w for w in re.findall(r"`([^`]+)`", newest) if w in class_names}
    return version, changed


def main() -> int:
    ap = argparse.ArgumentParser(description="Truy vết ticket")
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = Delivery(args.delivery)
    names = set(d.classes.values())
    new_version, changed = parse_changelog((d.root / "guideline/changelog.md").read_text(encoding="utf-8"), names)
    ticket = (d.root / "incoming/ticket.md").read_text(encoding="utf-8")
    scenes = set(re.findall(r"scene_\d+", ticket))
    changed_ids = {cid for cid, n in d.classes.items() if n in changed}

    tier_a, tier_b, jobs = [], [], set()
    for stem in d.stems:
        m = d.meta.get(stem)
        if not m:
            continue
        job = d.jobs.get(m["job_id"])
        if not job or job["guideline"] == new_version:  # chỉ job theo guideline cũ
            continue
        if not any(box[0] in changed_ids for box in d.labels(stem)):
            continue
        (tier_a if m["scene_id"] in scenes else tier_b).append(stem)
        jobs.add(m["job_id"])

    notify = sorted({d.jobs[j][k] for j in jobs for k in ("annotator", "reviewer")})
    out = {"tier_a": sorted(tier_a), "tier_b": sorted(tier_b), "notify": notify}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"lớp đổi quy tắc: {sorted(changed)}; bản mới: {new_version}; cảnh ticket: {sorted(scenes)}")
    print(f"tier_a {len(tier_a)} ảnh, tier_b {len(tier_b)} ảnh, notify {notify} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
