# Flow: Super Value Weekly Card

1. Mở Valuable Event và tìm/chọn đúng tab Super Value Weekly Card bằng ảnh tên.
2. Tìm toàn bộ hộp quà phát sáng `Common/button_reward_chest` ở ngưỡng `0.80`;
   không thấy mới tap fallback `(45, 190)`.
3. Sau khi phần thưởng hiện, chỉ tìm và bấm các mẫu an toàn trong vùng xanh:
   `Claim`, `Claim All`, `Claimable`, `Daily Free`, `Free`. Không dùng `Go` hoặc
   `Continue` làm dấu hiệu DONE vì đó là trạng thái hàng chưa hoàn thành.
4. Mọi cú lướt dọc đều nằm trong vùng xanh `(4,59,96,99)`. Đưa danh sách về
   đầu rồi quét tới cuối; mỗi biên phải có hai cú lướt liên tiếp với khoảng cách
   dHash/Hamming không quá `24/576 bit`. Không dùng giới hạn số lần lướt cục bộ.
5. Chỉ DONE sau khi đã xác nhận biên cuối và không còn mẫu nút nhận nào trong
   vùng xanh; sau đó quay về màn thành.

Hộp quà là điều hướng, không phải thao tác nhận quà.
