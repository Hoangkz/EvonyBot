# refine_equipment — việc còn lại

- [ ] **Đọc 4 dòng New** (`_judge` ở [run.py](run.py)): cần tên thuộc tính + màu chữ của từng dòng (trắng / xanh / tím / cam / vàng; Original có dòng tím). Cần ảnh chụp New
  với dòng cam / vàng và quyết định cách đọc tên (ảnh mẫu từng tên theo ô trang bị, hay đo bằng mẫu chữ như `ocr-samples`). Hiện luôn False.
- [ ] **Luật "đạt" và Lock**: mỗi dòng có màu tối thiểu riêng và cờ `lock`. Giả định: dòng ở Original đã đúng thuộc tính + màu thì khoá (nếu `lock`) để Refine không đổi nó; Refine tiếp tới khi mọi dòng đã chọn đều đúng thì Confirm.
  Chưa biết: bấm ổ khoá tốn thêm tài nguyên không, khoá tối đa mấy dòng, ảnh ổ khoá khoá / mở (đã thấy ổ mở ở Original), dòng New có bị khoá giữ nguyên không.
- [ ] **Bật `READY = True`** ([constants.py](constants.py)) khi hai mục trên xong; tới đó nhiệm vụ không vào danh sách của worker.
- [ ] **Hộp cảnh báo "unlocked high quality attribute(s)"** khi Refine mà dòng cao cấp đang khoá: King's Path xử lý bằng ảnh `warnLabel` / `warnConfirm`; activity này chưa xử lý.
- [ ] **Lần Refine đầu của trang bị chưa tinh luyện** (không có New): `_refine_until` coi là lần đầu và bấm tiếp; cần xác nhận trên trang bị thật chưa có dòng.
- [ ] **Hết nguyên liệu / vàng**: chưa biết màn báo; hiện `_refine_until` dừng khi không thấy nút Refine.
- [ ] **Nhãn tab loại tướng**: hammer = "Development", crown = "Duty" đã thấy; swords và tower chưa chụp tên (xem tab đang chọn giãn ra).
- [ ] Ô trống (không có trang bị): hộp thông tin không hiện, bot bỏ qua (chưa chụp màn ô trống để xác nhận).
- [ ] Danh mục thuộc tính của loại trang bị khác (cung / giáo / kiếm, mũ / giáp khác bộ) có khác danh mục đã chụp không.
- [ ] Tướng đầu tiên sau lọc có thể chưa mặc đủ 6 trang bị: hiện chỉ bỏ qua ô trống; có cần chọn tướng khác không.
