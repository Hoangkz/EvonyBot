# cultivate_generals — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:86](run.py#L86) (1s): `bot.back(delay=1)`
- [ ] [run.py:91](run.py#L91) (1s): `bot.tap(*cancel, delay=1)`
- [ ] [run.py:108](run.py#L108) (2s): `bot.tap(*pos, delay=2)`
- [ ] [run.py:110](run.py#L110) (1s): `bot.tap(*pos, delay=1)`
- [ ] [run.py:117](run.py#L117) (1s): `bot.tap_percent(*RECRUIT_DISMISS, delay=1)`
- [x] [run.py:127](run.py#L127) (3s): `bot.tap(*go, delay=3)` — đã đổi: chờ 2s, rồi 1s × tối đa 10 lần
- [ ] [run.py:193](run.py#L193) (1s): `bot.swipe_percent(*LIST_FLING, duration=LIST_FLING_DURATION, delay=1)`
