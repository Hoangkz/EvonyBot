# Flow: Buy Daily (General: mua Stamina + Hammer)

Code: [run.py](run.py) (`buy_stamina`, `buy_all_hammers`). Hàm thực thi cả hai món: `run(bot, stamina_quantity, hammers)`; worker gọi thẳng `run` này (handler của `daily_buy_general` trong `bot/worker/priority.py`).

1. Ở màn chính, bấm góc trên bên phải (`FEATURES_BUTTON`), chờ 1s xem màn đã đổi chưa; chưa thì chờ thêm 1s, tối đa `OPEN_WAIT` (10) lần.
2. Stamina tới mốc 10 / 16 / 20 cái trong ngày (giá kim cương mỗi cái, `STAMINA_TIERS`: cái 1-10: 200, 11-16: 400, 17-19: 800, 20-22: 1600, 23-25: 3200, 26-31: 6400; chỉ mua tới cái 20, `stamina_price`). Chọn tab War,
   bấm Stamina -> popup số lượng. Giống Offering (`_buy_in_popup`), không mua lại cái đã mua hôm nay (kể cả mua tay):
   OCR số trên nút xanh (`read_cost`, số lượng 1) -> `stamina_done` ra các khả năng số cái đã mua -> bấm "+" lên
   `mốc - đã mua` cái, OCR lại để biết chính xác (dư thì bấm "-" lùi) -> bấm mua. Đã đủ mốc: đóng popup. Không đọc
   được Cost: không mua.
   Hammer: tab Special; nút giá Hammer xám ("Daily Limit: 0 / 10", `HammerSoldOut.png`, ngưỡng 0,97) = đã mua hết, bỏ qua. Không thì bấm giá Hammer -> popup (`bua.png`), chọn tối đa, xác nhận.
3. Màn lạ: Back / về thành (tối đa `MAX_STEPS` bước).

Đánh dấu "xong hôm nay" (nhiệm vụ tự lưu vào DB ngay khi mua xong từng món: `JOB["run"]` ở cuối [run.py](run.py)): mỗi món một dấu riêng,
`General: Stamina reached <mốc>` và `General: Hammer`. Chạy lại chỉ mua món / phần chưa mua: nâng mốc Stamina (10 -> 16)
thì popup tự tính phần còn lại; hạ mốc thì không mua.
