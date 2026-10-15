# Flow: Black Market

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Giống hệt King's Path Black Market sau Go: dùng chung `event/kings_path/black_market/run.py`
(`open_black_market`, `buy_items`).

1. Go → về thành, **Chợ** ở giữa → menu → "Black Market" → màn Black Market.
2. Mỗi bước chụp 1 ảnh (6 món ở vị trí cố định):
   - vừa bấm một món mà hiện hộp "Are you sure you want to purchase ...?" → Confirm (+1 lần mua);
   - bỏ các món trả bằng **kim cương**; món còn mua được (nút giá xanh) → bấm, mỗi món 1 lần mỗi bộ hàng;
   - mua hết bộ → **Instant Refresh** (hết lượt miễn phí thì bằng kim cương, có hộp xác nhận thì Confirm) → chờ ô
     vật phẩm 1 đổi → mua tiếp bộ mới.
3. Đủ **3 lần mua** (`BUY_GOAL`) → Back, đánh dấu xong hôm nay. Luôn mua 3, không theo số trên dòng: nhiệm vụ có
   nhiều mốc ("for 1 time(s)" xong thì ra "for 3 time(s)", tối đa 3 lần) nên mua 3 luôn một lượt.
4. Mỗi bước đọc **số dư** (OCR `read_balance`, font `Images/OCR/Balance`): vàng < **2.000.000** (`GOLD_MIN`) hoặc kim
   cương < **50** (`GEMS_MIN`, giá một lần refresh trả phí) → Back, dừng. Đọc lỗi → bỏ qua kiểm tra.
5. Dừng giữa chừng (hết hàng / không thấy Instant Refresh / kẹt / thiếu vàng, kim cương) → không đánh dấu, lần sau
   thử lại từ 0.
