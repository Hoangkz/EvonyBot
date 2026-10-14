# General Enhancing — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

0. **`after_go` hiện tại**: như Event Cultivate Generals tới màn Cultivate; phải ở tab Cultivate Once (đang ở Quick thì bấm sang); thấy Cancel thì bấm, thấy Gold Cultivate (`GoldCultivateNew.png`) thì bấm, chờ Cancel kết quả; đủ `GOLD_GOAL` = 5 lần thì Cancel rồi đánh dấu xong hôm nay. Còn: đọc số lần đã làm ở dòng nhiệm vụ; viết lại `tests/.../general_enhancing/test_flow.py` (còn là luồng giao diện cũ) với ảnh màn Cancel / Gold mới.
1. ~~**Luồng mới sau Go**~~ (luồng Gold Cultivate cũ, đã bỏ khỏi code): đã có `after_go` (Generals → tướng cuối → Cultivate → Gold Cultivate → Cancel × 5).
   Ảnh màn đã chụp trên 21943 (`tests/daily_activities/general_enhancing/screens/04..09`). Còn: chạy thử thật cả flow;
   ~~`test_flow`~~ (đã có: `tests/daily_activities/general_enhancing/test_flow.py` — 5 lần Gold Cultivate, không ra
   kết quả thì dừng); **giao diện mới** (màn tướng có tab Cultivate Once / Quick Cultivate — chưa biết nút Gold Cultivate
   ở đâu, ảnh `GoldCultivate.png` / `CultivateCancel.png` chỉ cắt từ giao diện cũ); nối vào `run.py` chung.
2. ~~`test_flow.py` + `screens/`~~: đã có (xem mục 1).
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
