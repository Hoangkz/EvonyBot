# Hall of Historic Generals

1. Trong Super Value Return, chọn `Hall of Historic Generals/tab`.
2. Xác nhận `Challenge Quest`, bấm vào và chỉ tiếp tục khi thấy
   `How to Earn Scores`.
3. Quét dọc vùng xanh `(5,40,97,86)`. Cả hai biên cần hai cú lướt liên tiếp có
   dHash/Hamming không quá `24/576 bit`; không có giới hạn số lần lướt cục bộ.
4. Một nút chỉ được bấm khi vừa khớp chữ `Claim`, vừa có dải xanh HSV. Ảnh
   `Claimed` phải vừa khớp chữ đầy đủ, vừa có dải xám/độ bão hòa thấp.
5. Sau khi có thao tác nhận, phải quay lại biên đầu và quét đầy đủ tới biên cuối
   lần nữa. Chỉ khi lượt xác minh này không còn bất kỳ Claim xanh nào mới trả
   `DONE_1`. Sau đó Back về màn có `Challenge Quest`, dùng ảnh rương chung của
   Login Gifts với ngưỡng Hall `0.52` để nhận/kiểm tra hết rương trong vùng
   `(2,18,27,41)`, rồi mới chuyển sang nhiệm vụ khác. Một Claim vừa nhận không
   đủ để tạo `DONE_1`.
   `DONE_1` không ghi DONE vào DB và chỉ được kiểm tra lại ở lần chạy Claim
   Gifts tiếp theo.
6. Chỉ trả `DONE` khi một lượt quét đầy đủ không nhận thêm Claim, có các trạng
   thái Claimed hợp lệ và không thấy hàng `Go/Continue` chưa hoàn thành.
