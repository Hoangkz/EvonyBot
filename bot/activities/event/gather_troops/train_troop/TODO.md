# train_troop — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:168](run.py#L168) (1s): `bot.back(delay=1)`
- [ ] [run.py:175](run.py#L175) (1s): `bot.back(delay=1)`
- [x] [run.py:178](run.py#L178) (2s): `bot.tap(*pos, delay=2)` — đã đổi: tap_tab (1s, tối đa 10 lần chờ thêm)
- [ ] [run.py:346](run.py#L346) (1s): `bot.tap(*box, delay=1)`
