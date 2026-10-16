# Alliance VIP — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

- [x] Chạy thật trên 21913: Monthly (nút xám -> đánh dấu xong), Daily (kéo xuống cuối -> giá -> popup -> + 5 lần -> mua -> đánh dấu).
- [ ] Chưa thử nhánh Monthly nút **xanh** (tài khoản có thẻ tháng): cần ảnh popup / kiểm tra nút giá xanh ở nhóm Monthly.
- [ ] Chưa có ảnh khi không đủ Alliance Points (nút giá chữ đỏ): hiện vẫn bấm, popup có thể không mua được -> popup còn mở thì Back, không lưu.
- [ ] `flow test` (tests/daily_activities/alliance_vip/) với ảnh Alliance Shop 1.png .. 3.png + popup (chưa viết).
- [ ] Tài khoản có VIP tối đa: sách VIP có thể biến mất khỏi shop (đã xử lý: tới Weekly Sale mà không thấy sách thì lưu xong).

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:142](run.py#L142) (1s): `bot.back(delay=1)`
- [ ] [run.py:149](run.py#L149) (1s): `bot.back(delay=1)`
- [ ] [run.py:213](run.py#L213) (1s): `bot.back(delay=1)`
