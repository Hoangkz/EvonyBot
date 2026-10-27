# Active Monthly Card

Chọn tab, xác nhận trang bằng dòng `Purchase it to instantly get`, rồi chỉ tìm
hộp quà phát sáng `button_reward_chest_median` trong khung xanh
`(2,17,27,41)`. Ảnh median 40x40 được tạo từ 60 frame thật trên máy 21503:
điểm thấp nhất/trung vị/cao nhất là `0.7869/0.9569/0.9816`, còn nhiễu ngoài
khung cao nhất `0.2579`; dùng ngưỡng `0.72`.

Không dùng tọa độ fallback. Tọa độ cũ `(52,326)` nằm trên rương mua trả phí,
không phải rương phát sáng trong khung xanh.

Sau đó quét khung nhiệm vụ màu xanh `(4,59,96,99)`, tương đương khoảng
`x=16..380, y=415..697` trên ảnh 396x704. Cú lướt dọc nằm trong khung:
`(50,92) -> (50,65)`. dHash/Hamming chỉ lấy dữ liệu trong vùng xanh; hai lần
lướt liên tiếp có khoảng cách không quá `24/576 bit` mới xác nhận một biên.
Một lần có chuyển động sẽ đặt bộ đếm về 0 và không có giới hạn số lần lướt cục
bộ. Khi đã xác nhận cuối và không còn `Claim`, nhiệm vụ được coi là DONE. `Go`
và `Continue` không phải điều kiện DONE.
