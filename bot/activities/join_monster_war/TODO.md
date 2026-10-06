# Join Monster War — việc còn lại

Cập nhật: 2026-10-06. Toàn bộ 94 test trong `tests/join_monster_war` đều pass; các mục dưới đây là lỗ hổng mà test chưa
bắt được. Xong mục nào thì xoá mục đó. Ảnh còn thiếu để test: [tests/join_monster_war/TODO.md](../../../tests/join_monster_war/TODO.md).

## Lỗi

- [ ] **Kẹt vòng lặp khi OCR tọa độ thẻ thất bại** (`_join` → `_stable_join_target`)
  - `CAN_READ_COORDS` bật mà `_read_card_coords` trả `None`: `_stable_join_target` luôn ra `matches = []`, xoá
    `screen_blacklist`, trả `None` → `_join` trả `False`, không cuộn, không tăng `idle_scrolls`. Vòng sau lại gặp đúng
    nút đó → lặp mãi, không bao giờ rảnh / cuộn. Chỉ cần 1 thẻ luôn OCR lỗi là bot đứng yên.
  - Đã tái hiện bằng mock: gọi `_join` 5 lần liên tiếp đều `no tap`, blacklist `[]`, `idle_scrolls` 0.
  - Hướng sửa: khi `coords is None` thì đưa nút vào `screen_blacklist` (bỏ thẻ đó trên màn hiện tại) thay vì xoá
    blacklist; thêm test trong `test_edge_cases.py`.

- [ ] **Join → Back lặp mãi trên cùng một boss khi tọa độ March lệch tọa độ thẻ** (`_march_target_matches`)
  - Tọa độ thẻ và tọa độ màn March được OCR ở hai chỗ khác nhau. Nếu một bên đọc sai 1 chữ số (hoặc March không đọc
    được) thì mỗi lần đều Back, boss không vào `BossMemory`, và `idle_scrolls` bị reset về 0 mỗi lần tap Join → bot
    Join/Back mãi boss đó, không rảnh.
  - Hướng sửa: đếm số lần lệch theo tọa độ thẻ trong lượt chạy; quá N lần (VD 2) thì blacklist thẻ đó trên màn hiện tại
    / tạm bỏ qua một lúc. Không ghi `JOINED`.

## Cần cân nhắc

- [ ] **Điều kiện thành công sau March yếu hơn trước**: chỉ cần thấy tab PvP War là ghi `JOINED`. Nếu game từ chối
  March (thông báo / popup khác) mà vẫn quay về danh sách thì boss bị nhớ nhầm là đã tham gia và bị bỏ qua tới khi
  `BossMemory` hết hạn. Cân nhắc kiểm tra thêm thẻ có tọa độ đó đã chuyển sang "Joined" (chỉ OCR thẻ Joined khi cần).
- [ ] **`_stable_join_target` gán `screen_blacklist = [point]`** (nhánh thời gian chuyển đỏ / boss không đúng loại):
  mất các nút đã blacklist trước đó trên màn này → vòng sau OCR lại tên/cấp của các thẻ đã loại. Không sai kết quả
  nhưng tốn thời gian OCR; nên `append` thay vì gán.
- [ ] Chú thích bước 6 trong `_join` ghi "kiểm tra thêm một ảnh ngay trước cú tap" nhưng `_stable_join_target` chỉ chụp
  **một** ảnh mới; phần còn lại dựa vào kiểm tra tọa độ ở màn March. Sửa chú thích cho khớp code.

## Test

- [ ] Flow test cũ (`test_flow.py`) mock `_march_target_matches` = True vì bộ ảnh ghép từ nhiều lượt chơi. Đã chạy thử
  `_read_march_target_coords` trên mọi ảnh March thật trong `screens/`: đọc được hết (VD `march_ready.png` → (664, 899),
  `07_march_before_action.png` → (767, 811)). Nên thêm test cố định các kết quả này.
- [ ] Thêm kịch bản chọn **tướng chính** trong tab Development (`CHOOSE_MAIN_DEVELOPMENT`): ô chính trống → "+" → búa
  → Select → March. Hiện chỉ có `CHOOSE_ASSISTANT_DEVELOPMENT`.
- [ ] Test cho 2 lỗi ở trên (OCR thẻ lỗi không kẹt; tọa độ March lệch nhiều lần thì bỏ qua thẻ).

## Tài liệu

- [ ] `FLOW.md` mục "Chọn tướng: `_select_general()`" mô tả hàm cũ không còn trong `run.py` (đã thay bằng
  `_choose_general`) → xoá mục đó.
