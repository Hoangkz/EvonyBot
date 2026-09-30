# Join Monster War — trường hợp còn cần ảnh để test

Ảnh chụp **nguyên màn hình** giả lập (396×704), lưu vào `screens/`, rồi thêm test vào
`test_flow.py` / `test_boss_names.py` (xem skill `flow-test`).

## Danh sách boss

- [ ] **Lực có chữ số `0`**
  - VD: Warlord 85.6M không có, nhưng Pumpkin Monster 708.5K, Achelois 187.7M... thì có.
  - `8`, `K`, `B` đã có mẫu (từ `war_epic_cerberus_skeleton.png`). Còn thiếu `0`, nên boss không có tier có lực chứa `0` sẽ không suy ra được cấp và bị bỏ qua.
  - Việc cần làm: thêm mẫu (`add_sample Power`), thêm thẻ vào `CARDS` trong `test_boss_names.py`.
- [ ] **Tier Legendary / Mythical / Excellent / Supreme / Grand**
  - Font `Name` đã có `E` hoa (Epic). Còn thiếu `L` hoa và `x`.
  - Không bắt buộc: bot vẫn nhận gần đúng được nhờ `?`.
  - Việc cần làm: thêm mẫu, thêm thẻ vào `CARDS`.
- [x] **Đã cuộn tới cuối một danh sách dài** (`war_list_bottom.png`)
  - Thẻ cuối nằm sát nút Battle Logs, không có khoảng trống, nên bot không biết đã tới cuối.
  - Bot vẫn cuộn đủ vòng 3 xuống / 3 lên như bình thường (`test_bottom_of_long_list_keeps_scrolling`).

## Sau khi bấm Join

- [ ] **Màn March**
  - Cần ảnh lúc vừa mở, sau khi chọn quân (có `checkLocam.png`), và màn ngay sau khi bấm hành quân.
  - Kiểm tra: chọn đúng preset quân (`tap_pct(troop × 11, 11)`), bấm hành quân, và BossMemory ghi `JOINED` **chỉ khi** màn March đóng lại.
  - Kiểm tra thêm: các nhánh Back (không phải boss, không chọn được quân) không ghi gì.
- [ ] **Popup sau khi bấm Join**
  - Cần ảnh các popup: rally đã đầy, không đủ điều kiện, hết thể lực (`hettheluc.png`).
  - Kiểm tra: bot không kẹt, bỏ qua boss đó.
  - Kiểm tra thêm: `use_stamina = No` thì dừng hẳn (`end(None)`); `ALL` / `100` thì dùng vật phẩm thể lực.
- [ ] **Màn chọn tướng** (`selectGeneral.png`, `chooseDevelopment.png`, `chooseFavorite.png`, `Select.png`)
  - Kiểm tra nhánh `_select_general()`.

## Đang dùng ảnh tổng hợp

- [ ] Các kịch bản dùng `W("...")` (ảnh gốc bị xoá dấu tích ô War): thay bằng ảnh chụp thật khi ô War đã bỏ tích.
  - Hiện chỉ có `war_list_long_name.png` là ảnh thật ở trạng thái này.
