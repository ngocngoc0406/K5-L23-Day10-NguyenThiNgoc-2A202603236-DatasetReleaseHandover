# Phân công nhóm — Day 10 Lab (làm song song)

| | Họ tên | MSHV | Phần chính |
|---|---|---|---|
| **TV1** | Nguyễn Mạnh Quang | 2A202603241 | 5 luật file + detection, công cụ xem ảnh |
| **TV2** | Nguyễn Thị Ngọc Mai | 2A202603188 | Đối chiếu det ↔ panoptic (swap, drift, merge), gộp review |
| **TV3** | Phạm Đức Mạnh | 2A202603079 | Lineage, dựng + đóng gói lô v2, export bài nộp |
| **TV4** | Nguyễn Thị Ngọc | 2A202603236 | 4 luật metadata + panoptic, `missing_box`, truy vết, bảo mật |

`<seed>` = seed luyện tập chung của nhóm. Giờ tính từ lúc bắt đầu lab.

## Nguyên tắc để 4 người làm cùng lúc

1. **Khung chung có sẵn trước buổi lab.** `validator/common.py` (hàm đọc dữ liệu) và `validator/validate.py` (CLI, gom kết quả) được viết và push **trước giờ lab**. Vào lab ai cũng viết ngay vào file của mình, không ai chờ ai.
2. **Mỗi người một file riêng**, cùng một kiểu hàm, nên không conflict git:

   | File | Ai | Hàm |
   |---|---|---|
   | `validator/common.py` | có sẵn | `load(delivery) -> d` (manifest, metadata, jobs, classes, labels theo pixel, panoptic, hàm đọc mask) |
   | `validator/rules_file.py` | Quang | `check(d) -> [{"type", "target"}]` |
   | `validator/rules_meta.py` | Ngọc | `check(d) -> [{"type", "target"}]` |
   | `validator/crosscheck.py` | Ngọc Mai | `candidates(d) -> [{"type", "target", "reason"}]` |
   | `validator/missing_box.py` | Ngọc | `candidates(d, match) -> [...]` (dùng hàm ghép của Ngọc Mai) |
   | `tools/view.py` | Quang | công cụ xem ảnh |
   | `tools/build_v2.py` | Mạnh | dựng lô v2 |
   | `tools/trace_query.py` | Ngọc | truy vết |

3. **Không đợi dữ liệu thật của người khác: tự làm dữ liệu giả để thử.**
   - Mạnh thử `build_v2.py` bằng một `errors.json` **tự viết tay** (mỗi loại lỗi lấy 1–2 ảnh bất kỳ), không đợi `errors.json` thật.
   - Ngọc làm truy vết chỉ cần `delivery/`, không phụ thuộc validator.
   - Quang làm `view.py` chỉ cần ảnh + mask, không phụ thuộc ứng viên.
4. **Chỉ có 2 điểm hẹn cả nhóm** (lúc đó ai cũng đã xong phần trước):
   - **1:15** Ngọc Mai đẩy `candidates.json` → cả 4 xem ảnh cùng lúc.
   - **1:50** có `errors.json` thật → Mạnh chạy lại `build_v2.py`, những người khác tiếp tục phần mình.
5. **Review mỗi người một file** `review_<tên>.csv` (`image,type,verdict,note`), note ≥ 20 ký tự nói thấy gì, có tên người xem. Ngọc Mai ghép lại.
6. Mỗi người ≥ 2 commit, tên và email của mình; `git pull` trước khi push. Dùng AI thì ghi vào `submission/prompts.md`. Không sửa `delivery/`, `scripts/`; không đọc `_private/`.

---

## Lịch song song

