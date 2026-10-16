# gift_claims — việc còn lại

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [common.py](common.py)

- [ ] [common.py:152](common.py#L152) (2s): `bot.tap(pos[0], max(0, pos[1] - round(20 * screen.shape[1] / REFERENCE_WIDTH)), delay=2)`
- [ ] [common.py:171](common.py#L171) (1s): `bot.tap(launcher[0], max(0, launcher[1] - 20), delay=1)`
- [ ] [common.py:219](common.py#L219) (2s): `bot.tap_percent(52, row_pos[1] * 100 / screen.shape[0], delay=2)`
- [ ] [common.py:394](common.py#L394) (0.4s): `bot.sleep(0.4)`
- [ ] [common.py:400](common.py#L400) (1.5s): `bot.tap(*point, delay=1.5)`
- [ ] [common.py:442](common.py#L442) (0.8s): `bot.back(delay=0.8)`

### [lobby.py](lobby.py)

- [ ] [lobby.py:154](lobby.py#L154) (0.7s): `bot.sleep(0.7)`
- [ ] [lobby.py:181](lobby.py#L181) (1s): `bot.tap(*target, delay=1)`
