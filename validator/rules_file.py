"""Luật file + detection (TV1 — Nguyễn Mạnh Quang).

TODO:
  missing_image      : có trong manifest nhưng thiếu file ảnh
  wrong_hash         : sha256 tự tính trên bytes (đọc "rb") khác manifest
  invalid_class      : class_id ngoài 0–79
  bbox_out_of_bounds : box vượt mép ảnh (kể cả tràn ít)
  duplicate_box      : cùng lớp, cùng w/h, lệch tâm ≤ ~2 px

Dùng: d.stems, d.manifest[stem], d.path(stem, "image"), d.labels(stem), d.size(stem). Xem common.py.
"""
from __future__ import annotations

from common import Delivery, err  # noqa: F401


def check(d: Delivery) -> list[dict]:
    return []
