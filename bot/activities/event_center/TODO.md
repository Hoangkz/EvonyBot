# event_center — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [common.py](common.py)

- [x] [common.py:148](common.py#L148) (5s): `bot.tap(center[0] + dx, center[1] + dy, delay=5)` — đã đổi: delay 1s, chờ thêm 1s × 10, thấy thì chờ 3s
- [ ] [common.py:165](common.py#L165) (1s): `bot.back(delay=1)`
