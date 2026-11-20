# Báo cáo nhóm 68

> Các mục ghi **[cập nhật sau review]** sẽ điền số cuối sau khi cả nhóm xem ảnh xong (review_log.csv).

## 1. Số liệu luyện tập
- **F1 lỗi luật** (`score_findings.py`, làm tròn 0,1): ≈ 1.0 trên seed luyện tập 68007 và các seed thử 68104, 11, 4242, lô giả lập đề ẩn `--opaque` seed 777; lô sạch `runs/clean` báo **0** lỗi luật.
- **Truy vết**: tier_a / tier_b / notify ≈ 1.0 / 1.0 / 1.0 trên cả 5 lô trên.
- **F1 lỗi gán nhãn sau review** (seed 68007): [cập nhật sau review].
- **Số ứng viên trên lô sạch** (`--no-faults`, 50 ảnh): bản đầu của crosscheck **5** (toàn `instance_merge`), bản cuối **1**. Hàng đợi trên seed luyện tập 68007: **11 ảnh** (bản đầu: 30).
- **Ngưỡng đã chọn và cách chọn** (không dùng `_private`):
  1. *Lô sạch*: mọi ứng viên ở đây là lệch tự nhiên của COCO → chọn ngưỡng sao cho số này nhỏ.
  2. *Lỗi giả tự gài* trong bộ nhớ trên lô sạch (dịch/đổi cỡ box, xoá box, đổi lớp, gộp 2 segment) để đo tỉ lệ bắt được từng loại: drift 90%, missing_box 92%, swap 98%, merge 91%.
  3. *Dấu hiệu bbox_drift*: đếm số mép box khớp mép bbox segment (lệch ≤ 3% cỡ box). Trên lô sạch 434/435 box khớp ≥ 3 mép; box bị dịch thường khớp ≤ 2 mép. Tỉ lệ pixel trong box đơn thuần không đủ (box phóng to vẫn chứa gần hết segment).
  4. *instance_merge*: chỉ báo khi bbox segment ≈ hợp của ≥ 2 box cùng lớp (IoU ≥ 0,7) và các box đó không có segment riêng; bỏ được các ca người đứng sát nhau.
  5. *duplicate_box*: cùng lớp, w/h chênh ≤ 1 px, tâm lệch ≤ 3 px (không dùng IoU vì COCO có cặp box tự nhiên chồng nhau tới IoU ~0,66). *bbox_out_of_bounds*: tràn > 1e-4 (toạ độ chuẩn hoá), lớn hơn sai số làm tròn 6 chữ số thập phân.

## 2. Vì sao báo hết ứng viên làm F1 giảm?
F1 tính trên cặp (type, target); báo thừa làm giảm precision y như bỏ sót làm giảm recall. Ứng viên chỉ là chỗ hai nguồn nhãn lệch nhau, mà COCO vốn lệch tự nhiên (vật bị che, crowd, mask panoptic khác instance mask). Số của nhóm: nếu coi **mọi** ứng viên là lỗi, F1 lỗi gán nhãn trên 4 seed chỉ **0,1–0,2** với bản crosscheck đầu (~30 ứng viên/lô, phần lớn là lệch tự nhiên) và **0,5–0,6** với bản cuối (~11 ứng viên/lô). Ngoài ra ứng viên `swap` không cho biết bên nào sai: báo bừa `class_swap` thì một nửa số ca sai loại. Phải mở ảnh để bỏ lệch tự nhiên (`rejected`) và chọn đúng loại, F1 sau review: [cập nhật sau review].

