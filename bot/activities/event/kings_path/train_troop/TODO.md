# train_troop — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:119](run.py#L119) (1s): `bot.back(delay=1)`
- [ ] [run.py:126](run.py#L126) (1s): `bot.back(delay=1)`
- [ ] [run.py:129](run.py#L129) (2s): `bot.tap(*pos, delay=2)`
