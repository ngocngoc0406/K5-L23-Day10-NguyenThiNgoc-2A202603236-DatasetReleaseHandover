"""Luật file + detection (TV1 — Nguyễn Mạnh Quang).

missing_image      : có trong manifest nhưng thiếu file ảnh
wrong_hash         : sha256 tự tính trên bytes (đọc "rb") khác sha256 ghi trong manifest
invalid_class      : class_id ngoài khoảng của classes.txt (0–79)
bbox_out_of_bounds : box vượt mép ảnh (kể cả tràn ít)
duplicate_box      : hai box cùng lớp, cùng kích thước, tâm lệch nhau ≤ vài pixel

Mỗi ảnh mang nhiều nhất một lỗi, nên khi một ảnh đã có lỗi file thì không xét tiếp nhãn của nó.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from common import Delivery, err

# Nhãn YOLO ghi 6 chữ số thập phân: làm tròn tự nhiên có thể vượt mép khoảng 1e-6.
# Box "tràn mép một chút" do lỗi thì vượt nhiều hơn hẳn mức đó.
EDGE_EPS = 1e-4          # theo toạ độ chuẩn hoá 0–1
DUP_SIZE_PX = 1.0        # chênh lệch w/h tối đa (pixel) để coi là "cùng kích thước"
DUP_SHIFT_PX = 3.0       # tâm lệch tối đa (pixel) để coi là box lặp


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def raw_labels(d: Delivery, stem: str) -> list[tuple[int, float, float, float, float]]:
    """(class_id, xc, yc, w, h) chuẩn hoá, đọc thẳng từ file."""
    p = d.path(stem, "label")
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 5:
            out.append((int(float(parts[0])), *(float(v) for v in parts[1:])))
    return out


def file_error(d: Delivery, stem: str) -> dict | None:
    item = d.manifest[stem]
    img = d.path(stem, "image")
    if not img.is_file():
        return err("missing_image", stem)
    for kind in ("image", "label", "mask"):
        p = d.path(stem, kind)
        want = item.get(f"{kind}_sha256")
        if want and p.is_file() and sha256(p) != want:
            return err("wrong_hash", stem)
    return None


def label_error(d: Delivery, stem: str) -> dict | None:
    boxes = raw_labels(d, stem)
    n_classes = len(d.classes)
    if any(not 0 <= b[0] < n_classes for b in boxes):
        return err("invalid_class", stem)
    for _, xc, yc, bw, bh in boxes:
        if xc - bw / 2 < -EDGE_EPS or yc - bh / 2 < -EDGE_EPS or xc + bw / 2 > 1 + EDGE_EPS or yc + bh / 2 > 1 + EDGE_EPS:
            return err("bbox_out_of_bounds", stem)
    w, h = d.size(stem)
    px = [(c, xc * w, yc * h, bw * w, bh * h) for c, xc, yc, bw, bh in boxes]
    for i in range(len(px)):
        for j in range(i + 1, len(px)):
            a, b = px[i], px[j]
            if a[0] != b[0]:
                continue
            same_size = abs(a[3] - b[3]) <= DUP_SIZE_PX and abs(a[4] - b[4]) <= DUP_SIZE_PX
            shift = max(abs(a[1] - b[1]), abs(a[2] - b[2]))
            if same_size and shift <= DUP_SHIFT_PX:
                return err("duplicate_box", stem)
    return None


def check(d: Delivery) -> list[dict]:
    out = []
    for stem in d.stems:
        e = file_error(d, stem) or label_error(d, stem)
        if e:
            out.append(e)
    return out
