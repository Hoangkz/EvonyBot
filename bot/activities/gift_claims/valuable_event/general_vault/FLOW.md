# Flow: General Vault

1. Tìm tab General Vault ở hàng tab Valuable Event bằng ảnh `ValuableEvent/GeneralVault/tab_icon`.
2. Mở tab (`zone.open_tab`): tab đã chọn sẵn thì không bấm tab; còn lại bấm chính giữa ô tab, chờ sang trang. Sang trang rồi
   bấm chỗ tiêu đề (x 50% y 5%), nghỉ 1s.
3. Tìm nút Daily Free (`button_daily_free_current`, `button_daily_free`, khớp từ 0.72) chỉ trong vùng y 18-50% màn:
   - Không thấy nút: đã nhận rồi, đánh dấu DONE.
   - Thấy nút: bấm vào giữa nút; cứ chờ 1s rồi tìm `Congratulations`, tối đa 5 lần. Thấy thì Back đóng popup, DONE.
   - 5 lần vẫn không thấy Congratulations: quay lại bước 3. Bước 3 bấm tối đa 2 lần; hết 2 lần vẫn chưa có Congratulations
     thì giữ PENDING (lượt sau thử lại).
4. Quay lại hàng tab làm event kế tiếp (chạy riêng qua `run` thì Back một lần nếu không nhận diện được tab).

Code: `run.py` `claim_daily_free` (gắn vào `ExactFlow(handler=...)`). Không bấm Packages hay control mua hàng.
