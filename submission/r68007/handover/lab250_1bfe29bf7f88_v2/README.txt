Release: lab250_1bfe29bf7f88_v2
Parent: lab250_1bfe29bf7f88
Số ảnh: 245
Số nhãn: 1667
Guideline: v1.2 (J01-J03), v1.3 (J04-J10)
QC v1: 12/250 = 4.8%
Kết luận v1: Hold — 4.8% ảnh lỗi > ngưỡng 2%, không train tiếp trên v1
Kết luận v2: Hold — còn 8 ứng viên chờ review; đã tách 5 ảnh lỗi detection/thiếu file, chưa chốt để train
Ghi chú: Đã tách 5 ảnh lỗi nhãn detection/thiếu file sang rework_queue.csv, giao lại người gán/người kiểm của job (A01/Q02, A03/Q01). wrong_hash: đã mở ảnh kiểm, 1 ảnh còn nguyên nên giữ và ghi sha256 thật trong manifest.csv (000000009590). guideline_mismatch (2 ảnh): truyvet.csv ghi guideline theo job trong jobs.csv. scene_leak (scene_838): đưa cả cảnh về một split (split đa số của cảnh). Ảnh chỉ lỗi panoptic ở lại v2 vì nhãn detection vẫn đúng, báo team panoptic: 000000009772, 000000010707, 000000016249. v1 giữ nguyên, nhãn trong v2 không sửa tay. Còn 8 ứng viên chờ review; giữ v2 ở trạng thái Hold cho đến khi hoàn tất kiểm tra.
