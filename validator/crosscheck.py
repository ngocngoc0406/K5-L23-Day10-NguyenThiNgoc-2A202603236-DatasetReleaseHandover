"""Đối chiếu detection ↔ panoptic, sinh ứng viên lỗi gán nhãn (TV2 — Nguyễn Thị Ngọc Mai; missing_box: TV4).

Mỗi ứng viên: {"type": ..., "target": stem, "reason": "..."}.
Dùng: d.labels(stem), d.segments[stem], d.mask(stem), d.classes, d.categories. Xem common.py.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from common import Delivery

# --- CÁC NGƯỠNG TINH CHỈNH (Chạy thử trên runs/clean để điều chỉnh) ---
TH_SWAP_IN_BOX = 0.65      # Tỉ lệ pixel segment nằm trong box để coi là khớp vị trí (bắt swap)
TH_SWAP_BOX_COVER = 0.45   # Tỉ lệ diện tích box được segment che phủ (tránh box to nuốt vật nhỏ)
TH_DRIFT_IN_BOX = 0.72     # Dưới mức này (nhưng > TH_DRIFT_MIN) thì coi là bbox_drift
TH_DRIFT_MIN = 0.25        # Tối thiểu pixel nằm trong box để biết box đang gán cho segment này
TH_MERGE_IN_BOX = 0.25     # Tỉ lệ pixel của 1 segment nằm trong MỖI box (khi có >= 2 box cùng lớp)
MIN_SEG_PIXELS = 150       # Bỏ qua các mảnh segment quá nhỏ (nhiễu tự nhiên của COCO)


def _analyze_stem(d: Delivery, stem: str) -> dict | None:
    """Tính toán ma trận đếm pixel giao nhau giữa mọi box detection và segment panoptic của 1 ảnh."""
    m = d.mask(stem)
    if m is None:
        return None
    w, h, px = m
    labels = d.labels(stem)
    segs = d.segments.get(stem, [])

    # Lọc các segment là 'thing' và không phải 'iscrowd'
    thing_segs = {}
    for s in segs:
        if s.get("iscrowd", 0) == 1:
            continue
        cat = d.categories.get(s["category_id"])
        if not cat or cat.get("isthing", 0) != 1:
            continue
        thing_segs[s["id"]] = {
            "id": s["id"],
            "category_id": s["category_id"],
            "name": cat["name"],
            "bbox": s.get("bbox", [0, 0, 0, 0]),
            "area": s.get("area", 0),
        }

    if not thing_segs and not labels:
        return None

    # Chuyển đổi tọa độ box sang dạng số nguyên kẹp trong khung ảnh
    boxes = []
    for idx, (cid, x1, y1, x2, y2) in enumerate(labels):
        ix1 = max(0, min(w, int(round(x1))))
        iy1 = max(0, min(h, int(round(y1))))
        ix2 = max(0, min(w, int(round(x2))))
        iy2 = max(0, min(h, int(round(y2))))
        area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        boxes.append({
            "idx": idx,
            "class_id": cid,
            "name": d.classes.get(cid, f"cls_{cid}"),
            "coords": (ix1, iy1, ix2, iy2),
            "area": area,
        })

    # Tổng pixel thật của từng segment trên toàn ảnh
    total_counts = d.pixel_counts(stem)

    # Đếm số pixel của từng segment nằm bên trong từng box
    # box_seg_pixels[box_idx][seg_id] = count
    box_seg_pixels: list[Counter] = []
    for b in boxes:
        ix1, iy1, ix2, iy2 = b["coords"]
        c = Counter()
        if ix2 > ix1 and iy2 > iy1:
            for y in range(iy1, iy2):
                row_offset = y * w * 3
                start = row_offset + ix1 * 3
                end = row_offset + ix2 * 3
                row_slice = px[start:end]
                for r, g, bl in zip(row_slice[0::3], row_slice[1::3], row_slice[2::3]):
                    sid = r + g * 256 + bl * 65536
                    if sid in thing_segs:
                        c[sid] += 1
        box_seg_pixels.append(c)

    return {
        "w": w,
        "h": h,
        "boxes": boxes,
        "thing_segs": thing_segs,
        "total_counts": total_counts,
        "box_seg_pixels": box_seg_pixels,
    }


def match(d: Delivery, stem: str) -> dict:
    """Ghép box detection <-> segment thing (qua tên lớp, theo pixel mask), bỏ iscrowd.

    Trả về dict chứa:
      - 'pairs': [(box_dict, seg_dict, pixels_in_box, seg_total_pixels), ...] các cặp đã ghép
      - 'unmatched_boxes': [box_dict, ...]
      - 'unmatched_segs': [seg_dict, ...] (hữu ích cho TV4 viết missing_box)
      - 'raw': dữ liệu phân tích chi tiết của ảnh
    """
    info = _analyze_stem(d, stem)
    if info is None:
        return {"pairs": [], "unmatched_boxes": [], "unmatched_segs": [], "raw": None}

    boxes = info["boxes"]
    thing_segs = info["thing_segs"]
    total_counts = info["total_counts"]
    box_seg_pixels = info["box_seg_pixels"]

    # Tìm tất cả ứng viên ghép tiềm năng theo độ chồng lấp pixel
    potential = []
    for b in boxes:
        b_idx = b["idx"]
        for sid, in_px in box_seg_pixels[b_idx].items():
            seg_tot = total_counts.get(sid, 0)
            if seg_tot < MIN_SEG_PIXELS or b["area"] <= 0:
                continue
            seg_ratio = in_px / seg_tot      # Tỉ lệ pixel của segment nằm trong box
            box_ratio = in_px / b["area"]    # Tỉ lệ diện tích box được segment lấp đầy
            # Ưu tiên cặp cùng tên lớp nếu độ chồng lấp tương đương
            same_cls = 1 if b["name"] == thing_segs[sid]["name"] else 0
            score = seg_ratio * 0.7 + box_ratio * 0.3 + same_cls * 0.15
            if seg_ratio >= TH_DRIFT_MIN:
                potential.append((score, b_idx, sid, in_px, seg_tot))

    # Ghép tham lam 1-1 theo điểm số cao nhất
    potential.sort(key=lambda x: x[0], reverse=True)
    matched_b = set()
    matched_s = set()
    pairs = []

    for _, b_idx, sid, in_px, seg_tot in potential:
        if b_idx in matched_b or sid in matched_s:
            continue
        matched_b.add(b_idx)
        matched_s.add(sid)
        pairs.append((boxes[b_idx], thing_segs[sid], in_px, seg_tot))

    unmatched_boxes = [b for b in boxes if b["idx"] not in matched_b]
    unmatched_segs = [
        s for sid, s in thing_segs.items()
        if sid not in matched_s and total_counts.get(sid, 0) >= MIN_SEG_PIXELS
    ]

    return {
        "pairs": pairs,
        "unmatched_boxes": unmatched_boxes,
        "unmatched_segs": unmatched_segs,
        "raw": info,
    }


def _check_stem(d: Delivery, stem: str) -> list[dict]:
    res = match(d, stem)
    info = res["raw"]
    if info is None:
        return []

    out = []
    seen_types = set()

    def add_cand(ctype: str, reason: str) -> None:
        # Mỗi loại lỗi chỉ báo tối đa 1 ứng viên trên mỗi ảnh
        if ctype not in seen_types:
            seen_types.add(ctype)
            out.append({"type": ctype, "target": stem, "reason": reason})

    # 1. Kiểm tra class_swap / category_swap và bbox_drift trên các cặp đã ghép
    for b, seg, in_px, seg_tot in res["pairs"]:
        seg_ratio = in_px / seg_tot
        box_ratio = in_px / b["area"] if b["area"] > 0 else 0.0

        if b["name"] != seg["name"]:
            # Trùng vị trí chặt chẽ nhưng khác tên lớp
            if seg_ratio >= TH_SWAP_IN_BOX and box_ratio >= TH_SWAP_BOX_COVER:
                add_cand(
                    "class_swap",
                    f"det='{b['name']}' vs pan='{seg['name']}' (in_box={seg_ratio:.2f}, box_cov={box_ratio:.2f})",
                )
        else:
            # Cùng lớp nhưng nhiều pixel của segment bị rơi ra ngoài box
            if TH_DRIFT_MIN <= seg_ratio < TH_DRIFT_IN_BOX:
                add_cand(
                    "bbox_drift",
                    f"'{b['name']}' lệch box: chỉ {seg_ratio:.2f} pixel segment nằm trong box ({in_px}/{seg_tot})",
                )

    # 2. Kiểm tra instance_merge: 1 segment lớn phủ lên >= 2 box cùng lớp tách biệt
    boxes = info["boxes"]
    thing_segs = info["thing_segs"]
    total_counts = info["total_counts"]
    box_seg_pixels = info["box_seg_pixels"]

    seg_to_same_cls_boxes = defaultdict(list)
    for b in boxes:
        if b["area"] <= 0:
            continue
        for sid, in_px in box_seg_pixels[b["idx"]].items():
            seg = thing_segs[sid]
            seg_tot = total_counts.get(sid, 0)
            if seg_tot < MIN_SEG_PIXELS:
                continue
            seg_ratio = in_px / seg_tot
            box_ratio = in_px / b["area"]  # Segment phải chiếm ít nhất 25% diện tích box đó
            if b["name"] == seg["name"] and seg_ratio >= TH_MERGE_IN_BOX and box_ratio >= 0.25:
                seg_to_same_cls_boxes[sid].append((b, seg_ratio, box_ratio))

    for sid, hit_boxes in seg_to_same_cls_boxes.items():
        if len(hit_boxes) >= 2:
            # Lọc bỏ cặp box mà box này nằm lọt thỏm bên trong box kia
            valid_boxes = []
            for i, (b1, sr1, br1) in enumerate(hit_boxes):
                x1, y1, x2, y2 = b1["coords"]
                is_contained = False
                for j, (b2, _, _) in enumerate(hit_boxes):
                    if i == j or b2["area"] <= b1["area"]:
                        continue
                    ox1, oy1, ox2, oy2 = b2["coords"]
                    inter = max(0, min(x2, ox2) - max(x1, ox1)) * max(0, min(y2, oy2) - max(y1, oy1))
                    if inter / b1["area"] > 0.70:  # b1 nằm lọt >70% trong b2 -> bỏ qua
                        is_contained = True
                        break
                if not is_contained:
                    valid_boxes.append((b1, sr1, br1))

            if len(valid_boxes) >= 2:
                seg_name = thing_segs[sid]["name"]
                ratios_str = ", ".join(f"box#{b['idx']}(seg={sr:.2f},box={br:.2f})" for b, sr, br in valid_boxes)
                add_cand(
                    "instance_merge",
                    f"segment '{seg_name}' (id={sid}) phủ {len(valid_boxes)} box cùng lớp: {ratios_str}",
                )

    return out


def candidates(d: Delivery) -> list[dict]:
    out = []
    for stem in d.stems:
        out.extend(_check_stem(d, stem))
    return out