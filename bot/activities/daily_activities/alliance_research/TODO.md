# TODO: Research technologies

## Chưa kiểm chứng trên máy thật
- [ ] Cuộn cây xuống và dừng sớm khi cây hết (`_scroll_tree`, so ảnh trước / sau khi vuốt, `TREE_END_DIFF`).
- [ ] Cả luồng qua 4 tab (Advancement → Defense → Military → Medical Aid) mà không có công nghệ nào nghiên cứu được
  → báo xong hôm nay (`_research_one` trả None). Mới thử riêng bấm tab và cuộn về đầu tab.
- [ ] Nhánh Học viện đang nghiên cứu sẵn (icon Speed Up trên menu) sau khi thêm bước Speedup Settings.
- [ ] Nhánh nghiên cứu xong ngay (nút Research ghi 00:00:00) sau khi đổi cách nhận kết quả sang đếm điểm ảnh đổi
  (`changed_pixels`, ngưỡng `CHANGED_PIXELS`).
- [ ] Popup Finish All còn hỏi Confirm ở lần tăng tốc đầu (chưa gặp trong luồng của bot; code vẫn xử lý).
- [ ] Ô tích "common speedups" đã tích sẵn khi vào popup Speedup Settings (mới thử lúc chưa tích).
- [ ] Nhãn chữ trắng (chưa mở khoá) chưa được nhận riêng: bot chỉ dựa vào việc không có nhãn xanh. Quy tắc "tất cả vàng
  + 1 trắng thì sang tab khác" chưa làm riêng, hiện chỉ cuộn tối đa 2 lần / dừng khi hết cây rồi sang tab.

## Chưa làm
- [ ] Flow test cả luồng từ Go (cần ảnh dòng "Research technologies" ở danh sách Activity và ảnh thành lúc Học viện ở giữa).
- [ ] Ảnh dòng nhiệm vụ `Title.png` đang chép từ `ActivitiesSourceCollecting.png`; cắt lại từ danh sách thật nếu khớp kém.
- [ ] Màn Technology báo lỗi riêng khi thiếu tài nguyên hoặc hàng chờ nghiên cứu đầy: hiện chỉ nhận qua việc nút Research
  xám hoặc không đổi sau khi bấm.

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [x] [run.py:84](run.py#L84) (2s): `bot.tap(*pos, delay=2)` — đã đổi: delay=1, hai nhánh tự wait_for
- [ ] [run.py:132](run.py#L132) (1.5s): `bot.swipe_percent(*TREE_SWIPE, duration=0.6, delay=1.5)`
- [ ] [run.py:140](run.py#L140) (1s): `bot.tap(*pos, delay=1)`
- [ ] [run.py:148](run.py#L148) (1s): `bot.back(delay=1)`
- [ ] [run.py:173](run.py#L173) (2s): `bot.tap(*speed, delay=2)`
- [ ] [run.py:183](run.py#L183) (1.5s): `bot.tap(*finish, delay=1.5)`
- [ ] [run.py:201](run.py#L201) (1.5s): `bot.tap(*settings, delay=1.5)`
- [ ] [run.py:207](run.py#L207) (1s): `bot.tap(*unchecked, delay=1)`