## 3. Quyết định và lineage
- **Kết quả chạy lại trên dữ liệu thật** (seed 68007, `lab250_1bfe29bf7f88`): validator đọc trực tiếp `runs/r68007/delivery/`, phát hiện **9 lỗi luật** trong `rules.json`. Sau khi ghép **3 lỗi gán nhãn đã được nhóm xem ảnh và xác nhận**, `errors.json` có **12 lỗi**. QC v1 hiện tại **12/250 = 4,8% > 2%** → **HOLD**. Đây là các lỗi đã xác nhận ở thời điểm báo cáo; còn 8 ứng viên chưa được review.
- `lineage.py impact` → `R-021: affected=True action=review_or_retrain`. R-021 đã train trên v1 có lỗi; sửa dataset thành v2 không làm model quên những gì đã học từ nhãn sai (box lệch, lớp sai, vật thiếu box). Vì vậy phải đánh giá lại R-021 trên dữ liệu đã sửa, và nếu lỗi ảnh hưởng (ví dụ lớp `truck` trong ticket) thì train lại trên v2.
- v2 `lab250_1bfe29bf7f88_v2` ghi `release --parent lab250_1bfe29bf7f88`, nên từ v2 truy ngược được về v1 và run R-021. Lineage có thêm quyết định **HOLD cho v2** vì còn 8 ứng viên chờ review.
- **Review lô luyện tập phần 3/4:** nhóm đã xem và xác nhận `000000009772` là `instance_merge` (hai bồn rửa bị gộp segment), `000000009914` là `missing_box` (thiếu box bát sốt xanh lớn), `000000012639` là `bbox_drift` (box người ngồi áo xanh lệch phải và xuống dưới). Ghi chú có nêu AI hỗ trợ soạn, lưu ở `reviews/r68007/review_manh.csv` và ghép vào `runs/r68007/review_log.csv`.
- **Tiến độ review đề ẩn ngày 20/11/2026:** nhóm đã kiểm tra và chốt 3 ảnh thuộc phần 3/4 trong `reviews/review_manh.csv`: `img_0108` confirmed `category_swap`; `img_0126` rejected `instance_merge`; `img_0136` rejected `bbox_drift`. AI hỗ trợ phân tích và soạn ghi chú, có ghi trong `prompts.md`. Kết quả của phần này chờ ghép với 9 ứng viên còn lại để hoàn thiện review chung của nhóm.
- **Bản bàn giao từ kết quả thật:** **245 ảnh, 1.667 box, 5 ảnh rework**. Ba ảnh chỉ lỗi panoptic vẫn ở lại sản phẩm detection. Nhóm đã review 3/11 ứng viên; 8 ứng viên còn lại được ghi riêng trong `submission/r68007/review_pending.json`. V2 giữ trạng thái **Hold**, chờ hoàn tất các review còn lại trước khi chốt để train.
- **Bằng chứng theo checklist TV3:** ghi chú H1–H17 nằm trong `submission/TV3_CHECKS.txt`. `errors_test.json` chỉ là bộ kiểm thử công cụ đã được tách riêng; không được đọc hoặc ghép vào lần chạy kết quả thật này. Số liệu kiểm thử được lưu riêng trong `runs/tv3_checks/fixture_summary.json`, không dùng làm số liệu QC hoặc F1.
- **Pipeline bàn giao:** chạy lại validator để tạo `rules.json` và `candidates.json`; ghép review đã xác nhận thành `errors.json`; chạy `build_v2.py --pending-review 8`, `pack_release.py`, truy vấn `lineage.py impact`, kiểm tra bàn giao và `export_submission.py --run runs/r68007`. `trace.json` và `security.md` đã nhận được giữ nguyên. Log và số liệu chạy thật lưu trong `runs/tv3_checks/real_rerun/`. V1 giữ nguyên; bản export đang Hold chờ hoàn tất 8 review còn lại.

