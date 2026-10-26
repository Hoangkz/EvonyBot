# Moment of Glory

1. Trong Event Center > Limited, tìm dòng `Moment of Glory` bằng crop tên ổn
   định và bấm đúng tâm ảnh, không dùng tọa độ cố định.
2. Chỉ tiếp tục khi nhận diện đúng title `Moment of Glory` trên trang đã mở.
3. Đưa vùng nhiệm vụ xanh `(1,40,99,97)` về biên đầu. Mỗi biên cần hai lần
   Hamming liên tiếp không quá `24` bit; không có giới hạn cứng số lần lướt.
4. Trong vùng xanh chỉ tìm và bấm nút có cả chữ `Claim` và dải xanh; không bấm
   `Go`. Chữ `Claim` khớp lồng trong `Claimed` xám bị loại bằng dải màu.
5. Sau lượt có nhận Claim, quay về đầu và quét lại. Chỉ DONE khi một lượt quét
   đầy đủ từ đầu tới cuối không tìm thấy Claim.
