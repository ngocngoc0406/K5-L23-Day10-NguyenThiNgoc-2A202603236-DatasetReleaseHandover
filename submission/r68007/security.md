# Bảo mật khi làm việc

> Gắn với lô `lab250_1bfe29bf7f88` (seed 68007, 250 ảnh COCO) mà nhóm 68 vừa QC và bàn giao bản v2.

## 1. Ca USB: hết giờ, muốn chép lô về nhà làm tiếp
Không chép. Lô này có 250 ảnh kèm nhãn, metadata và tên người gán/người kiểm (A01–A05, Q01–Q03); USB dễ mất, không mã hoá và không ai kiểm soát được bản sao sau khi rời máy công ty. Gửi qua email cá nhân cũng là đưa dữ liệu ra hệ thống ngoài công ty (lưu trên server của bên thứ ba, không xoá được). Nhờ người khác làm hộ thì người đó không có quyền với job này và mình đã chuyển dữ liệu cho người ngoài phân quyền. Cách đúng: dừng ở checkpoint, ghi lại tiến độ (ví dụ: đã xong review 6/11 ứng viên của r68007) vào ticket, hôm sau làm tiếp trên máy công ty; nếu cần làm từ xa thì xin quyền VPN / máy ảo của công ty với người phụ trách.

## 2. Năm việc: được hay không
- **Mở job được giao trên máy công ty: được.** Đúng người, đúng quyền, đúng thiết bị (ví dụ job J01–J10 của lô này trên máy lab).
- **Chụp màn hình gửi người quen: không.** Ảnh chụp mang theo nội dung lô (ảnh, nhãn, tên người gán) ra ngoài mà không còn dấu vết kiểm soát; hỏi bài thì mô tả bằng lời, không kèm dữ liệu.
- **Chép lô ra USB: không.** Như ca 1: mất kiểm soát bản sao; chỉ làm khi có quy trình chuyển dữ liệu được phê duyệt.
- **Dán nhãn thật lên chatbot: không.** Dữ liệu bị gửi lên dịch vụ ngoài và có thể bị lưu lại. Ở lab này ảnh COCO là dữ liệu công khai nên được phép và nhóm ghi lại trong `prompts.md`; với dữ liệu thật của dự án thì không.
- **Đưa tài khoản CVAT cho đồng nghiệp: không.** Mất truy vết: lineage và `truyvet.csv` ghi ai gán, ai kiểm; dùng chung tài khoản thì không biết ai sửa nhãn nào, rework giao sai người. Đồng nghiệp cần quyền thì xin tài khoản riêng.

## 3. Ca khuôn mặt: thấy mặt người rõ trong lô, guideline yêu cầu làm mờ
Lô có ảnh mặt người nhìn rõ, ví dụ `000000004395` (người đàn ông áo sơ mi trắng, cà vạt sọc, mặt chiếm gần nửa khung hình) và `000000001296` (cô gái cầm điện thoại ốp Hello Kitty, mặt rõ chính diện). Kết luận: **Hold** các ảnh đó (không đưa vào bản phát hành cho đến khi xử lý xong) và **báo người phụ trách dữ liệu/bảo mật** kèm tên ảnh, ghi vào ticket. Không tự làm mờ hay tự xoá ảnh: làm mờ sai cách vẫn lộ mặt hoặc làm hỏng nhãn (box `person` lệch so với ảnh đã sửa), xoá ảnh làm mất truy vết và đổi số liệu lô mà không ai duyệt; quyết định xử lý dữ liệu cá nhân thuộc về người phụ trách, theo quy trình chung cho cả lô chứ không phải từng người tự làm.
