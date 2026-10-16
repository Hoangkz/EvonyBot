# event — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [common.py](common.py)

- [ ] [common.py:217](common.py#L217) (1s): `bot.back(delay=1)`
- [ ] [common.py:219](common.py#L219) (2s): `bot.tap(*pos, delay=2)`
- [ ] [common.py:252](common.py#L252) (2s): `bot.tap(pos[0] + dx, pos[1] + dy, delay=2)`
- [ ] [common.py:253](common.py#L253) (1s): `bot.back(delay=1)`
- [ ] [common.py:257](common.py#L257) (2s): `bot.tap(*pos, delay=2)`
- [x] [common.py:268](common.py#L268) (5s): `bot.tap(*button, delay=5)` — đã đổi: delay 1s, chờ thêm 1s × 10 tìm chữ day(s), thấy thì chờ 3s
- [ ] [common.py:271](common.py#L271) (1s): `bot.back(delay=1)`
- [ ] [common.py:273](common.py#L273) (2s): `bot.tap(*pos, delay=2)`
- [ ] [common.py:322](common.py#L322) (1s): `bot.back(delay=1)`
- [ ] [common.py:522](common.py#L522) (1s): `bot.swipe_percent(*swipe, duration=0.5, delay=1)`

### [cycle.py](cycle.py)

- [ ] [cycle.py:147](cycle.py#L147) (1s): `bot.sleep(1)`
