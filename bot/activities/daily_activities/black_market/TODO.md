# Black Market — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. **Luồng mới sau Go** (`after_go`): cần ảnh người dùng gửi (menu công trình → màn chức năng → làm → xong), rồi nối vào `run.py` chung (xem [../TODO.md](../TODO.md)).
2. `test_flow.py` + `screens/` trong `tests/daily_activities/black_market/`.
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
4. **Không đủ tiền** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