| Giờ | Quang (TV1) | Ngọc Mai (TV2) | Mạnh (TV3) | Ngọc (TV4) |
|---|---|---|---|---|
| **0:00–0:15** | P0 trên máy mình | P0 trên máy mình | P0 trên máy mình | P0 trên máy mình + `TEAM.md`, tiêu đề README |
| **0:15–0:55** | 5 luật `rules_file.py` | Hàm ghép box ↔ segment + `class_swap`/`category_swap` | Đọc `check_handover.py`; `build_v2.py` với `errors.json` giả: images/labels, rework, truyvet | 4 luật `rules_meta.py` |
| **0:55–1:15** | `view.py` | `bbox_drift`, `instance_merge`, chỉnh ngưỡng trên lô sạch | `build_v2.py`: manifest, label_summary, phần số liệu README | `missing_box.py`, đếm ứng viên lô sạch |
| **1:15–1:45** | **Xem ảnh phần 1** | **Xem ảnh phần 2** | **Xem ảnh phần 3** | **Xem ảnh phần 4** |
| **1:45–2:05** | Mở kiểm ảnh `wrong_hash`, báo Mạnh | Ghép review, `merge_review.py` → `errors.json` | HOLD + `impact` trong lineage | `trace_query.py` |
| **2:05–2:45** | Chạy thử validator + `view.py` trên 2 seed khác, sửa lỗi | Thử validator trên seed khác, soát FP | `build_v2.py` thật, `pack_release.py`, release lineage, `check_handover.py` | Ghi chú README v2, `trace.json`, `security.md` |
| **2:45–3:10** | REPORT §1 (F1 luật) | REPORT §2 | REPORT §3, §4; export, push | REPORT §1 (ứng viên lô sạch), §5, §6 |
| **3:10–3:15** | Pull, chạy thử trên máy mình | Pull, chạy thử | Pull, chạy thử | Pull, chạy thử |
| **3:15–3:55** | Đề ẩn | Đề ẩn | Đề ẩn | Đề ẩn |

**P0 (mỗi người trên máy mình):** `git clone` → `python scripts/download_public.py` → `python scripts/run_lab.py --seeds <seed>` (**một lần**) → `python scripts/inject_release.py --seed 5 --no-faults --out runs/clean` → `python scripts/inject_release.py --seed <X> --out runs/r<X>` (mỗi người một `<X>` khác).

---

## Chi tiết từng người

### 👤 Quang (TV1)
- [ ] `rules_file.py`:
  - `missing_image`: có trong manifest, thiếu file
  - `wrong_hash`: tự tính sha256 trên bytes (`rb`)
  - `invalid_class`: `class_id` ngoài 0–79
  - `bbox_out_of_bounds`: box vượt mép ảnh, kể cả tràn ít
  - `duplicate_box`: cùng lớp, cùng w/h, lệch tâm ≤ ~2 px
- [ ] Tự đo `score_findings.py` trên `r<seed>`, `r<X>`, `runs/clean`: F1 luật ≈ 1.0, lô sạch 0 lỗi → **Commit 1**
- [ ] `tools/view.py` (được dùng Pillow): vẽ box + viền segment, cắt và phóng to, nhận tên `img_0001`
- [ ] Xem phần 1 → `review_quang.csv`
- [ ] Mở kiểm từng ảnh `wrong_hash`: còn nguyên hay hỏng, báo Mạnh
- [ ] REPORT §1 (F1 luật theo seed) → **Commit 2**
- Vấn đáp: `wrong_hash`, `duplicate_box`, `view.py`

### 👤 Ngọc Mai (TV2)
- [ ] `crosscheck.py`:
  - ghép lớp qua tên (`classes.txt` ↔ `categories`); hàm `match(d)` ghép box ↔ segment thing theo pixel mask, bỏ `iscrowd` (**push sớm** để Ngọc dùng)
  - `class_swap`/`category_swap`: trùng chỗ, khác lớp
  - `bbox_drift`: nhiều pixel segment cùng lớp rơi ra ngoài box
  - `instance_merge`: một segment có pixel trong 2 box cùng lớp
- [ ] Chỉnh ngưỡng trên `runs/clean` (không dựa vào tham số `inject_release.py`) → **Commit 1**
- [ ] 1:15: đẩy `candidates.json`, chia 4 phần; xem phần 2 → `review_mai.csv`
- [ ] Ghép 4 file review → `review_log.csv`; `merge_review.py --rules rules.json --review review_log.csv --out errors.json`; `score_findings.py`; gửi Mạnh
- [ ] REPORT §2 (vì sao báo hết làm F1 giảm, bằng số của nhóm) → **Commit 2**
- Vấn đáp: ghép bằng pixel mask, phân biệt swap/drift/merge

### 👤 Mạnh (TV3)
- [x] Đọc `scripts/check_handover.py`, ghi H1–H17 kiểm gì — xem `submission/TV3_CHECKS.txt`.
- [x] Viết tay `errors_test.json` (mỗi loại lỗi 1–2 ảnh) để thử — 14 loại, 16 trường hợp giả; đã kiểm thử riêng, không dùng làm kết quả thật.
- [x] `tools/build_v2.py` tạo `runs/r<seed>/handover/<id>_v2/`:
  - images/labels của v1, **bỏ** ảnh lỗi detection hoặc thiếu file; ảnh chỉ lỗi panoptic **ở lại**
  - `rework_queue.csv` (người theo `jobs.csv`), `truyvet.csv` (guideline theo job, mỗi cảnh một split)
  - `manifest.csv`, `label_summary.csv` (+ `TOTAL`), `README.txt` (số liệu tự sinh + Ghi chú của Ngọc)
