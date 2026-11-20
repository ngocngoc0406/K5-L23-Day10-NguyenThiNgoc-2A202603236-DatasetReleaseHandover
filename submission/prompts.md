# Dùng AI

| # | Ai dùng | Công cụ | Prompt (tóm tắt) | AI sai ở đâu | Nhóm kiểm lại thế nào |
|---|---|---|---|---|---|
| 1 | Nguyễn Thị Ngọc (TV4) | Claude Code | "Viết khung validator chung (common.py, validate.py) và 4 luật metadata + panoptic (scene_leak, guideline_mismatch, invalid_category_id, thing_overlap) chỉ dùng thư viện chuẩn" | Lần chạy đầu trên Windows lỗi in tiếng Việt (do `run_lab.py` gọi script con không ở chế độ UTF-8), phải đặt `PYTHONUTF8=1` | Chạy trên r68007, r68104 và lô sạch: lô sạch 0 lỗi luật; tự đọc lại từng luật so với docs/DELIVERY.md mục 2 |
| 2 | Phạm Đức Mạnh | Codex | "Hỗ trợ phần TV3: review ảnh, ghi chú H1–H17, thử và dựng v2, lineage, đóng gói, export, báo cáo §3–§4 và commit/push phần đã sửa." | Kết luận AI cần đối chiếu ảnh và được nhóm xác nhận; CSV/README cần thống nhất xuống dòng LF để hash ổn định. PASS định dạng không đồng nghĩa đã review hết. | Nhóm xác nhận các review đã chốt, tách dữ liệu thử khỏi kết quả thật. Chạy lại seed 68007: 12 lỗi, QC 4,8%; v2 có 245 ảnh, 1.667 box, 5 ảnh rework; đạt 17 PASS/0 FAIL. Còn 8 ứng viên chờ review nên v2 Hold. |
