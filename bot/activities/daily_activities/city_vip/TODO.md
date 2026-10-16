# City VIP — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

- [x] Luật chạy: chỉ 0h–1h giờ máy tính, chỉ khi có route trong DB, không có ô tích, ưu tiên 650, lưu `City VIP: claimed` khi nhận được.
- [x] Flow nhận VIP (tường -> hộp quà -> Server Gift -> Claim All), chạy thật trên 21913 (route tạm dựng từ FIXED civ1, không lưu DB): bấm Claim All.
- [x] Lưu DB ngay khi bấm Claim All (người dùng chốt), không cần popup hay Back. Sau đó vẫn chờ 2 giây và Back một lần để về thành.
- [ ] Chạy lại cả flow trên máy thật sau các thay đổi gần nhất (ảnh hộp quà không nền, vùng tìm `GIFT_AREA`, lưu DB ngay khi bấm Claim All): lần chạy thật duy nhất là trên 21913 trước các thay đổi đó.
- [ ] Máy chưa có route trong DB thì nhiệm vụ không tự chạy: cần đo route civ3 (21933: `goto` tường không thấy mốc nào) hoặc để worker quét route khi rảnh.
- [ ] Kiểm tra ảnh hộp quà trên các civ khác (civ2, civ4..7), thấy không khớp thì cắt thêm ảnh trong `GiftBox/`.
- Không viết flow test cho nhiệm vụ này (người dùng chốt: không cần test).

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:75](run.py#L75) (1s): `bot.tap(*walls, delay=1)   # bấm lại đúng chỗ: menu đóng, thấy rõ hộp quà`
- [ ] [run.py:103](run.py#L103) (1s): `bot.back(delay=1)`
