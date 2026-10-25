# Active Monthly Card

Chọn tab, xác nhận trang bằng dòng `Purchase it to instantly get`, rồi tìm hộp
quà phát sáng `Common/button_reward_chest` ở ngưỡng `0.80`. Chỉ khi không nhận
diện được hộp mới tap fallback `(52, 326)`, là tâm hộp quà trên ảnh tham chiếu
396 px.

Sau đó quét khung nhiệm vụ màu xanh từ trên xuống dưới. Cú lướt luôn nằm trong
khung (`50,92 -> 50,65`), bấm mọi `ActiveMonthlyCard/button_claim` nhìn thấy và
dừng khi phần ảnh trong khung không còn di chuyển. Khi đã lướt hết mà không còn
`Claim`, nhiệm vụ được coi là DONE. `Go` và `Continue` không còn là điều kiện
DONE vì chúng là trạng thái nhiệm vụ chưa đủ điều kiện nhận quà.
