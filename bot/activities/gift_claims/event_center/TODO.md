# event_center — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:82](run.py#L82) (0.8s): `bot.back(delay=0.8)`
- [ ] [run.py:387](run.py#L387) (1.2s): `bot.tap_percent(x_percent, 11, delay=1.2)`
