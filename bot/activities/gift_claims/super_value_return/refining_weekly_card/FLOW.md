# Refining Weekly Card

- Chỉ tìm và lướt trong khung danh sách phần thưởng màu xanh (`x=2..98%`, `y=67..98%`).
- Chỉ bấm chữ `Claim` khi crop của nút có dải màu xanh; tìm tất cả Claim xanh
  trong từng khung nhìn.
- Đưa danh sách về biên đầu và lướt tới biên cuối; mỗi biên cần hai cú lướt
  liên tiếp không đổi, không dùng giới hạn cứng số lần lướt.
- Khi một lượt đầy đủ không còn Claim, lượt nhận hiện tại đã xong. Nếu toàn bộ
  trạng thái nhận diện được là `Continue` dải vàng thì trả `DONE` lâu dài.
- Nếu không còn Claim nhưng chưa thấy toàn bộ `Continue` dải vàng, trả
  `DONE_1`: không ghi DB và không mở lại trong cùng cửa sổ 120 giây; cửa sổ
  sau phải kiểm tra lại.
- Nếu `Claim` vẫn còn nhưng không bấm được, giữ `PENDING`; không đoán DONE.
