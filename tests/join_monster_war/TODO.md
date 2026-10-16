# Join Monster War — trường hợp còn cần ảnh để test

Ảnh chụp **nguyên màn hình** giả lập (396×704), lưu vào `screens/`, rồi thêm test vào
`test_flow.py` / `test_boss_names.py` (xem skill `flow-test`).

## Danh sách boss

- [ ] **Lực có chữ số `0`**
  - VD: Pumpkin Monster 708.5K, Achelois 187.7M...
  - Đã thêm mẫu `0_2.png` (từ "250.5M", Screenshot_20261013-035556): đọc ra 250500000. Mới có 2 mẫu `0` (1 mẫu cũ).
  - Còn lại: thêm thẻ lực có `0` vào `CARDS` trong `test_boss_names.py` (cần ảnh thẻ có nút Join đúng cỡ bot cắt), thêm mẫu `0` từ các thẻ khác nếu đọc sai.
- [x] **Tier Legendary**: đã có mẫu `L` hoa, `ry` (`war_legendary_cerberus_bayar.png`).
- [ ] **Tier Mythical / Excellent / Supreme / Grand**
  - Font `Name` còn thiếu `x` và có thể thêm vài chữ khác.
  - Không bắt buộc: bot vẫn nhận gần đúng được nhờ `?`.
  - Việc cần làm: thêm mẫu, thêm thẻ vào `CARDS`.

## Sau khi bấm Join

- [ ] **Hết vật phẩm thể lực: cần ảnh thật**
  - Hành vi đã chốt: màn Use Item không còn nút Use (chỉ còn vật phẩm kim cương) -> Back 3 lần, **không** ghi boss là đã tham gia (để thử lại khi thể lực hồi), đánh dấu rảnh (không dừng Join Boss vì thể lực tự hồi).
  - Test `test_out_of_stamina_items_does_not_mark_joined` dùng ảnh thật `screens/stamina_no_items.png` (màn Use Item chỉ còn vật phẩm kim cương).

## Đang dùng ảnh tổng hợp

- [ ] Các kịch bản dùng `W("...")` (ảnh gốc bị xoá dấu tích ô War): thay bằng ảnh chụp thật khi ô War đã bỏ tích.
  - Hiện chỉ có `war_list_long_name.png`, `war_epic_cerberus_skeleton.png` và `war_legendary_cerberus_bayar.png` là ảnh thật ở trạng thái này.
