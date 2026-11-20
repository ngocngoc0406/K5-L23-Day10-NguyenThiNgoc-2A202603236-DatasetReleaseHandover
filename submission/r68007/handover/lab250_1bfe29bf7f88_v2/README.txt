Release: lab250_1bfe29bf7f88_v2
Parent: lab250_1bfe29bf7f88
Số ảnh: 244
Số nhãn: 1654
Guideline: v1.2 (J01-J03), v1.3 (J04-J10)
QC v1: 15/250 = 6.0%
Kết luận v1: Hold — 6.0% ảnh lỗi > ngưỡng 2%, không train tiếp trên v1
Kết luận v2: Release — đã tách 6 ảnh lỗi nhãn detection sang rework; sửa hash, guideline, split; còn 5 ảnh lỗi panoptic (detection đúng) đã báo team panoptic
Ghi chú: Đã tách 6 ảnh lỗi nhãn detection/thiếu file sang rework_queue.csv, giao lại người gán/người kiểm của job (A01/Q02, A03/Q01, A03/Q02). wrong_hash: đã mở ảnh kiểm, 1 ảnh còn nguyên nên giữ và ghi sha256 thật trong manifest.csv (000000009590). guideline_mismatch (2 ảnh): truyvet.csv ghi guideline theo job trong jobs.csv. scene_leak (scene_838): đưa cả cảnh về một split (split đa số của cảnh). Ảnh chỉ lỗi panoptic ở lại v2 vì nhãn detection vẫn đúng, báo team panoptic: 000000006894, 000000009772, 000000010707, 000000016249, 000000023781. v1 giữ nguyên, nhãn trong v2 không sửa tay.
