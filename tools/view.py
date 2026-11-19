"""Công cụ xem ảnh để review (TV1 — Nguyễn Mạnh Quang). Được dùng Pillow (validator thì không).

Vẽ hai khung cạnh nhau cho mỗi ảnh:
  trái : ảnh + box DETECTION (labels/), ghi số thứ tự và tên lớp
  phải : ảnh + viền segment PANOPTIC (masks/), ghi tên category của segment thing
Ảnh nhỏ được phóng to. Ứng viên có "bbox" [x1, y1, x2, y2] thì có thêm khung cắt phóng to quanh vùng đó.

  # một ảnh
  python tools/view.py runs/r68007/delivery --image 000000000139 --out review_imgs
  # phần k/n của hàng đợi ứng viên (chia theo thứ tự trong file)
  python tools/view.py runs/r68007/delivery --candidates runs/r68007/candidates.json --part 4/4 --out review_imgs
  # in danh sách ảnh của phần mình (để ghi review_<tên>.csv)
  python tools/view.py runs/r68007/delivery --candidates runs/r68007/candidates.json --part 4/4 --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validator"))
from common import Delivery  # noqa: E402

PALETTE = [(255, 59, 48), (52, 199, 89), (0, 122, 255), (255, 149, 0), (175, 82, 222),
           (255, 204, 0), (90, 200, 250), (255, 45, 85), (162, 132, 94), (0, 199, 190)]
MIN_W = 900  # phóng to tới ít nhất chiều rộng này


def font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf", "Arial.ttf"):  # font có dấu tiếng Việt (Windows / Linux / macOS)
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def label(draw: ImageDraw.ImageDraw, xy, text: str, color, f) -> None:
    x, y = xy
    l, t, r, b = draw.textbbox((x, y), text, font=f)
    draw.rectangle((l - 2, t - 1, r + 2, b + 1), fill=(0, 0, 0))
    draw.text((x, y), text, fill=color, font=f)


def det_panel(d: Delivery, stem: str, img: Image.Image, scale: float, f) -> Image.Image:
    out = img.copy()
    dr = ImageDraw.Draw(out)
    for i, (cid, x1, y1, x2, y2) in enumerate(d.labels(stem)):
        c = PALETTE[cid % len(PALETTE)]
        box = [v * scale for v in (x1, y1, x2, y2)]
        dr.rectangle(box, outline=c, width=2)
        label(dr, (box[0] + 2, box[1] + 2), f"#{i} {d.classes.get(cid, f'?{cid}')}", c, f)
    label(dr, (6, 6), "DETECTION", (255, 255, 255), f)
    return out


def pan_panel(d: Delivery, stem: str, img: Image.Image, scale: float, f) -> Image.Image:
    out = img.copy()
    m = d.mask(stem)
    if m is not None:
        w, h, px = m
        mask = Image.frombytes("RGB", (w, h), bytes(px)).resize(img.size, Image.NEAREST)
        edge = ImageChops.add(ImageChops.difference(mask, ImageChops.offset(mask, 1, 0)),
                              ImageChops.difference(mask, ImageChops.offset(mask, 0, 1)))
        edge = edge.convert("L").point(lambda v: 255 if v else 0)
        out.paste((255, 255, 0), mask=edge)
    dr = ImageDraw.Draw(out)
    for s in d.segments.get(stem, []):
        cat = d.categories.get(s["category_id"], {})
        if not cat.get("isthing", 1):
            continue
        x, y, bw, bh = s["bbox"]
        name = cat.get("name", f"?{s['category_id']}") + (" (crowd)" if s.get("iscrowd") else "")
        label(dr, (x * scale + 2, y * scale + 2), name, (255, 255, 0), f)
    label(dr, (6, 6), "PANOPTIC", (255, 255, 255), f)
    return out


def render(d: Delivery, stem: str, cand: dict | None, out_dir: Path, idx: int | None = None) -> Path:
    p = d.path(stem, "image")
    if not p.is_file():
        print(f"  {stem}: thiếu file ảnh")
        return None
    img = Image.open(p).convert("RGB")
    scale = max(1.0, MIN_W / img.width)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    f = font(max(12, int(14 * scale ** 0.5)))
    left, right = det_panel(d, stem, img, scale, f), pan_panel(d, stem, img, scale, f)
    panels = [left, right]
    if cand and cand.get("bbox"):
        x1, y1, x2, y2 = cand["bbox"]
        pad = 0.5 * max(x2 - x1, y2 - y1, 20)
        crop = [max(0, (x1 - pad) * scale), max(0, (y1 - pad) * scale),
                min(img.width, (x2 + pad) * scale), min(img.height, (y2 + pad) * scale)]
        for panel in (left, right):
            c = panel.crop(crop)
            k = img.height / max(1, c.height)
            panels.append(c.resize((max(1, round(c.width * k)), img.height), Image.LANCZOS))
    head = 30
    sheet = Image.new("RGB", (sum(pn.width for pn in panels) + 8 * (len(panels) - 1), img.height + head), (30, 30, 30))
    x = 0
    for pn in panels:
        sheet.paste(pn, (x, head))
        x += pn.width + 8
    title = stem if not cand else f"{stem} | {cand.get('type', '')} | {cand.get('reason', '')}"
    ImageDraw.Draw(sheet).text((8, 6), title, fill=(255, 255, 255), font=font(16))
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{idx:03d}_" if idx is not None else ""
    dest = out_dir / f"{name}{stem}{'__' + cand['type'] if cand else ''}.png"
    sheet.save(dest)
    return dest


def part_of(items: list, part: str) -> list:
    k, n = (int(v) for v in part.split("/"))
    size = -(-len(items) // n)
    return items[(k - 1) * size: k * size]


def main() -> int:
    ap = argparse.ArgumentParser(description="Vẽ box detection + viền panoptic để xem ảnh")
    ap.add_argument("delivery")
    ap.add_argument("--image", action="append", help="tên ảnh (không đuôi); lặp lại được")
    ap.add_argument("--candidates", help="candidates.json")
    ap.add_argument("--part", default="1/1", help="phần k/n của hàng đợi, ví dụ 2/4")
    ap.add_argument("--list", action="store_true", help="chỉ in danh sách ứng viên của phần này")
    ap.add_argument("--out", default="review_imgs")
    args = ap.parse_args()

    d = Delivery(args.delivery)
    out_dir = Path(args.out)
    if args.candidates:
        cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
        cands = cands.get("errors", cands.get("candidates", [])) if isinstance(cands, dict) else cands
        mine = part_of(cands, args.part)
        print(f"phần {args.part}: {len(mine)}/{len(cands)} ứng viên")
        for i, c in enumerate(mine):
            if args.list:
                print(f"{c['target']},{c['type']},,")
            else:
                dest = render(d, c["target"], c, out_dir, i)
                if dest:
                    print(f"  {dest}")
    for stem in args.image or []:
        dest = render(d, stem, None, out_dir)
        if dest:
            print(f"  {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
