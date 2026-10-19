# Gold Levy — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~`test_flow.py`~~: đã có (`tests/daily_activities/gold_levy/test_flow.py`: open_task, Free Levy All, nút đã xám).
2. **Free Levy All bị khoá** khi Thành chính < 11 và VIP < 4 (chữ trong popup) → nút xám ngay từ đầu, flow hiện coi là hết free và đánh dấu xong mà không levy. Đề xuất: còn nút "Free Levy" (trái, xanh) thì bấm từng lần tới khi nút thành "Gems Levy"; nút trái là "Gems Levy" = hết free. Không bấm Gems Levy.
3. Nút vàng / xám Free Levy All khớp chéo 0,88, sát ngưỡng 0,9 → nên nhận "hết free" bằng nút trái (Free Levy / Gems Levy).
4. ~~"Levy Gold 5 time(s)"~~: không cần xử lý — bấm Free Levy All là chắc chắn xong nhiệm vụ, chỉ lưu ngày xong vào DB.

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:28](run.py#L28) (2s): `bot.tap(*pos, delay=2)`
