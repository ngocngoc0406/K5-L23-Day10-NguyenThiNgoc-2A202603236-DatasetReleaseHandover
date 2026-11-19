"""Đối chiếu detection ↔ panoptic, sinh ứng viên lỗi gán nhãn (TV2 — Nguyễn Thị Ngọc Mai; missing_box: TV4).

Bản đầu (commit 05faaee) của Ngọc Mai ghép box ↔ segment bằng đếm pixel. Bản này giữ ý đó và sửa theo đo đạc:
  - instance_merge chỉ báo khi bbox segment ≈ hợp các box (bản đầu báo ~25 ca/lô, lô sạch 5 ca)
  - bbox_drift dùng "số mép box khớp mép segment" thay cho chỉ tỉ lệ pixel (bản đầu bắt ~16% drift giả)
  - ứng viên lệch lớp ghi "swap" (chưa biết bên nào sai), người xem ảnh chọn class_swap / category_swap
  - thêm missing_box (TV4)

Ứng viên: {"type", "target", "reason", "bbox"}; "bbox" là vùng [x1, y1, x2, y2] để tools/view.py cắt phóng to.
  swap           : box và segment trùng chỗ nhưng khác lớp -> mở ảnh: detection sai (class_swap) hay panoptic sai (category_swap)
  instance_merge : một segment trải trên ≥ 2 box cùng lớp, bbox segment ≈ hợp các box đó
  bbox_drift     : box chồng lên segment cùng lớp nhưng mép box không khớp mép segment (box bị dịch/đổi cỡ)
  missing_box    : segment thing đủ lớn mà không có box nào ở đó
Bỏ segment iscrowd (detection không có box cho crowd).
"""
from __future__ import annotations

from array import array
from itertools import groupby

from common import Delivery

# --- ngưỡng (đo trên lô sạch runs/clean + lỗi giả tự gài, xem REPORT §1) ---
MATCH_IOU = 0.7          # box và segment coi là "trùng chỗ"
MATCH_INSIDE = 0.9       # ... và ≥ 90% pixel segment nằm trong box
MERGE_SHARE = 0.15       # mỗi box phải chứa ≥ 15% pixel của segment bị gộp
MERGE_UNION_IOU = 0.7    # bbox segment ≈ hợp các box
DRIFT_MIN_IOU = 0.3      # box vẫn chồng lên segment (không phải box của vật ở chỗ khác)
DRIFT_MAX_EDGES = 2      # lô sạch: 434/435 box khớp ≥ 3 mép với segment; box bị dịch thường khớp ≤ 2 mép
EDGE_TOL = 0.03          # mép coi là khớp nếu lệch ≤ 3% kích thước box (tối thiểu 2 px)
MISSING_AREA = 0.005     # bbox segment ≥ 0.5% diện tích ảnh mới coi là "vật đáng kể"
MISSING_IOU = 0.3        # không box cùng lớp nào có IoU ≥ ngưỡng này với segment


def seg_runs(d: Delivery, stem: str) -> dict[int, list[tuple[int, int, int]]]:
    """{segment_id: [(y, x0, x1_exclusive), ...]}: mã hoá mask theo đoạn trên từng hàng (nhanh hơn duyệt từng pixel)."""
    m = d.mask(stem)
    if m is None:
        return {}
    w, h, px = m
    buf = bytearray(w * h * 4)                       # RGB -> số nguyên 32 bit: id = R + G*256 + B*65536
    buf[0::4], buf[1::4], buf[2::4] = px[0::3], px[1::3], px[2::3]
    ids = array("I", bytes(buf))
    runs: dict[int, list] = {}
    for y in range(h):
        x = 0
        for sid, grp in groupby(ids[y * w:(y + 1) * w]):
            n = sum(1 for _ in grp)
            if sid:
                runs.setdefault(sid, []).append((y, x, x + n))
            x += n
    return runs


def inside(runs, box) -> int:
    """Số pixel của segment nằm trong box (x1, y1, x2, y2), xét theo tâm pixel."""
    x1, y1, x2, y2 = box
    n = 0
    for y, a, b in runs:
        if y + 0.5 < y1 or y + 0.5 > y2:
            continue
        lo, hi = max(a, x1 - 0.5), min(b, x2 - 0.5)
        if hi > lo:
            n += int(hi) - int(lo)
    return n


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def edges_matched(box, sb) -> int:
    """Số mép (trái, trên, phải, dưới) của box khớp mép bbox segment."""
    tol = (max(2.0, EDGE_TOL * (box[2] - box[0])), max(2.0, EDGE_TOL * (box[3] - box[1])))
    return sum(abs(box[k] - sb[k]) <= tol[k % 2] for k in range(4))


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def cand(kind: str, stem: str, reason: str, box) -> dict:
    return {"type": kind, "target": stem, "reason": reason, "bbox": [round(v, 1) for v in box]}


