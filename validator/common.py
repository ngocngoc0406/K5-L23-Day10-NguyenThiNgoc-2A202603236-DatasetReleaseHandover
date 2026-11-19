"""Đọc một thư mục delivery thành một đối tượng dùng chung cho mọi luật.

Chỉ dùng thư viện chuẩn và scripts/pngutil.py. Chỉ đọc thư mục delivery được truyền vào.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pngutil  # noqa: E402


class Delivery:
    """Toàn bộ dữ liệu của một lô.

    d.root          : Path tới thư mục delivery
    d.manifest      : {stem: {"image", "label", "mask", "image_sha256", "label_sha256", "mask_sha256"}}
    d.meta          : {stem: {"scene_id", "split", "job_id", "guideline_version"}}
    d.jobs          : {job_id: {"annotator", "reviewer", "guideline"}}
    d.classes       : {class_id: tên lớp}            (detection, 0–79)
    d.categories    : {category_id: {"name", "isthing", ...}}   (panoptic)
    d.pan_images    : {stem: {"id", "width", "height", "file_name"}}
    d.segments      : {stem: [{"id", "category_id", "iscrowd", "bbox", "area"}, ...]}
    d.stems         : danh sách tên ảnh (không đuôi) theo manifest
    d.labels(stem)  : [(class_id, x1, y1, x2, y2)] theo pixel; [] nếu thiếu file
    d.mask(stem)    : (width, height, pixels RGB) hoặc None nếu thiếu mask
    d.pixel_counts(stem) : Counter {segment_id: số pixel} (bỏ id 0)
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.manifest = self._json("manifest.json").get("items", {})
        self.meta = {it["image"]: it for it in self._json("metadata.json").get("items", [])}
        self.jobs = {}
        with open(self.root / "jobs.csv", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                self.jobs[row["job_id"].strip()] = {k: (v or "").strip() for k, v in row.items()}
        self.classes = {}
        for line in (self.root / "classes.txt").read_text(encoding="utf-8").splitlines():
            if line.strip():
                cid, name = line.strip().split(" ", 1)
                self.classes[int(cid)] = name.strip()
        pan = self._json("panoptic.json")
        self.categories = {c["id"]: c for c in pan.get("categories", [])}
        by_id = {im["id"]: im for im in pan.get("images", [])}
        self.pan_images = {Path(im["file_name"]).stem: im for im in pan.get("images", [])}
        self.segments = {}
        for ann in pan.get("annotations", []):
            im = by_id.get(ann["image_id"])
            stem = Path(im["file_name"]).stem if im else Path(ann["file_name"]).stem
            self.segments[stem] = ann.get("segments_info", [])
        self.stems = list(self.manifest)
        self._mask_cache: dict[str, tuple] = {}

    def _json(self, name: str) -> dict:
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def path(self, stem: str, kind: str) -> Path:
        """kind = "image" | "label" | "mask"."""
        return self.root / self.manifest[stem][kind]

    def size(self, stem: str) -> tuple[int, int]:
        im = self.pan_images.get(stem, {})
        return im.get("width", 0), im.get("height", 0)

    def labels(self, stem: str) -> list[tuple[int, float, float, float, float]]:
        p = self.path(stem, "label")
        if not p.is_file():
            return []
        w, h = self.size(stem)
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 5:
                continue
            cid = int(float(parts[0]))
            xc, yc, bw, bh = (float(v) for v in parts[1:])
            out.append((cid, (xc - bw / 2) * w, (yc - bh / 2) * h, (xc + bw / 2) * w, (yc + bh / 2) * h))
        return out

    def mask(self, stem: str):
        if stem not in self._mask_cache:
            p = self.path(stem, "mask")
            self._mask_cache[stem] = pngutil.read_rgb(p) if p.is_file() else None
        return self._mask_cache[stem]

    def pixel_counts(self, stem: str) -> Counter:
        m = self.mask(stem)
        if m is None:
            return Counter()
        _, _, px = m
        counts = Counter(zip(px[0::3], px[1::3], px[2::3]))
        out = Counter({r + g * 256 + b * 65536: n for (r, g, b), n in counts.items()})
        out.pop(0, None)
        return out


def err(kind: str, target: str) -> dict:
    return {"type": kind, "target": target}
