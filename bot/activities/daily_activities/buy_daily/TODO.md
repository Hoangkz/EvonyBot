# TODO: Buy Daily

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:107](run.py#L107) (1s): `bot.back(delay=1)`
- [ ] [run.py:154](run.py#L154) (5s): `bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)`