def thing_segments(d: Delivery, stem: str) -> list[dict]:
    """Segment thing (không crowd) của ảnh: tên lớp, runs, số pixel thật, bbox tính từ mask."""
    runs = seg_runs(d, stem)
    out = []
    for s in d.segments.get(stem, []):
        cat = d.categories.get(s["category_id"])
        if not cat or not cat.get("isthing") or s.get("iscrowd") or s["id"] not in runs:
            continue
        r = runs[s["id"]]
        bb = (min(a for _, a, _ in r), min(y for y, _, _ in r), max(b for _, _, b in r), max(y for y, _, _ in r) + 1)
        out.append({"name": cat["name"], "runs": r, "area": sum(b - a for _, a, b in r), "bbox": bb})
    return out


def image_candidates(d: Delivery, stem: str) -> list[dict]:
    w, h = d.size(stem)
    if not w or stem not in d.segments or not d.path(stem, "image").is_file():
        return []
    dets = [(d.classes[c], (x1, y1, x2, y2)) for c, x1, y1, x2, y2 in d.labels(stem) if c in d.classes]
    segs = thing_segments(d, stem)
    if not segs:
        return []

    ins = [[inside(s["runs"], b) / s["area"] for _, b in dets] for s in segs]   # phần pixel segment j trong box i
    ious = [[iou(s["bbox"], b) for _, b in dets] for s in segs]
    out, used_det, used_seg = [], set(), set()

    def own_match(j, i):  # khớp tốt: trùng chỗ, chứa gần hết pixel, và mép box khít mép segment
        return (ious[j][i] >= MATCH_IOU and ins[j][i] >= MATCH_INSIDE
                and edges_matched(dets[i][1], segs[j]["bbox"]) > DRIFT_MAX_EDGES)

    # 1. cặp khớp tốt và cùng lớp: đánh dấu đã dùng
    for j, s in enumerate(segs):
        for i, (name, _) in enumerate(dets):
            if name == s["name"] and own_match(j, i):
                used_det.add(i)
                used_seg.add(j)

    # 2. instance_merge: segment trải trên ≥ 2 box cùng lớp mà các box đó không có segment riêng
    for j, s in enumerate(segs):
        parts = [i for i, (name, _) in enumerate(dets)
                 if name == s["name"] and ins[j][i] >= MERGE_SHARE
                 and not any(own_match(k, i) and segs[k]["name"] == name for k in range(len(segs)) if k != j)]
        if len(parts) >= 2 and iou(s["bbox"], union([dets[i][1] for i in parts])) >= MERGE_UNION_IOU:
            out.append(cand("instance_merge", stem, f"1 segment {s['name']} phủ {len(parts)} box cùng lớp", s["bbox"]))
            used_seg.add(j)
            used_det.update(parts)

    # 3. swap: trùng chỗ, khác lớp, không có cặp cùng lớp nào ở đó
    for j, s in enumerate(segs):
        if j in used_seg:
            continue
        for i, (name, b) in enumerate(dets):
            if i in used_det or name == s["name"] or not own_match(j, i):
                continue
            out.append(cand("swap", stem, f"detection ghi '{name}', panoptic ghi '{s['name']}'", b))
            used_seg.add(j)
            used_det.add(i)
            break

    # 4. bbox_drift: box chưa khớp, chồng lên segment cùng lớp nhưng mép không khớp
    for i, (name, b) in enumerate(dets):
        if i in used_det:
            continue
        same = [j for j, s in enumerate(segs) if s["name"] == name and j not in used_seg]
        if not same:
            continue
        j = max(same, key=lambda j: ious[j][i])
        if ious[j][i] >= DRIFT_MIN_IOU and edges_matched(b, segs[j]["bbox"]) <= DRIFT_MAX_EDGES:
            out.append(cand("bbox_drift", stem,
                            f"box {name}: IoU {ious[j][i]:.2f}, {ins[j][i]:.0%} pixel segment trong box, "
                            f"{edges_matched(b, segs[j]['bbox'])}/4 mép khớp", union([b, segs[j]["bbox"]])))
            used_det.add(i)
            used_seg.add(j)

    # 5. missing_box (TV4): segment đủ lớn, không có box cùng lớp nào ở đó
    for j, s in enumerate(segs):
        x1, y1, x2, y2 = s["bbox"]
        if j in used_seg or (x2 - x1) * (y2 - y1) < MISSING_AREA * w * h:
            continue
        if all(ious[j][i] < MISSING_IOU for i, (name, _) in enumerate(dets) if name == s["name"]):
            out.append(cand("missing_box", stem, f"segment {s['name']} ({s['area']} px) không có box", s["bbox"]))
    return out


def candidates(d: Delivery) -> list[dict]:
    out = []
    for stem in d.stems:
        out.extend(image_candidates(d, stem))
    return out
