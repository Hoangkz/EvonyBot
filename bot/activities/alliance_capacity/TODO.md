# alliance_capacity — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [x] [run.py:97](run.py#L97) (2s): `delay(bot, 2)` — không cần sửa
- [x] [run.py:99](run.py#L99) (3s): `delay(bot, 3)` — không cần sửa
