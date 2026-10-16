# Resource Tax — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. Ảnh xong `TaxFinish2.png` là đúng nút "💎22" (giá lượt tiếp theo) → giá khác thì không khớp. Hiện thu xong đã `mark_daily_done` nên không thu lại, nhưng nên thay bằng dấu hiệu chắc hơn (VD dòng Activity hết Go).
2. Thử lại thật: Back sau khi thu (lần chạy 2026-10-04 một lần Back bị game bỏ qua; đã sửa thành Back tới khi màn Tax đóng).
3. **Thiếu kim cương** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log. (thu quá lượt free)

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:131](run.py#L131) (1s): `bot.back(delay=1)`
- [ ] [run.py:136](run.py#L136) (1s): `bot.back(delay=1)`
- [ ] [run.py:142](run.py#L142) (1s): `bot.back(delay=1)`
