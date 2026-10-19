# Offering — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. Thử thật khi hôm nay đã offer vài lượt; test bản cũ khi có ảnh thẻ Offer.
2. Offer Gems = 0 → worker bỏ qua nhiệm vụ (người dùng sửa ở worker).
3. **Thiếu kim cương** (làm sau): cần ảnh popup báo thiếu → đóng, bỏ qua, **không** đánh dấu xong, ghi log.

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:81](run.py#L81) (1s): `bot.tap(*button, delay=1)`
- [ ] [run.py:153](run.py#L153) (1s): `bot.back(delay=1)`
- [ ] [run.py:160](run.py#L160) (1s): `bot.tap(*close, delay=1)`
- [ ] [run.py:162](run.py#L162) (1s): `bot.back(delay=1)`
