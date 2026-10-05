# Flow: Alliance Donation

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.donate_free`, gọi từ `../run.py _run_donation`)

Tab UI: ô chọn giờ thay cho ô tích — **0 / 1h / 2h / 3h / 4h** (mặc định 4h, `INTERVAL_*`); 0 = không làm.

1. Chạy **cuối** Daily Activities (sau các nhiệm vụ được tích và nhận thưởng — không ưu tiên). Bỏ qua nếu đã xong
   hôm nay, hoặc chưa đủ số giờ kể từ lần thử trước (`TRIED_KEY` trong daily_done).
2. **Kiểm tra trước**: mở danh sách Activity, xem dòng "Donate to the Alliance" (`open_task(tap_go=False)`, không
   bấm Go). Hết Go (Claim / tích V / thẻ Completed) → đánh dấu xong hôm nay, thôi (không donate, không kiểm tra
   lại trong ngày).
3. Chưa xong → giống King's Path Donate khi không làm Patrol (`event/kings_path/donate/alliance.py`): màn chính →
   Liên minh → cuộn → **Alliance Science** → bấm "Donate" thẻ khoa học trên cùng tới khi **hết lượt miễn phí** (nút
   thành kim cương). **Không mua lượt** bằng kim cương (hộp xác nhận kim cương → Back). Không donate được lần nào
   → dừng, sang nhiệm vụ khác.
4. Có donate → Back, kiểm tra dòng Activity lần nữa: xong → đánh dấu xong hôm nay.
5. Vẫn chưa xong → `bot.again_after` = số giờ đã chọn: worker hẹn chạy lại Daily Activities sau chừng đó với độ ưu
   tiên thấp nhất (`bot/worker/scheduler.py` `AGAIN_PRIORITY`); lần sau các nhiệm vụ đã xong tự bỏ qua.

## Luồng cũ C# (`common.run_task` + `run.handle`, không còn được `../run.py` gọi)

1. Mở từ `ActivitiesDonateAlliance1.png`.
2. Khi thấy `AllianceCapacity.png`, crop từ hàng đó xuống 390 px.
3. Tìm nút `Donate.png` trong vùng crop và bấm.
4. Không tìm thấy Donate thì kết thúc pass hiện tại nhưng chưa ghi hoàn thành.
5. `AllianceDonateFinish.png` hoặc `AllianceDonateFinish1.png` báo hoàn thành.
