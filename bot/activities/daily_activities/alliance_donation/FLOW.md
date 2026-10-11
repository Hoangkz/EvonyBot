# Flow: Alliance Donation

Nhiệm vụ Daily Activities **theo giờ**. Code: [run.py](run.py) (`donate_free`), hằng số: [constants.py](constants.py).
Phần dùng chung của Daily (nhận thưởng `collect_activity_rewards`): [../FLOW.md](../FLOW.md).

Tab UI: ô chọn giờ thay cho ô tích — **0 / 1h / 2h / 3h / 4h** (mặc định 4h, `INTERVAL_*`); 0 = không làm.

## Flow

1. **Liên minh**: màn chính → nút Liên minh → kéo xuống tìm **Alliance Science** (dùng lại `_open_science` của King's Path Donate,
   `event/kings_path/donate/alliance.py`).
2. **Donate**: bấm "Donate" thẻ khoa học trên cùng tới khi **hết lượt miễn phí** (nút thành kim cương). **Không mua lượt** bằng kim
   cương (hộp xác nhận kim cương → Back). Rồi Back đóng Alliance Science.
3. **Lưu vào DB**: donate được ít nhất 1 lần thì lưu giờ vừa donate (`daily_alliance_donation_tried` trong `daily_done`).
4. **Nhận thưởng**: ra danh sách nhiệm vụ Activity và nhận thưởng (`collect_activity_rewards`: Claim All + rương điểm). **Không**
   tìm dòng nhiệm vụ rồi bấm Go, cũng không mở bảng để kiểm tra dòng đã xong chưa.
5. Hết lượt free ngay khi vào (hoặc không tới được Alliance Science): Back, không nhận thưởng, chờ tới giờ kế tiếp.

## Khi nào donate lại

Không có "xong hôm nay": lượt free hồi theo thời gian nên mỗi N giờ lại donate. Worker (`bot/worker/bot_worker.py`) mỗi vòng lặp chỉ
so giờ đã lưu trong DB với số giờ trên tab: đã qua N giờ thì làm ngay, trước các nhiệm vụ trong danh sách; chưa tới thì thôi. Nhiệm
vụ khai báo bằng `hourly_job(...)` trong bảng [priority.py](../../../worker/priority.py); `hourly_job` (`../common.py`) cũng lưu giờ
sau mỗi lần chạy, kể cả khi hết lượt free (để không thử lại liên tục). Bị ngắt giữa chừng (hết 120 giây, boss) thì chưa lưu giờ,
lượt sau làm tiếp. Lỗi thì lưu `daily_alliance_donation_error` vào DB.

Test: [test_flow.py](../../../../tests/daily_activities/alliance_donation/test_flow.py).
