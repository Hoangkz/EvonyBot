# Trap Building — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (Trap Factory → Build → bẫy đang hiện, đủ 150 theo số mặc định mỗi mẻ → Finish All).
   Còn: chạy thử thật trên máy (kiểm tra nút Build / "Training Speedup" của màn bẫy khớp ảnh của lính); nối vào `run.py` chung (xem [../TODO.md](../TODO.md)).
2. `test_flow.py` + `screens/` trong `tests/daily_activities/trap_building/`.
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
4. Ảnh thẻ bản cũ (`Card.png`) trên tài khoản khác chỉ khớp **0,88** (sát ngưỡng 0,85) → có thể cần thêm mẫu.
5. **Thiếu tài nguyên / hết tăng tốc** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
