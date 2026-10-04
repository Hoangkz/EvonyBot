# Troop Healing — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (Bệnh viện → Heal 150 → Finish All, giống King's Path), đã chạy thật bản
   cũ trên 21943 (heal 150, Finish All; log "150 of ? troops": OCR không đọc được tổng số lính bị thương của dòng). Còn: `test_flow` phần sau Go (có thể dùng ảnh `tests/event/kings_path/screens/heal_*`); nối vào
   `run.py` chung (xem [../TODO.md](../TODO.md)).
2. Không có lính bị thương / ít hơn 150 → hiện vẫn đánh dấu xong hôm nay dù dòng Activity chưa đủ (giống King's Path).
3. ~~Ảnh `Done.png`~~: đã có (21943, `tests/daily_activities/screens/29_old_grid_end_heal_completed.png`; thẻ xong 1,00,
   màn khác <= 0,72).
4. **Thiếu tài nguyên / hết tăng tốc** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
