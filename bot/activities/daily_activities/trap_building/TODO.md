# Trap Building — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. **Luồng mới sau Go** (`after_go`): cần ảnh người dùng gửi (menu công trình → màn chức năng → làm → xong), rồi nối vào `run.py` chung (xem [../TODO.md](../TODO.md)).
2. `test_flow.py` + `screens/` trong `tests/daily_activities/trap_building/`.
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
4. Ảnh thẻ bản cũ (`Card.png`) trên tài khoản khác chỉ khớp **0,88** (sát ngưỡng 0,85) → có thể cần thêm mẫu.
5. **Thiếu tài nguyên / hết tăng tốc** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
