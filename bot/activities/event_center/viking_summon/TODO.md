# Viking Summon — việc cần làm

Cập nhật: 2026-10-22. Xong mục nào thì xoá mục đó.

## Cơ chế (người dùng cho biết)

- Viking Challenge xuất hiện 3 ngày trong Event Center → tab Activities.
- Bot triệu hồi boss Viking của mình cho cả liên minh đánh; mình chỉ gọi ra rồi tham gia (Join Boss) như người khác.
- 4 độ khó: Easy, Normal, Hard, Hell. UI chọn 1, mặc định **Hard** (`viking_level` trong settings; chỉ bật khi tích `viking_summon`).
- Boss bị hạ → hiện ngay nút Summon để gọi tiếp. Mỗi lần hạ boss, lần gọi sau tăng 1 level, tối đa 50 (game tự tăng, bot không chọn).
- Nút Summon dễ bị hành động khác đè mất (popup, thông báo…).

## Đã làm

- [x] UI: combobox độ khó cạnh checkbox Summon ([join_monster_war_tab.py](../../../../ui/tabs/join_monster_war_tab.py)).
- [x] Template icon dòng "Viking Challenge" trong tab Activities: [Images/EventCenter/Viking/icon.png](../../../../Images/EventCenter/Viking/icon.png) (khớp 1,00; dòng khác ≤ 0,52 → ngưỡng 0,8).

## Ảnh cần người dùng chụp (396x704, bỏ vào tests/event_center/viking_summon/screens/)

- [ ] Dòng Viking Challenge lúc sự kiện **đang chạy** (ảnh đã có chỉ là "Claiming Reward Countdown" — hết giai đoạn đánh) để phân biệt trạng thái.
- [ ] Màn trong Viking Challenge: 4 độ khó, hiện level hiện tại.
- [ ] Popup xác nhận Summon (nếu có).
- [ ] Màn lúc boss vừa bị hạ, có nút Summon.
- [ ] Màn level 50 (tối đa): Summon hiển thị thế nào (mờ / "Max" / mất nút).
- [ ] Màn khi Summon không dùng được (hết lượt / thiếu vật phẩm / hết sự kiện), nếu có.

## Câu hỏi cần xác nhận

- [ ] Summon có giới hạn lượt hoặc tốn vật phẩm không?
- [ ] Độ khó chọn một lần hay phải chọn lại mỗi lần Summon?
- [ ] Join boss Viking của mình dùng luồng Join Boss hiện tại, hay có đường tắt?

## Code

- [ ] Tạo `constants.py` (ICON, ngưỡng, vùng tìm, độ khó), `run.py`, `__init__.py`, `FLOW.md` trong thư mục này (không phải activity, giống `crazy_eggs`).
- [ ] `run.py`: dùng `event_center.common.run_task` đi tới icon Viking Challenge → chọn độ khó theo `viking_level` → Summon → xác nhận.
- [ ] Đọc level hiện tại (OCR hoặc ảnh); đạt 50 thì dừng summon.
- [ ] Nhận biết sự kiện hết hạn / đang ở "Claiming Reward" → bỏ qua, không lỗi.
- [ ] Summon lại sau khi boss bị hạ: nhớ trạng thái "Viking của mình đang sống" trong BotContext; kiểm tra khi quay lại; chưa thấy nút Summon thì thử lại vài lần (nút dễ bị che), Back popup lạ theo quy tắc popup ở màn thành.
- [ ] Nối vào worker (`bot/worker/tasks.py`, `bot_worker.py`): chỉ chạy khi `viking_summon` bật; thứ tự ưu tiên: Summon trước, rồi Join Boss Viking.
- [ ] Đưa `viking_level` từ settings vào nhiệm vụ.
- [ ] Log: `bot.record` cho sự kiện summon (độ khó, level), `bot.log` cho chi tiết (xem skill bot-logs).

## Test

- [ ] Flow test bằng ảnh thật (skill flow-test), trỏ ảnh ở thư mục test; chỉ chạy khi được yêu cầu.
- [ ] Test: level 50 dừng; sự kiện hết hạn bỏ qua; không thấy nút Summon thì thử lại rồi thôi.
- [ ] Chạy thật trên giả lập (ngoài test tự động) khi sự kiện đang diễn ra.
