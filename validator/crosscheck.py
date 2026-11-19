"""Đối chiếu detection ↔ panoptic, sinh ứng viên lỗi gán nhãn (TV2 — Nguyễn Thị Ngọc Mai; missing_box: TV4).

TODO:
  match(d, stem)  : ghép box ↔ segment thing (qua tên lớp, theo pixel mask), bỏ iscrowd
  class_swap / category_swap : trùng chỗ, khác lớp
  bbox_drift      : nhiều pixel segment cùng lớp rơi ra ngoài box
  instance_merge  : một segment có pixel trong 2 box cùng lớp
  missing_box     : segment thing lớn không có box (TV4)

Mỗi ứng viên: {"type": ..., "target": stem, "reason": "..."}.
Dùng: d.labels(stem), d.segments[stem], d.mask(stem), d.classes, d.categories. Xem common.py.
"""
from __future__ import annotations

from common import Delivery  # noqa: F401


def candidates(d: Delivery) -> list[dict]:
    return []
