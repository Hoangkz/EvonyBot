# Black Market — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (giống hệt King's Path, `buy_items`, 3 lần mua), đã chạy thật trên 21943
   và 21913 (bản mới, mua 3/3). Còn: nối vào `run.py` chung (xem [../TODO.md](../TODO.md)).
2. ~~`test_flow.py`~~: `tests/daily_activities/black_market/test_flow.py` (ảnh dùng chung, không có `screens/` riêng).
3. ~~Ảnh `Done.png`~~: đã cắt (76x64) từ lưới bản cũ máy 21943 — tự khớp 1,00, thẻ khác <= 0,62.
4. **Không đủ tiền**: ~~kiểm tra số dư~~ đã có (OCR vàng < 2.000.000 / kim cương < 50 → Back, dừng, không đánh dấu).
   Còn: popup báo thiếu của game (nếu giá một món lớn hơn số dư còn lại) — cần ảnh để đóng popup.
5. **UI tích chọn vật phẩm cần mua** (làm sau). Thống kê 21913 (2026-10-05, 61 bộ hàng = 366 ô, 60 lần refresh):
   ~72 loại; ~84 % ô trả kim cương, ~9 % trả tài nguyên, ~4 % trả vàng. Món trả **vàng** chỉ thấy các gói tài nguyên
   **5M** (lương thực / đá / quặng / gỗ) giá **1.763.000 vàng** (cùng gói đó có lúc bán 1.800 kim cương). Món trả
   tài nguyên: sách EXP 1000/500 (37.500 bạc / 7.000–14.000 quặng), 100 chip x2 (150.000 / 75.000 bạc), tăng tốc
   xây dựng / nghiên cứu (33.000 gỗ), VIP 60m (6.000 gỗ). Còn lại (trang bị, rương, VIP, EXP lớn, ngọc...) trả kim cương.
   Cần: ảnh mẫu từng món (cắt icon giữa ô, bỏ viền / số lượng), nhóm theo loại trên UI, bot chỉ mua món được tích.
   Đã có: nhận ra món trả vàng (`GOLD_PRICE`, vùng `GOLD_PRICE_AREA`).
   Lưu ý: 21913 là tài khoản VIP (ít món trả vàng). Tài khoản thường: món trả **vàng** nhiều hơn, chủ yếu mua bằng
   vàng, giá **100.000 .. 1.700.000** (cao nhất ~1,7 triệu). 