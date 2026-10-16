# common — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [bubble.py](bubble.py)

- [ ] [bubble.py:106](bubble.py#L106) (1s): `delay(bot, 1)`

### [go_home.py](go_home.py)

- [ ] [go_home.py:36](go_home.py#L36) (1s): `delay(bot, 1)`
- [ ] [go_home.py:48](go_home.py#L48) (10s): `delay(bot, 10)`
- [ ] [go_home.py:52](go_home.py#L52) (10s): `delay(bot, 10)`
- [ ] [go_home.py:56](go_home.py#L56) (1s): `bot.tap(*cancel, delay=1)`
- [ ] [go_home.py:62](go_home.py#L62) (1s): `bot.tap_percent(x, y, delay=1)`
