# Hướng dẫn Review nhãn ảnh cho 4 thành viên (Đề ẩn)

Hàng đợi review từ `submission/de_an/candidates.json` có **12 ứng viên**, được chia đều cho 4 thành viên:

---

## 1. Phân công xem ảnh

### 👤 TV1 — Nguyễn Mạnh Quang (`review_quang.csv` - Phần 1/4)
- **Ảnh 1 — `img_0019`** (type: `swap`): Detection ghi `cell phone`, Panoptic ghi `remote`.
- **Ảnh 2 — `img_0029`** (type: `swap`): Detection ghi `couch`, Panoptic ghi `chair`.
- **Ảnh 3 — `img_0041`** (type: `missing_box`): Segment `knife` (989 px) không có box detection.
> **Lệnh xuất ảnh review:**  
> `python tools/view.py delivery --candidates submission/de_an/candidates.json --part 1/4 --out review_quang_imgs`

---

### 👤 TV2 — Nguyễn Thị Ngọc Mai (`review_mai.csv` - Phần 2/4)
- **Ảnh 4 — `img_0056`** (type: `bbox_drift`): Box `truck` (IoU 0.75, 77% pixel segment trong box, 2/4 mép khớp).
- **Ảnh 5 — `img_0061`** (type: `bbox_drift`): Box `person` (IoU 0.63, 97% pixel segment trong box, 1/4 mép khớp).
- **Ảnh 6 — `img_0065`** (type: `swap`): Detection ghi `cow`, Panoptic ghi `horse`.
> **Lệnh xuất ảnh review:**  
> `python tools/view.py delivery --candidates submission/de_an/candidates.json --part 2/4 --out review_mai_imgs`

---

### 👤 TV3 — Phạm Đức Mạnh (`review_manh.csv` - Phần 3/4)
- **Ảnh 7 — `img_0108`** (type: `swap`): Detection ghi `laptop`, Panoptic ghi `tv`.
- **Ảnh 8 — `img_0126`** (type: `instance_merge`): 1 segment `bottle` phủ 2 box cùng lớp.
- **Ảnh 9 — `img_0136`** (type: `bbox_drift`): Box `skis` (IoU 0.59, 100% pixel segment trong box, 2/4 mép khớp).
> **Lệnh xuất ảnh review:**  
> `python tools/view.py delivery --candidates submission/de_an/candidates.json --part 3/4 --out review_manh_imgs`

---

### 👤 TV4 — Nguyễn Thị Ngọc (`review_ngoc.csv` - Phần 4/4)
- **Ảnh 10 — `img_0177`** (type: `missing_box`): Segment `laptop` (55284 px) không có box detection.
- **Ảnh 11 — `img_0190`** (type: `swap`): Detection ghi `cow`, Panoptic ghi `horse`.
- **Ảnh 12 — `img_0214`** (type: `missing_box`): Segment `car` (488 px) không có box detection.
> **Lệnh xuất ảnh review:**  
> `python tools/view.py delivery --candidates submission/de_an/candidates.json --part 4/4 --out review_ngoc_imgs`

---

## 2. Quy tắc điền file CSV

Mỗi người mở file `.csv` của mình (dùng Notepad, VSCode hoặc Excel) và điền:

| Cột | Giá trị bắt buộc | Quy định |
|---|---|---|
| `image` | Tên ảnh | Giữ nguyên (`img_xxxx`). |
| `type` | Loại lỗi | • Với các lỗi `bbox_drift`, `instance_merge`, `missing_box`: **giữ nguyên**.<br>• Với ứng viên `swap`: Nếu **confirmed**, phải đổi `swap` thành `class_swap` (nếu nhãn detection sai) hoặc `category_swap` (nếu nhãn panoptic sai). |
| `verdict` | Kết luận | Chỉ điền `confirmed` (nếu thật sự là lỗi) hoặc `rejected` (nếu là bình thường / lệch tự nhiên). |
| `note` | Ghi chú | **Phải từ 20 ký tự trở lên**, mô tả rõ mắt người nhìn thấy gì trong ảnh (đặc điểm vật thể, vị trí sai khác). |

### Ví dụ mẫu ghi chú hợp lệ:
- `mở ảnh kiểm tra: vật thể là điều khiển tivi từ xa (remote), nhãn detection ghi cell phone sai`
- `nhìn ảnh: segment con dao trên thớt rõ ràng nhưng thiếu bounding box detection`
- `box bao quanh người bị lệch mép dưới quá nhiều so với viền thực tế của cơ thể`
- `hai chai nước cạnh nhau bị panoptic gộp chung thành một segment mask duy nhất`

---

## 3. Lệnh ghép review sau khi cả nhóm hoàn thành

Ngọc Mai (TV2) nhận 4 file và chạy lệnh ghép:
```powershell
python tools/merge_reviews.py review_quang.csv review_mai.csv review_manh.csv review_ngoc.csv --out review_log.csv
```
Script sẽ tự động kiểm tra định dạng và báo lỗi nếu có dòng nào chưa điền hoặc ghi chú < 20 ký tự.
