# refine_equipment — việc còn lại

## Còn mở

- [ ] **Chạy qua app thật (nút Start)**: mới gọi trực tiếp hàm `run` và `_refine_until`; chưa chạy 6 trang bị liền một mạch với mức dừng thật, chưa thử mức dừng có Orange / tổ hợp vàng + cam. Ứng dụng đang chạy (`main.py`) cần đóng và mở lại để nhận code mới.
- [x] **Giao diện** đã xem trên app thật (người dùng xác nhận xong).
- [ ] **Hộp thoại lạ**: đã gặp bất ngờ hai hộp (cảnh báo "unlocked high quality attribute(s)" và "The new attribute is higher than the old one"), đã xử lý. Hộp lạ khác: màn đứng yên mà không thấy nút Refine thì kiểm tra 2 lần rồi bấm Back một lần (`_stuck_popup`, theo yêu cầu người dùng); mới thử bằng ảnh thay thế, chưa gặp hộp lạ thật.
- [ ] **Màu vàng ít mẫu** (6 dòng có ảnh trên ~300 dòng): ngưỡng cam / vàng theo hue (11-12 / 24) mới đo trên ít mẫu. Game chỉ có 4 màu: trắng, tím, cam, vàng.
- [ ] **Chữ báo danh sách tướng trống**: đã biết hai chữ ("No favorite General" khi tích tim, "No General!" khi chưa tích tim, tab Duty); trường hợp tích tim + loại tướng cụ thể trống chưa thấy ảnh, nếu game hiện chữ khác thì bot không nhận ra và cứ bấm vào chỗ tướng đầu tiên tới hết 15 vòng.
- [ ] **Hết nguyên liệu / vàng**: chưa biết màn báo; hiện `_refine_until` dừng khi không thấy nút Refine sau 10 s.
- [ ] Lần chạy từng báo "general screen not reached" khi máy đang ở sẵn màn Refine của một trang bị khác: chưa tìm ra nguyên nhân.
- [ ] FLOW.md còn vài câu mô tả cũ ở phần đầu (trạng thái cũ) và chú thích GENERAL_TYPES trong constants.py còn một câu cũ nhắc "hammer = Development"; nội dung chi tiết đã đúng.

## Đã xong

- Về thành một lần ở đầu activity (từ màn Refine / màn tướng / danh sách đều về được, thử thật); giữa các trang bị chỉ Back về màn tướng.
- Dòng vàng không nhận ra tên: dừng trang bị đó, chuyển trang bị khác, không Cancel / Confirm (thử thật bằng dòng giả lập; kết quả New treo vẫn còn khi quay lại trang bị, bot đọc và xử lý như kết quả vừa ra, có test ảnh 31).

- Nhãn tab loại tướng đã đối chiếu với game (21913): All (mũ), Military (kiếm), Development (búa), Duty (vương miện), Subordinate City (tháp); vị trí bấm của từng tab đúng.

- Nhận ô trống bằng độ bão hòa màu: người dùng chỉ làm đồ khung đỏ / vàng trở lên (độ bão hòa 153 .. 214, ô trống 56 .. 65, ngưỡng 100) nên không còn lo đồ phẩm chất thấp bị nhận nhầm là trống.

- Danh mục thuộc tính theo VỊ TRÍ ô (Weapon, Armor, Boots, Helmet, Pants, Ring), không theo loại đồ: người dùng xác nhận cùng vị trí ô thì danh mục giống nhau (giáo / cung / kiếm ở ô Weapon dùng chung).

- Điều hướng ••• -> Generals -> lọc tim / loại tướng -> tướng đầu -> 6 ô trang bị -> màn Refine (chờ 1 s tối đa N lần, bấm lại khi không thấy); bỏ qua ô trống; dừng khi danh sách tướng trống.
- Nhận trạng thái màn Refine theo ổ khoá (mở / đóng / không có = chưa tinh luyện); cả 4 dòng khoá (từ đầu hoặc giữa vòng) thì bỏ qua trang bị.
- Đọc 4 dòng (tên + màu + loại % / Flat + khoá) bằng so khớp ảnh mẫu; khảo sát 312 dòng trên 6 trang bị, ảnh thật của người dùng cho 3 thuộc tính khó (March Speed to Monsters, Increases Construction Speed, Ore Gathering Speed); lỗi màu do ổ khoá vàng đã sửa.
- Luật dừng (đếm dòng thuộc yêu cầu theo màu tối thiểu + loại tăng; Max refines; Stop when), Lock, Confirm dòng mới rồi khoá, đọc kết quả ổn định (`_read_stable`), hộp cảnh báo high quality và hộp "giữ dòng cũ", lần Refine đầu của trang bị chưa tinh luyện.
- Test: `tests/refine_equipment` 29 test đạt (điều hướng, vòng Refine, hộp thoại, khoá, bộ đọc trên ảnh thật); tests/worker 70 test đạt.
