# city_tax — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:118](run.py#L118) (1s): `bot.back(delay=1)`
- [ ] [run.py:155](run.py#L155) (1s): `bot.tap_percent(*CONGRATS_TAP, delay=1)`
