"""Chốt bài từ các file review của nhóm, chạy lại được nhiều lần (không đụng git).

  python tools/finalize.py

Đề ẩn  : reviews/review_*.csv          -> submission/de_an/review_log.csv -> submission/de_an/errors.json
68007  : reviews/r68007/review_*.csv   -> runs/r68007/review_log.csv -> errors.json -> build_v2 -> pack
         -> check_handover -> export_submission (submission/r68007, submission/lineage.jsonl)

Chỉ dòng đã có verdict (confirmed/rejected) mới được tính. Còn ứng viên chưa review thì
v2 giữ Hold (--pending-review) và script in danh sách còn thiếu.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SEED = "r68007"


def run(*cmd: str) -> str:
    out = subprocess.run([PY, *cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                         env={**__import__("os").environ, "PYTHONUTF8": "1"})
    if out.returncode not in (0, 1):
        raise SystemExit(f"lỗi khi chạy {cmd}:\n{out.stdout}\n{out.stderr}")
    return out.stdout + out.stderr


def candidates(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["errors"] if isinstance(data, dict) else data


def collect(files: list[Path], cands: list[dict], out: Path) -> tuple[list[str], list[str]]:
    """Ghép review; trả về (ảnh chưa review, vấn đề cần sửa)."""
    rows, problems, done = [], [], set()
    for f in files:
        with f.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                v = (r.get("verdict") or "").strip().lower()
                if not v:
                    continue
                img, typ, note = r["image"].strip(), r["type"].strip(), (r.get("note") or "").strip()
                if v not in ("confirmed", "rejected"):
                    problems.append(f"{f.name}: {img} verdict '{v}' phải là confirmed/rejected")
                if len(note) < 20:
                    problems.append(f"{f.name}: {img} ghi chú < 20 ký tự")
                if v == "confirmed" and typ == "swap":
                    problems.append(f"{f.name}: {img} còn 'swap': đổi thành class_swap hoặc category_swap")
                rows.append([img, typ, v, note])
                done.add(img)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["image", "type", "verdict", "note"])
        w.writerows(rows)
    pending = sorted({c["target"] for c in cands} - done)
    return pending, problems


def main() -> int:
    # ---------- đề ẩn ----------
    de = ROOT / "submission" / "de_an"
    p_de, prob_de = collect(sorted((ROOT / "reviews").glob("review_*.csv")), candidates(de / "candidates.json"), de / "review_log.csv")
    print(run("scripts/merge_review.py", "--rules", "submission/de_an/rules.json",
              "--review", "submission/de_an/review_log.csv", "--out", "submission/de_an/errors.json").strip())

    # ---------- seed luyện tập ----------
    r = ROOT / "runs" / SEED
    p_r, prob_r = collect(sorted((ROOT / "reviews" / SEED).glob("review_*.csv")), candidates(r / "candidates.json"), r / "review_log.csv")
    print(run("scripts/merge_review.py", "--rules", f"runs/{SEED}/rules.json",
              "--review", f"runs/{SEED}/review_log.csv", "--out", f"runs/{SEED}/errors.json").strip())
    # lineage: lấy bản đã nộp (có thêm dòng của TV3) làm gốc
    lin = ROOT / "submission" / "lineage.jsonl"
    if lin.is_file():
        (ROOT / "runs" / "lineage.jsonl").write_text(lin.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8")
    print(run("tools/build_v2.py", f"runs/{SEED}", "--pending-review", str(len(p_r))).splitlines()[0])
    rid = json.loads((r / "delivery" / "release.json").read_text(encoding="utf-8"))["release_id"]
    print(run("scripts/pack_release.py", f"runs/{SEED}/handover/{rid}_v2").strip())
    check = run("scripts/check_handover.py", "--run", f"runs/{SEED}")
    print("\n".join(line for line in check.splitlines() if "FAIL" in line or "Tổng" in line))
    print(run("scripts/export_submission.py", "--run", f"runs/{SEED}").strip())
    if not p_r:
        (ROOT / "submission" / SEED / "review_pending.json").unlink(missing_ok=True)

    # ---------- tóm tắt ----------
    print("\n===== CÒN THIẾU =====")
    print(f"Đề ẩn chưa review ({len(p_de)}): {', '.join(p_de) or 'không'}")
    print(f"{SEED} chưa review ({len(p_r)}): {', '.join(p_r) or 'không'}")
    for p in prob_de + prob_r:
        print("  CẦN SỬA:", p)
    if not (p_de or p_r or prob_de or prob_r):
        print("Đủ review. Cập nhật số cuối trong REPORT.md rồi commit + push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
