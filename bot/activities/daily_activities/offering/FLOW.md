# Flow: Offering

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

1. Mở bảng Activity, tìm dòng Offer (`Title.png`), bấm Go ([../OPEN_TASK.md](../OPEN_TASK.md)). Dòng không còn Go → xong hôm nay (mục tiêu 0).
2. `after_go`: về thành, mở Đền thờ (Shrine, `open_building`), menu **Offer** (`Offer1.png`), màn Offer (`OfferGems.png`).
3. Số lần Offer Gems lấy từ ô "Offer Gems" của tab Daily Activities; 0 lần → bỏ qua, báo xong.
4. Bấm Offer Gems → popup (`PopupTitle.png`). OCR ô Cost (số lượng 1) để biết hôm nay đã offer mấy lượt, chỉ mua phần còn thiếu:
   đủ rồi → đóng popup, không mua; chưa đủ → bấm `+` tới số lượng cần, OCR lại Cost để kiểm tra, dư thì bấm `-`, rồi Offer.
   Không đọc được Cost thì không mua (tránh tốn kim cương).
5. Offer xong → báo xong hôm nay (mục tiêu = số lần đã chọn), Back `BACKS_AFTER_OFFER` lần về thành.
