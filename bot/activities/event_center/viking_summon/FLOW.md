# Viking Summon — flow

Không phải activity (giống `crazy_eggs`). **Chưa nối vào worker** (chưa có dòng trong priority.py; `JOB` trong [run.py](run.py) đã sẵn). Bật bằng ô tích Summon + chọn độ khó ở tab Join Monster War (`viking_summon`, `viking_level`, mặc định Hard).

## Lịch

- Chỉ chạy từ **giờ reset thứ 2 tới giờ reset thứ 5** (3 ngày, `in_window`; giờ reset do người dùng chọn ở màn Home; hiện game đã tăng lên 15:00, khớp countdown trong game: hết ~15:00 thứ 5).
- Trong cửa sổ: thử lại mỗi 10 phút (`INTERVAL_MINUTES`, lưu giờ thử vào DB `viking_summon_tried`). Boss bị hạ thì nút Summon hiện ngay nên lần thử kế tiếp gọi boss mới.
- Nối worker (chưa làm): thêm dòng `viking_summon` (group "Join Monster War") vào bảng priority.py; `build_tasks` đang bỏ nhóm Join Monster War nên cần gỡ chỗ đó ở bot_worker.py.

## Các bước ở màn Viking Challenge ([run.py](run.py))

Đi tới đây bằng `event_center.common.run_task` (màn chính -> Event Center -> tab Activities -> icon Viking Challenge). Không có toạ độ cố định: mọi nút tìm bằng ảnh trong [Images/EventCenter/Viking](../../../../Images/EventCenter/Viking).

1. **Màn chọn độ khó** ("Select Difficulty Level:") — chỉ hiện MỘT lần cho cả sự kiện; chọn rồi thì các lần sau vào thẳng màn Summon, không đổi được, sang event kế tiếp mới chọn lại. Tìm tên độ khó bằng ảnh (`level_*.png`), bấm huy hiệu ngay trên tên, bấm Confirm, chờ hộp thoại giữa màn (1 giây, tối đa 5 lần; không ra thì làm lại, tối đa 3 lần chọn).
2. **Hộp thoại "Select <Level> level?"** — chỉ Confirm khi chữ trong hộp đúng độ khó yêu cầu (`select_*.png`); sai thì Cancel rồi chọn lại.
3. **"Congratulations!"** (nhận Viking Poleaxe) — bấm vào chính popup; vẫn còn thì BACK.
4. **Màn Summon** ("Summoning Cost:" + nút Summon) — bấm Summon, game về bản đồ thế giới, boss Viking ở giữa màn.
5. **Chia sẻ liên minh** — chia sẻ như Find Boss (`_share_boss`: bấm boss -> Share -> liên minh -> Confirm, dùng lại `boss_scan.share_to_alliance`): tìm nhãn "Viking" (hình boss `bossIcon.png` gần giữa màn nhất, nhãn `bossName.png` gần hình đó); kiểm tra 1 giây mỗi lần, tối đa 3 lần; không thấy thì bấm giữa màn hình. Không đọc / ghi nhớ toạ độ boss, nên mỗi lần thấy boss còn sống (Go) là chia sẻ lại.
6. **Boss chưa bị hạ**: màn Viking hiện nút **Go** thay cho Summon -> bấm Go (về đúng vị trí boss) -> chia sẻ lại.

Độ khó đã khoá khác với yêu cầu (VD sự kiện đã chọn Easy, muốn Hell): chỉ ghi log, vẫn Summon. Hiện mới có ảnh nhãn độ khó trên màn Summon của Easy.

## Test

[tests/event_center/viking_summon/test_flow.py](../../../../tests/event_center/viking_summon/test_flow.py), ảnh thật chụp trên giả lập (độ khó Easy xác nhận thật; Normal / Hard / Hell chỉ chọn rồi Cancel ở hộp thoại). `_share_boss` được giả trong test.
