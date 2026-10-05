# Black Market (activity) — việc còn lại

Danh mục vật phẩm: [items.json](items.json) (ảnh icon `Images/Black Market/Items/`). Tab UI:
[ui/tabs/black_market_tab.py](../../../ui/tabs/black_market_tab.py) — dựng từ items.json.

1. ~~**Viết lại vòng mua**~~ / ~~**mở Chợ ở mọi chỗ trong thành**~~: xong ([run.py](run.py), bản đồ thành
   [city_map.py](city_map.py), luồng: [FLOW.md](FLOW.md)). Còn: **ảnh mẫu** Học viện (21943), War Hall,
   Embassy, Nhà kho, Prison (người dùng bổ sung) để quét ghi được đủ công trình; chạy thử cả `_market` qua Gold Levy
   (Go thật) + lưu DB trong app.
2. **Gói vàng**: tạm **không mua** (người dùng sẽ thêm sau nếu cần). Đã loại: icon Gold 50k / 100k khớp gói vàng mọi
   mức (10k / 5k ở bm_screen_2: 0,93) -> bỏ ô, kể cả khi chữ số lượng khớp. Muốn mua: thêm ô tích + bỏ GOLD_PACK_IDS.
3. **Danh mục tài khoản thường**: items.json thống kê từ 21913 (VIP); tài khoản thường món trả vàng nhiều hơn (giá
   100.000 .. ~1.700.000), cần chạy lại thống kê để thêm icon / món còn thiếu.
4. ~~`FLOW.md` + flow test~~: [FLOW.md](FLOW.md), `tests/black_market/test_flow.py` (8 test).