- [x] Xem phần 3 → `review_manh.csv` — đã chốt 3/3 ảnh đề ẩn và 3/3 ảnh phần 3/4 lô luyện tập; hai file nằm riêng ở `reviews/review_manh.csv` và `reviews/r68007/review_manh.csv`, ghi chú mô tả chi tiết đối chiếu ảnh thực tế.
- [x] QC v1 = số ảnh lỗi / 250, trên 2% thì HOLD: `lineage.py record --event decision --release-id <id> --decision HOLD`; `lineage.py impact --release-id <id>` → `R-021: affected=True` — chạy thật được 12/250 = 4,8%, gồm 9 lỗi luật và 3 lỗi review đã xác nhận.
- [x] Chạy `build_v2.py` với `errors.json` thật → `pack_release.py` → `lineage.py record --event release --release-id <id>_v2 --parent <id>` → `check_handover.py --run runs/r<seed>` → **Commit 1** (`e8e6cc6`). Pipeline thật đạt 17 PASS, 0 FAIL; v2 Hold vì còn 8 ứng viên chờ review.
- [x] REPORT §3, §4; nhận `trace.json`, `security.md` từ Ngọc; `check_handover.py` không còn FAIL; `export_submission.py --run runs/r<seed>` → **Commit 2**, push bản bàn giao hiện tại theo yêu cầu. Bản export có 245 ảnh, 1.667 box, 5 ảnh rework và giữ Hold; việc chốt bản Release cuối chờ 8 review còn lại.
- Vấn đáp: mọi con số trong `README.txt` v2, hash chứng minh gì

### 👤 Ngọc (TV4)
- [ ] `TEAM.md` (số nhóm, seed, GitHub), tiêu đề README → commit "P0: chia viec"
- [ ] `rules_meta.py`:
  - `scene_leak`: cảnh có ảnh ở cả train và val, target = `scene_id`
  - `guideline_mismatch`: guideline ảnh ≠ guideline job
  - `invalid_category_id`: không có trong `categories`
  - `thing_overlap`: đếm pixel mask (`scripts/pngutil.py`, id = R + G·256 + B·256², bỏ id 0), `area` khai > pixel thật
- [ ] Tự đo trên các seed và lô sạch → **Commit 1**
- [ ] `missing_box.py`: segment thing lớn không có box (dùng `match` của Ngọc Mai); đếm ứng viên lô sạch, gửi Ngọc Mai
- [ ] Xem phần 4 → `review_ngoc.csv`
- [ ] `tools/trace_query.py`: `tier_a` (cảnh bị báo + job guideline cũ + có box lớp bị đổi), `tier_b` (ảnh khác cùng điều kiện), `notify` (người gán + kiểm của các job đó) → `trace.json`
- [ ] Ghi chú README v2 (đã sửa hash/guideline/split, ảnh lỗi panoptic ở lại), gửi Mạnh
- [ ] `security.md` (ca USB, năm việc được/không, ca khuôn mặt Hold + báo người phụ trách, tên ảnh có người)
- [ ] REPORT §1 (ứng viên lô sạch, ngưỡng), §5, §6 → **Commit 2**
- Vấn đáp: `thing_overlap`, `scene_leak`, tầng a/b, ca khuôn mặt

---

## Đề ẩn (3:15–3:55): cả 4 người cùng lúc

Mỗi người tự tải `de_an.zip` (tab Releases), giải nén vào gốc repo, chạy:
`python validator/validate.py delivery --out submission/de_an/rules.json --candidates submission/de_an/candidates.json`

Validator chạy giống nhau trên mọi máy nên cả 4 có cùng `candidates.json`. **Chia theo số thứ tự ứng viên** (1/4 đầu là Quang, tiếp theo là Ngọc Mai…), không cần ai chia giùm.

| Phút | Quang | Ngọc Mai | Mạnh | Ngọc |
|---|---|---|---|---|
| 0–5 | Tải, chạy validator | Tải, chạy validator | Tải, chạy, soát lỗi luật | Tải, chạy `trace_query.py` |
| 5–30 | Xem phần 1 | Xem phần 2 | Xem phần 3 | Xem phần 4 |
| 30–35 | Gửi `review_quang.csv` | Ghép review, `merge_review.py` → `errors.json` | Soát `class_swap` vs `category_swap` | Chốt `trace.json`, gửi Ngọc Mai |
| 35–40 | Soát note ≥ 20 ký tự | Commit + push `submission/de_an/` (không commit `delivery/`) | Kiểm lần cuối trên GitHub | Nộp link lên LMS |
