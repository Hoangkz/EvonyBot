# Active Monthly Card

Chọn tab, xác nhận trang bằng dòng `Purchase it to instantly get`, rồi tìm hộp
quà phát sáng `Common/button_reward_chest` ở ngưỡng `0.80`. Chỉ khi không nhận
diện được hộp mới tap fallback `(52, 326)`, là tâm hộp quà trên ảnh tham chiếu
396 px.

Sau đó quét khung nhiệm vụ màu xanh `(4,59,96,99)`, tương đương khoảng
`x=16..380, y=415..697` trên ảnh 396x704. Cú lướt dọc nằm trong khung:
`(50,92) -> (50,65)`. dHash/Hamming chỉ lấy dữ liệu trong vùng xanh; hai lần
lướt liên tiếp có khoảng cách không quá `24/576 bit` mới xác nhận một biên.
Một lần có chuyển động sẽ đặt bộ đếm về 0 và không có giới hạn số lần lướt cục
bộ. Khi đã xác nhận cuối và không còn `Claim`, nhiệm vụ được coi là DONE. `Go`
và `Continue` không phải điều kiện DONE.
