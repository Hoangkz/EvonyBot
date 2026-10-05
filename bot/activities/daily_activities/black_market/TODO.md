# Black Market — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (giống hệt King's Path, `buy_items`, 5 lần mua). Còn: chạy thử thật
   trên máy; `test_flow` phần sau Go (dùng ảnh `bm_*` của `tests/event/kings_path/screens/`); nối vào `run.py`
   chung (xem [../TODO.md](../TODO.md)).
2. `test_flow.py` + `screens/` trong `tests/daily_activities/black_market/`.
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
4. **Không đủ tiền** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.
