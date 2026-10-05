# Black Market (activity) — việc còn lại

Danh mục vật phẩm: [items.json](items.json) (ảnh icon `Images/Black Market/Items/`). Tab UI:
[ui/tabs/black_market_tab.py](../../../ui/tabs/black_market_tab.py) — dựng từ items.json.

1. **Viết lại vòng mua** ([market.py](market.py) vẫn là bản C# đọc cấu hình cũ `black_market_items` -> hiện không mua
   gì). Cấu hình mới: `check_gold`, `refresh`, `quantity_buy`, `resources`, `items` ({id: bool}).
   - Mở: về thành -> tìm Chợ trên **cả** màn hình (ảnh mẫu civ của `event/city_building`, kể cả ảnh tự học); không thấy
     thì kéo màn tìm tiếp -> menu "Black Market" -> màn Black Market.
   - Mua: chỉ món được tích (nhận theo icon trong items.json; `resources` = gói tài nguyên 4 loại lương thực / gỗ / đá /
     quặng, mọi mức `resource_packs` 10k .. 5M, nhận theo chữ số lượng `label_templates`).
   - Dừng: kim cương < 50 (luôn); vàng < 2.000.000 khi `check_gold`; đủ `refresh` lần Instant Refresh / đủ
     `quantity_buy` lần mua ("ALL" = không giới hạn). OCR số dư: `bot/ocr/read_balance` (read_gold / read_gems).
2. **Gói vàng** (Gold 50k / 100k): tạm **không mua** (người dùng sẽ thêm sau nếu cần). Ảnh chữ số lượng cũng khớp gói
   vàng (50k: 0,93) -> khi mua `resources` phải phân biệt loại tài nguyên để bỏ gói vàng.
3. **Danh mục tài khoản thường**: items.json thống kê từ 21913 (VIP); tài khoản thường món trả vàng nhiều hơn (giá
   100.000 .. ~1.700.000), cần chạy lại thống kê để thêm icon / món còn thiếu.
4. `FLOW.md` + flow test (`tests/black_market/`).
