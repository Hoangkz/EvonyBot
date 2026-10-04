# Troop Healing — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (Bệnh viện → Heal 150 → Finish All, giống King's Path). Còn: chạy thử
   thật trên máy; `test_flow` phần sau Go (có thể dùng ảnh `tests/event/kings_path/screens/heal_*`); nối vào
   `run.py` chung (xem [../TODO.md](../TODO.md)).
2. Không có lính bị thương / ít hơn 150 → hiện vẫn đánh dấu xong hôm nay dù dòng Activity chưa đủ (giống King's Path).
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
4. **Thiếu tài nguyên / hết tăng tốc** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
