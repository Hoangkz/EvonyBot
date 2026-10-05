# Troop Training — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (cấp I, ≥ 300 lính, Finish All), đã chạy thật bản cũ trên 21943 (cấp I,
   1 mẻ 13.101 lính, Finish All). `test_flow` phần sau Go đã có (ảnh `tests/event/kings_path/screens/train_*` +
   `gather_troops/ground_troop` dùng chung). Còn: chọn cấp lùi từng cấp 14 → 1 (13 lần bấm, chậm); nối vào `run.py`
   chung (xem [../TODO.md](../TODO.md)).
2. ~~Ảnh `Done.png`~~: đã có (21943, `tests/daily_activities/screens/28_old_grid_end_train_completed.png`; thẻ xong 1,00,
   thẻ chưa nhận / PvP Battle <= 0,73).
3. **Thiếu tài nguyên / hết tăng tốc** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
