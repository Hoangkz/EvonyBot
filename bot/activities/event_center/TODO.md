# event_center — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [common.py](common.py)

- [ ] [common.py:148](common.py#L148) (5s): `bot.tap(center[0] + dx, center[1] + dy, delay=5)`
- [ ] [common.py:165](common.py#L165) (1s): `bot.back(delay=1)`
