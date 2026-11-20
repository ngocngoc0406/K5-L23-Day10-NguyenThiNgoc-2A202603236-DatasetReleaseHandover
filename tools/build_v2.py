"""Dựng lô v2 từ errors.json, không sửa v1 (TV3 — Phạm Đức Mạnh).

  python tools/build_v2.py runs/r68007 [--broken 000000xxxx ...] [--notes notes_v2.txt]
  python tools/build_v2.py runs/r68007 --pending-review 8   # giữ v2 Hold khi chưa review hết

Tạo runs/r<seed>/handover/<release_id>_v2/ gồm:
  images/, labels/     ảnh + nhãn GIỮ NGUYÊN của v1, trừ ảnh phải gán lại
  rework_queue.csv     image,type,annotator,reviewer,action  (người theo jobs.csv)
  truyvet.csv          image,scene_id,split,job_id,annotator,reviewer,guideline (guideline theo job, mỗi cảnh một split)
  manifest.csv         file,sha256 cho mọi file trong images/ và labels/
  label_summary.csv    class,count theo tên lớp trong classes.txt, dòng cuối TOTAL
  README.txt           số liệu tự sinh từ file thật + Ghi chú (thêm phần của TV4 qua --notes)

Quy tắc (GUIDE Pha 4):
  - lỗi nhãn detection / thiếu file -> rework, rời v2
  - wrong_hash: đã MỞ ẢNH KIỂM; ảnh còn nguyên -> ở lại, manifest ghi hash thật; ảnh hỏng -> truyền vào --broken -> rework
  - guideline_mismatch -> truyvet ghi guideline theo job;  scene_leak -> cả cảnh về split đa số
  - lỗi chỉ ở panoptic -> ảnh ở lại v2, ghi vào Ghi chú để báo team panoptic
Sau khi chạy: python scripts/pack_release.py <thư mục v2>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validator"))
from common import Delivery  # noqa: E402

DET_REWORK = {"missing_image", "invalid_class", "bbox_out_of_bounds", "duplicate_box", "class_swap", "bbox_drift", "missing_box"}
PANOPTIC = {"invalid_category_id", "thing_overlap", "category_swap", "instance_merge"}
FIXED_IN_V2 = {"wrong_hash", "guideline_mismatch", "scene_leak"}
ACTION = {
    "missing_image": "thiếu file ảnh: lấy lại ảnh gốc rồi kiểm nhãn",
    "wrong_hash": "file ảnh hỏng: lấy lại ảnh gốc rồi kiểm nhãn",
}
THRESHOLD = 0.02


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def job_ranges(jobs: dict) -> str:
    """'v1.2 (J01-J03), v1.3 (J04-J10)'."""
    by = defaultdict(list)
    for j in sorted(jobs):
        by[jobs[j]["guideline"]].append(j)
    return ", ".join(f"{g} ({v[0]}-{v[-1]})" if len(v) > 1 else f"{g} ({v[0]})" for g, v in sorted(by.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description="Dựng lô v2")
    ap.add_argument("run", help="runs/r<seed>")
    ap.add_argument("--broken", nargs="*", default=[], help="ảnh wrong_hash đã mở kiểm và thấy HỎNG (vào rework)")
    ap.add_argument("--notes", help="file văn bản thêm vào Ghi chú của README (phần TV4)")
    ap.add_argument("--pending-review", type=int, default=0, help="số ứng viên còn chờ review; lớn hơn 0 thì kết luận v2 là Hold")
    args = ap.parse_args()
    if args.pending_review < 0:
        ap.error("--pending-review phải không âm")

    run = Path(args.run)
    d = Delivery(run / "delivery")
    rid = json.loads((d.root / "release.json").read_text(encoding="utf-8"))["release_id"]
    errors = json.loads((run / "errors.json").read_text(encoding="utf-8"))["errors"]
    by_img = {e["target"]: e["type"] for e in errors if e["target"] in d.manifest}
    leak_scenes = {e["target"] for e in errors if e["type"] == "scene_leak"}

    rework = {s: t for s, t in by_img.items() if t in DET_REWORK}
    for s in args.broken:
        if by_img.get(s) != "wrong_hash":
            raise SystemExit(f"--broken {s}: ảnh này không có lỗi wrong_hash trong errors.json")
        rework[s] = "wrong_hash"
    keep = [s for s in d.stems if s not in rework]

    v2 = run / "handover" / f"{rid}_v2"
    if v2.exists():
        shutil.rmtree(v2)  # chỉ xoá bản v2 cũ do script này tạo; KHÔNG đụng delivery/
    (v2 / "images").mkdir(parents=True)
    (v2 / "labels").mkdir()
    for s in keep:
        shutil.copyfile(d.path(s, "image"), v2 / "images" / d.path(s, "image").name)
        shutil.copyfile(d.path(s, "label"), v2 / "labels" / d.path(s, "label").name)

    # rework_queue: giao đúng người gán / người kiểm của job
    rows = []
    for s, t in sorted(rework.items()):
        job = d.jobs[d.meta[s]["job_id"]]
        rows.append([s, t, job["annotator"], job["reviewer"], ACTION.get(t, "gán lại nhãn detection")])
    write_csv(v2 / "rework_queue.csv", ["image", "type", "annotator", "reviewer", "action"], rows)

    # truyvet: guideline theo job; mỗi cảnh một split (split đa số của cảnh trong v1)
    scene_split = {}
    for scene in {m["scene_id"] for m in d.meta.values()}:
        votes = Counter(m["split"] for m in d.meta.values() if m["scene_id"] == scene)
        scene_split[scene] = max(sorted(votes), key=lambda k: votes[k])
    rows = []
    for s in keep:
        m = d.meta[s]
        job = d.jobs[m["job_id"]]
        rows.append([s, m["scene_id"], scene_split[m["scene_id"]], m["job_id"], job["annotator"], job["reviewer"], job["guideline"]])
    write_csv(v2 / "truyvet.csv", ["image", "scene_id", "split", "job_id", "annotator", "reviewer", "guideline"], rows)

    # manifest + label_summary
    files = sorted(p for sub in ("images", "labels") for p in (v2 / sub).iterdir())
    write_csv(v2 / "manifest.csv", ["file", "sha256"], [[p.relative_to(v2).as_posix(), sha(p)] for p in files])
    counts = Counter()
    for p in (v2 / "labels").iterdir():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                counts[d.classes[int(float(ln.split()[0]))]] += 1
    order = [d.classes[c] for c in sorted(d.classes)]
    rows = [[n, counts[n]] for n in order if counts[n]] + [["TOTAL", sum(counts.values())]]
    write_csv(v2 / "label_summary.csv", ["class", "count"], rows)

    # README
    n_err = len({e["target"] for e in errors})
    rate = n_err / len(d.manifest)
    v1 = (f"Hold — {rate:.1%} ảnh lỗi > ngưỡng 2%, không train tiếp trên v1" if rate > THRESHOLD
          else f"Release — {rate:.1%} ảnh lỗi ≤ ngưỡng 2%")
    types = Counter(by_img.values())
    hash_ok = sorted(s for s, t in by_img.items() if t == "wrong_hash" and s not in rework)
    pan = sorted(s for s, t in by_img.items() if t in PANOPTIC)
    people = sorted({f"{r[2]}/{r[3]}" for r in csv.reader((v2 / 'rework_queue.csv').open(encoding='utf-8')) if r[0] != 'image'})
    notes = [
        f"Đã tách {len(rework)} ảnh lỗi nhãn detection/thiếu file sang rework_queue.csv, giao lại người gán/người kiểm của job ({', '.join(people) or 'không có'}).",
        f"wrong_hash: đã mở ảnh kiểm, {len(hash_ok)} ảnh còn nguyên nên giữ và ghi sha256 thật trong manifest.csv ({', '.join(hash_ok) or 'không có'})"
        + (f"; {len(args.broken)} ảnh hỏng vào rework." if args.broken else "."),
        f"guideline_mismatch ({types['guideline_mismatch']} ảnh): truyvet.csv ghi guideline theo job trong jobs.csv.",
        f"scene_leak ({', '.join(sorted(leak_scenes)) or 'không có'}): đưa cả cảnh về một split (split đa số của cảnh).",
        f"Ảnh chỉ lỗi panoptic ở lại v2 vì nhãn detection vẫn đúng, báo team panoptic: {', '.join(pan) or 'không có'}.",
        "v1 giữ nguyên, nhãn trong v2 không sửa tay.",
    ]
    if args.notes:
        notes.append(Path(args.notes).read_text(encoding="utf-8").replace("\n", " ").strip())
    if args.pending_review:
        notes.append(f"Còn {args.pending_review} ứng viên chờ review; giữ v2 ở trạng thái Hold cho đến khi hoàn tất kiểm tra.")
    v2_decision = (
        f"Hold — còn {args.pending_review} ứng viên chờ review; đã tách {len(rework)} ảnh lỗi detection/thiếu file, chưa chốt để train"
        if args.pending_review else
        f"Release — đã tách {len(rework)} ảnh lỗi nhãn detection sang rework; sửa hash, guideline, split; "
        f"còn {len(pan)} ảnh lỗi panoptic (detection đúng) đã báo team panoptic"
    )
    readme = [
        f"Release: {rid}_v2",
        f"Parent: {rid}",
        f"Số ảnh: {len(keep)}",
        f"Số nhãn: {sum(counts.values())}",
        f"Guideline: {job_ranges(d.jobs)}",
        f"QC v1: {n_err}/{len(d.manifest)} = {rate:.1%}",
        f"Kết luận v1: {v1}",
        f"Kết luận v2: {v2_decision}",
        "Ghi chú: " + " ".join(notes),
    ]
    (v2 / "README.txt").write_text("\n".join(readme) + "\n", encoding="utf-8", newline="\n")
    print(f"{v2}: {len(keep)} ảnh, {sum(counts.values())} nhãn, rework {len(rework)}, QC v1 {n_err}/{len(d.manifest)} = {rate:.1%}")
    if hash_ok:
        print(f"NHẮC: mở kiểm các ảnh wrong_hash {hash_ok}; ảnh nào hỏng thì chạy lại với --broken <tên>")
    print(f"Tiếp: python scripts/pack_release.py {v2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
