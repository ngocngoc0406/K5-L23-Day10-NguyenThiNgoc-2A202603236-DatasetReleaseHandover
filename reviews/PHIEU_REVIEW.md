# Phiếu review: 14 ảnh còn lại

Mỗi người mở ảnh của mình, trả lời **một dòng: thấy gì + confirmed/rejected**, điền vào file csv (hoặc nhắn cho người tổng hợp).
Phần "Dữ liệu" trích từ nhãn (không phải kết luận): **kết luận là của người xem ảnh**.

> ⚠️ Mỗi ảnh mang nhiều nhất **một** lỗi. Ảnh đã có lỗi luật (đánh dấu ⚠️ bên dưới) thì ứng viên gán nhãn ở ảnh đó nhiều khả năng là hệ quả của lỗi luật; vẫn phải mở ảnh xem rồi mới kết luận.

---

## Quang: đề ẩn (`runs/de_an_review/quang/` → `reviews/review_quang.csv`)

| Ảnh | Dữ liệu | Câu hỏi |
|---|---|---|
| img_0019 swap | Cùng một vật (IoU 1.00): detection **cell phone**, panoptic **remote** | Vật trong vùng đó là **điện thoại** hay **điều khiển TV**? Điện thoại → panoptic sai → `category_swap`; điều khiển → detection sai → `class_swap` |
| img_0029 swap | Cùng một vật ở góc trên phải (x 443–499, y 0–66): detection **couch**, panoptic **chair** | Đó là **ghế sofa (couch)** hay **ghế đơn (chair)**? |
| img_0041 missing_box | Segment **knife** nhỏ (989 px, x 273–339, y 187–226), không có box nào ở đó | Có con dao nhìn rõ mà không có box không? Rõ → `confirmed`; quá nhỏ/bị che → `rejected` |

## Quang: 68007 (`runs/r68007_review/quang/` → `reviews/r68007/review_quang.csv`)

| Ảnh | Dữ liệu | Câu hỏi |
|---|---|---|
| 000000001353 bbox_drift | Box person #5 trùng vùng (IoU 0.92), chứa 100% pixel segment, chỉ 2/4 mép khớp | Box có **lệch khỏi người** (cắt đầu/chân, ôm nền thừa) không, hay chỉ rộng hơn một chút? |
| 000000001584 instance_merge | Vùng rất nhỏ (12×38 px) dưới đáy ảnh, 1 segment person phủ 2 box person | Ở đó có **2 người riêng** bị gộp thành 1 mask không, hay 1 người bị che? |
| 000000002923 instance_merge ⚠️ | Ảnh **đã có lỗi luật `duplicate_box`**; 2 box boat (#3, #6) gần như trùng nhau trên 1 segment boat | Ở đó có 2 chiếc thuyền hay **1 chiếc** (box bị lặp)? 1 chiếc → `rejected` (đã tính là duplicate_box) |

## Ngọc Mai: 68007 (`runs/r68007_review/mai/` → `reviews/r68007/review_mai.csv`)

| Ảnh | Dữ liệu | Câu hỏi |
|---|---|---|
| 000000003845 instance_merge ⚠️ | Ảnh **đã có lỗi luật `duplicate_box`**; 2 box carrot (#7, #9) gần trùng nhau trên 1 segment | Ở đó có 2 củ cà rốt hay **1 củ** (box lặp)? 1 củ → `rejected` |
| 000000006894 swap | Vật lớn bên phải (x 293–640): detection **person**, panoptic **bicycle**; có thêm box elephant chồng lên | Vật đó là **người** hay **xe đạp**? Người → panoptic sai → `category_swap`; xe đạp → `class_swap` |
| 000000008277 swap | Vật lớn (x 19–465): detection **cup**, panoptic **bowl**; có thêm 1 box bowl khác | Vật đó là **cốc (có quai, cao)** hay **bát (rộng, thấp)**? |
| *(sửa)* img_0065 đề ẩn | Ghi chú hiện chỉ chép dữ liệu | Ghi lại: con vật là gì, dấu hiệu nhìn thấy (bờm, sừng, đốm…) |

## Ngọc: đề ẩn (`runs/de_an_review/ngoc/` → `reviews/review_ngoc.csv`)

| Ảnh | Dữ liệu | Câu hỏi |
|---|---|---|
| img_0177 missing_box | Segment **laptop** lớn (55 284 px) gần cả ảnh; detection chỉ có box **cat** ở đó, không có box laptop | Có laptop thật không? Có → thiếu box → `confirmed` |
| img_0190 swap | Con vật ở mép trái (x 0–89): detection **cow**, panoptic **horse** (IoU 1.00) | Bò hay ngựa? Ngựa → `class_swap`; bò → `category_swap` |
| img_0214 missing_box | Segment **car** rất mỏng (488 px, y 187–210); 2 box car gần đó chồng ít (IoU 0.10, 0.18) | Có chiếc xe riêng nhìn rõ mà thiếu box, hay chỉ là mảnh xe bị che/xa? |

## Ngọc: 68007 (`runs/r68007_review/ngoc/` → `reviews/r68007/review_ngoc.csv`)

| Ảnh | Dữ liệu | Câu hỏi |
|---|---|---|
| 000000016249 missing_box ⚠️ | Ảnh **đã có lỗi luật `thing_overlap`**; quanh đó đã có 3 box bench | Có chiếc ghế dài nào **thật sự không có box** không? |
| 000000023781 instance_merge | 1 segment carrot khớp nhất box #3 (IoU 0.68), chồng thêm box #1, #5 | Mask có **gộp 2 củ riêng** thành 1 không? |

---

Điền xong: `py tools/finalize.py` → hết dòng "chưa review" là xong, rồi commit + push.
