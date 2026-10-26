# Viking Summon — việc còn lại

Cập nhật: 2026-10-26. Flow hiện tại: [FLOW.md](FLOW.md). Xong mục nào thì xoá mục đó.

## Cần xác nhận / cần ảnh

- [ ] Nhãn độ khó đã chọn trên màn Summon chỉ có ảnh Easy ([LEVEL_LABEL](constants.py)); chụp thêm khi sự kiện sau chọn Normal / Hard / Hell để cảnh báo độ khó khác yêu cầu.
- [ ] Màn lúc boss vừa bị hạ (nút Summon hiện lại) và màn level 50 (tối đa): Summon hiển thị thế nào.
- [ ] Hết lượt / thiếu Viking Poleaxe (Summoning Cost 5): nút Summon hiển thị thế nào.
- [ ] Đường đi tới icon "Viking Challenge" trong tab Activities: chưa có ảnh thật trong test (đã chạy thật trên giả lập).
- [ ] Hộp thoại chia sẻ + Confirm của boss Viking: chưa có ảnh trong test (_share_boss được giả; đã chạy thật).

## Code

- [ ] Nối vào worker: dòng `viking_summon` trong priority.py + gỡ việc bỏ nhóm Join Monster War ở `build_tasks(...)` (bot_worker.py). Chưa làm vì người dùng không muốn sửa phần khác.
- [ ] Level 50: dừng summon (cần biết màn level 50).
- [ ] Log `bot.record` cho từng lần Summon / chia sẻ đã có; xem lại sau khi chạy thật cả ngày.
- [ ] Chạy thật qua worker (`poe dev`) cả cửa sổ thứ 2–5: Summon xen kẽ Join Boss.
