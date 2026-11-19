# Dùng AI

| # | Ai dùng | Công cụ | Prompt (tóm tắt) | AI sai ở đâu | Nhóm kiểm lại thế nào |
|---|---|---|---|---|---|
| 1 | Nguyễn Thị Ngọc (TV4) | Claude Code | "Viết khung validator chung (common.py, validate.py) và 4 luật metadata + panoptic (scene_leak, guideline_mismatch, invalid_category_id, thing_overlap) chỉ dùng thư viện chuẩn" | Lần chạy đầu trên Windows lỗi in tiếng Việt (do `run_lab.py` gọi script con không ở chế độ UTF-8), phải đặt `PYTHONUTF8=1` | Chạy trên r68007, r68104 và lô sạch: lô sạch 0 lỗi luật; tự đọc lại từng luật so với docs/DELIVERY.md mục 2 |
