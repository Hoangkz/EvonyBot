# back_to_territory — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:102](run.py#L102) (0.7s): `bot.swipe_percent(50, 84, 50, 62, duration=0.45, delay=0.7)`
- [ ] [run.py:106](run.py#L106) (0.35s): `bot.swipe_percent(50, 62, 50, 84, duration=0.35, delay=0.35)`
