# Viking Summon — flow

Không phải activity (giống `crazy_eggs`). Đã nối vào worker: dòng `viking_summon` trong [priority.py](../../../worker/priority.py) (`JOB` trong [run.py](run.py)). Bật bằng ô tích Summon + chọn độ khó ở tab Join Monster War (`viking_summon`, `viking_level`, mặc định Hard).

## Lịch

- Chỉ chạy từ **giờ reset thứ 2 tới giờ reset thứ 5** (3 ngày, `in_window`; giờ reset do người dùng chọn ở màn Home; hiện game đã tăng lên 15:00, khớp countdown trong game: hết ~15:00 thứ 5).
- Điều kiện chạy (`summon_enabled`): tab Join Monster War có tích đánh boss **Viking** trong danh sách boss **và** tích **Summon**.
- Trong cửa sổ: kiểm tra boss Viking; xong lượt kiểm tra mới đếm 8 phút (`INTERVAL_MINUTES`; giờ kiểm tra xong lưu trong bộ nhớ của lượt chạy, **không lưu DB**: bấm Stop rồi Start là kiểm tra ngay) tới lần kế. Boss bị hạ thì nút Summon hiện ngay nên lần kiểm tra kế tiếp gọi boss mới và chia sẻ ngay.
- Boss còn sống (nút Go) đã chia sẻ rồi: kiểm tra lần 1-3 chỉ xem (không bấm Go); lần thứ 4 sau lần chia sẻ bấm Go rồi chia sẻ lại rồi đếm lại từ đầu (`SHARE_AFTER_CHECKS`; số lần đếm giữ trong bộ nhớ của lượt chạy, chưa chia sẻ lần nào thì chia sẻ ngay).
- Worker: `build_tasks` không còn bỏ nhóm Join Monster War (bot_worker.py), để dòng `viking_summon` của nhóm này vào danh sách nhiệm vụ.

## Các bước ở màn Viking Challenge ([run.py](run.py))

Đi tới đây bằng `event_center.common.run_task` (màn chính -> Event Center -> tab Activities -> icon Viking Challenge). Không có toạ độ cố định: mọi nút tìm bằng ảnh trong [Images/EventCenter/Viking](../../../../Images/EventCenter/Viking).

1. **Màn chọn độ khó** ("Select Difficulty Level:") — chỉ hiện MỘT lần cho cả sự kiện; chọn rồi thì các lần sau vào thẳng màn Summon, không đổi được, sang event kế tiếp mới chọn lại. Tìm tên độ khó bằng ảnh (`level_*.png`), bấm huy hiệu ngay trên tên, bấm Confirm, chờ hộp thoại giữa màn (1 giây, tối đa 5 lần; không ra thì làm lại, tối đa 3 lần chọn).
2. **Hộp thoại "Select <Level> level?"** — chỉ Confirm khi chữ trong hộp đúng độ khó yêu cầu (`select_*.png`); sai thì Cancel rồi chọn lại.
3. **"Congratulations!"** (nhận Viking Poleaxe) — bấm vào chính popup; vẫn còn thì BACK.
4. **Màn Summon** ("Summoning Cost:" + nút Summon) — bấm Summon, game về bản đồ thế giới, boss Viking ở giữa màn.
5. **Ask for Help rồi chia sẻ liên minh** — trước khi chia sẻ: nhãn boss đã "(Asking for help)" thì bỏ qua (mỗi lần nhờ tốn 1 Viking Poleaxe); chưa thì bấm boss -> Attack -> Ask for Help -> Confirm. Sau đó chia sẻ: — chia sẻ như Find Boss (`_share_boss`: bấm boss -> Share -> liên minh -> Confirm, dùng lại `boss_scan.share_to_alliance`): tìm nhãn "Viking" (hình boss `bossIcon.png` gần giữa màn nhất, nhãn `bossName.png` gần hình đó); mỗi lần chờ bản đồ đứng yên (camera trượt xong, như Find Boss) rồi mới tìm, tối đa 3 lần; không thấy thì bấm giữa màn hình. Không đọc / ghi nhớ toạ độ boss, nên mỗi lần thấy boss còn sống (Go) là chia sẻ lại.
   - Chờ về bản đồ: sau Summon / Go chờ thấy nút "•••" (qua màn trắng và sương nếu từ thành ra thế giới); thấy ảnh click thì bấm, ảnh exit thì Back, tới khi thấy "•••" lần đầu mới tìm boss.
   - Chia sẻ chưa được (VD bấm trượt vì camera chưa vào giữa boss): về bản đồ sạch, tìm lại boss rồi chia sẻ lại; không thấy boss thì quay lại màn Viking bấm Go (camera vào đúng boss) rồi chia sẻ tiếp. Tối đa 3 lần chia sẻ (`SHARE_TRIES`).
   - Nhiệm vụ `must_finish` (priority.py): phải chia sẻ xong mới thôi, không bị Join Boss, bong bóng... ngắt (chỉ Stop).
6. **Boss chưa bị hạ**: màn Viking hiện nút **Go** thay cho Summon -> chỉ ở lần kiểm tra thứ 4 sau lần chia sẻ trước: bấm Go (về đúng vị trí boss) -> chia sẻ lại.

Độ khó đã khoá khác với yêu cầu (VD sự kiện đã chọn Easy, muốn Hell): chỉ ghi log, vẫn Summon. Hiện mới có ảnh nhãn độ khó trên màn Summon của Easy.

## Test

[tests/event_center/viking_summon/test_flow.py](../../../../tests/event_center/viking_summon/test_flow.py), ảnh thật chụp trên giả lập (độ khó Easy xác nhận thật; Normal / Hard / Hell chỉ chọn rồi Cancel ở hộp thoại). `_share_boss` được giả trong test.
