# Flow: Alliance Capacity

Port của C# `ScienceNew`. Code: [run.py](run.py), hằng số: [constants.py](constants.py).

## Flow

1. Màn chính → **Liên minh** → **Alliance Science** (kéo xuống tìm nếu chưa thấy).
2. **Donate**: giữ nút Donate 5 giây (lượt miễn phí); khi hết lượt free thì chi **gem** tối đa số lần ở ô **Times** của tab
   Alliance Capacity (`No` = không chi gem, một số = chừng đó lần, `ALL` = không giới hạn).
3. Hết lượt free (hộp mua gem) hoặc đủ số lần gem → thoát.

## Chỉ làm một lần, không lưu gì

- Dòng `alliance_capacity` trong [priority.py](../../worker/priority.py) có `once: True`: chạy **một lần mỗi lần bấm Start**, xong thì
  không đưa lại vào danh sách, kể cả khi sang ngày mới (muốn chạy lại thì Stop rồi Start).
- Làm xong **không lưu gì vào DB** (worker coi là xong khi hàm `run` chạy hết một lượt). Bị ngắt giữa chừng (hết 120 giây, có boss)
  thì chưa tính là xong, lượt sau làm lại từ đầu. Lỗi thật thì lưu `alliance_capacity_error` + một dòng History
  (`bot/activities/result.py` `save_errors`).

Test: [test_donate.py](../../../tests/alliance_capacity/test_donate.py); bảng nhiệm vụ: [test_scheduler.py](../../../tests/worker/test_scheduler.py).
