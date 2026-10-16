# valuable_event — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:102](run.py#L102) (0.7s): `bot.back(delay=0.7)`