## 4. Hash chứng minh gì, không chứng minh gì?
- **Chứng minh**: file không đổi một byte nào so với lúc lập manifest. Nhờ vậy biết v1 không bị ghi đè (H1), nhãn trong v2 đúng là nhãn đã gán, không sửa tay (H7), và zip v2 đóng gói lại ra đúng mã `.sha256` (H15). `wrong_hash` cũng được phát hiện bằng cách tự tính sha256 trên bytes rồi so.
- **Không chứng minh**: nhãn đúng. Một box lệch hay sai lớp vẫn có hash hợp lệ; hash chỉ nói "đây đúng là file đó", không nói "file đó đúng". Hash sai cũng không có nghĩa ảnh hỏng: ở lô 68007, manifest của ảnh `000000009590` ghi sha256 của ảnh `000000005037` (so khớp với hash tự tính của cả lô), còn file `000000009590.jpg` vẫn giải mã được (640×427) và đúng nội dung (nhóm người ngồi ăn quanh bàn). Vì vậy giữ ảnh trong v2 và ghi hash thật vào `manifest.csv`, thay vì đưa vào rework.
- **Kiểm tra đóng gói từ kết quả thật:** v2 có 245 ảnh và 245 file nhãn, manifest gồm **490 file dữ liệu**, ZIP gồm **495 file**. SHA256 khớp file `.sha256`: `a7a360ce2f7664133cab6a4bf3a955c33458950f721a6f5ab2b7a796b218a85b`. ZIP không lỗi CRC; CSV/README dùng UTF-8 và xuống dòng LF. Các con số khớp README và nhãn thực tế.
- **Kiểm tra bàn giao sau đóng gói:** chạy script gốc `check_handover.py --run runs/r68007`: **17 PASS, 0 FAIL**. H3 đã PASS nhờ 3 dòng review thật được nhóm xác nhận. Kết quả đã export sang `submission/r68007/`; log ở `runs/tv3_checks/real_rerun/check_handover.txt`. PASS xác nhận định dạng và tính nhất quán, không có nghĩa đã review hết: còn 8 ứng viên đang chờ nên README v2 vẫn ghi **Hold**.

## 5. Truy vết
- Ticket báo lớp `truck` (seed 68007) ở scene_365 và scene_679; changelog: v1.3 bắt buộc gán box cho `truck` bị che / cắt mép, v1.2 cho phép bỏ qua.
- **tier_a**: ảnh trong scene_365, scene_679, thuộc job theo guideline cũ v1.2 (tra ở `jobs.csv`), có ≥ 1 box `truck` trong `labels/` → 2 ảnh.
- **tier_b**: các ảnh khác cùng điều kiện (job v1.2, có box `truck`) mà team AI chưa báo → 4 ảnh.
- **notify**: người gán + người kiểm của các job chứa ảnh tầng a và b → A04, A05, Q01, Q03.
- **Vì sao lấy guideline theo job, không theo ảnh**: guideline ghi ở từng ảnh có thể chính là lỗi `guideline_mismatch` (lô 68007 có 2 ảnh như vậy). Job là đơn vị giao việc: người gán làm cả job theo một bản guideline, nên bản ghi ở job mới phản ánh quy tắc thật đã áp dụng.
- `tools/trace_query.py` tự đọc lớp và cảnh từ changelog/ticket, không ghi cứng; chọn bản guideline mới nhất theo số phiên bản lớn nhất.

## 6. Bug hoặc điểm chưa rõ trong lab
- **Windows: `run_lab.py` lỗi `UnicodeEncodeError`** dù đã chạy `py -X utf8`: `run_lab.py` gọi `inject_release.py` bằng subprocess, tiến trình con không nhận chế độ UTF-8 nên lỗi khi in chữ có dấu (lô vẫn tạo ra nhưng bước ghi lineage R-021 bị bỏ). Cách tránh: đặt `$env:PYTHONUTF8 = "1"` trước khi chạy.
- **`download_public.py` tải lại từ đầu khi rớt mạng**: file `.part` mở chế độ `wb` nên mỗi lần thử lại mất phần đã tải (file panoptic ~820 MB). Nhóm phải tải tiếp bằng `curl -C -` rồi đặt vào `data_source/cache/`.
- Máy có hai bản Python (`py` 3.14 không có Pillow, `python` 3.12 có): công cụ xem ảnh phải chạy bằng `python`.
