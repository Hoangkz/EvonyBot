# Join Monster War — trường hợp còn cần ảnh để test

Ảnh chụp **nguyên màn hình** giả lập (396×704), lưu vào `screens/`, rồi thêm test vào
`test_flow.py` / `test_boss_names.py` (xem skill `flow-test`).

## Danh sách boss

- [ ] **Lực có chữ số `0`**
  - VD: Pumpkin Monster 708.5K, Achelois 187.7M...
  - `8`, `K`, `B` đã có mẫu. Còn thiếu `0`, nên boss không có tier có lực chứa `0` sẽ không suy ra được cấp và bị bỏ qua.
  - Việc cần làm: thêm mẫu (`add_sample Power`), thêm thẻ vào `CARDS` trong `test_boss_names.py`.
- [ ] **Tier Legendary / Mythical / Excellent / Supreme / Grand**
  - Font `Name` đã có `E` hoa (Epic). Còn thiếu `L` hoa và `x`.
  - Không bắt buộc: bot vẫn nhận gần đúng được nhờ `?`.
  - Việc cần làm: thêm mẫu, thêm thẻ vào `CARDS`.

## Sau khi bấm Join

- [ ] **Hết vật phẩm thể lực: cần ảnh thật**
  - Hành vi đã chốt: màn Use Item không còn nút Use -> Back 2 lần, nhớ boss là đã tham gia, đánh dấu rảnh (không dừng Join Boss vì thể lực tự hồi).
  - Test `test_out_of_stamina_items_marks_joined_and_idles` đang dùng ảnh tổng hợp `stamina_after_use.png?no_items` (xoá cột nút Use). Cần ảnh thật của màn Use Item khi hết vật phẩm để thay.

## Đang dùng ảnh tổng hợp

- [ ] Các kịch bản dùng `W("...")` (ảnh gốc bị xoá dấu tích ô War): thay bằng ảnh chụp thật khi ô War đã bỏ tích.
  - Hiện chỉ có `war_list_long_name.png` và `war_epic_cerberus_skeleton.png` là ảnh thật ở trạng thái này.
