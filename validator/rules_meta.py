"""Luật metadata + panoptic (TV4 — Nguyễn Thị Ngọc).

scene_leak          : một cảnh có ảnh ở cả train và val          -> target = scene_id
guideline_mismatch  : guideline của ảnh khác guideline của job     -> target = tên ảnh
invalid_category_id : segment có category_id không có trong categories -> target = tên ảnh
thing_overlap       : area khai > số pixel thật của segment trong mask -> target = tên ảnh
"""
from __future__ import annotations

from collections import defaultdict

from common import Delivery, err


def scene_leak(d: Delivery) -> list[dict]:
    splits = defaultdict(set)
    for stem, m in d.meta.items():
        splits[m["scene_id"]].add(m["split"])
    return [err("scene_leak", scene) for scene, s in sorted(splits.items()) if len(s) > 1]


def guideline_mismatch(d: Delivery) -> list[dict]:
    out = []
    for stem, m in d.meta.items():
        job = d.jobs.get(m["job_id"])
        if job and m["guideline_version"] != job["guideline"]:
            out.append(err("guideline_mismatch", stem))
    return out


def invalid_category_id(d: Delivery) -> list[dict]:
    out = []
    for stem, segs in d.segments.items():
        if any(s["category_id"] not in d.categories for s in segs):
            out.append(err("invalid_category_id", stem))
    return out


def thing_overlap(d: Delivery) -> list[dict]:
    out = []
    for stem, segs in d.segments.items():
        if stem not in d.manifest:
            continue
        counts = d.pixel_counts(stem)
        if not counts:
            continue
        if any(s["area"] > counts.get(s["id"], 0) for s in segs):
            out.append(err("thing_overlap", stem))
    return out


def check(d: Delivery) -> list[dict]:
    return scene_leak(d) + guideline_mismatch(d) + invalid_category_id(d) + thing_overlap(d)
