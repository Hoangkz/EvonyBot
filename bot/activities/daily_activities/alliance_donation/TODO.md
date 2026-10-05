# Alliance Donation — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới**~~: đã có `donate_free`, chạy theo giờ (ô chọn 0–4h). Đã chạy thật trên 21943 (2026-10-04, giao
   diện cũ): từ bảng Activity → Liên minh → Alliance Science → donate 13 lượt free → hết lượt → kiểm tra lưới
   Activity → thẻ "Completed" → xong. Còn: chạy thử trên máy giao diện mới (danh sách Activity, nút Claim / tích).
2. ~~`test_flow.py`~~: đã có (`tests/daily_activities/alliance_donation/test_flow.py`, giao diện cũ): đã xong từ
   trước, donate rồi xong, hết lượt free. Không bấm Go nên không cần ảnh popup
   thẻ. Còn thiếu nhánh giao diện mới.
3. ~~Ảnh `Done.png`~~: đã cắt từ máy 21943 (`tests/daily_activities/screens/31_old_grid_end_donation_completed.png`,
   thẻ (160, 544)); thẻ chưa xong <= 0,79 (ngưỡng 0,85).
4. ~~Không còn lượt free thì không kiểm tra Activity~~ → nhiệm vụ đã đủ từ trước không bao giờ được đánh dấu xong:
   đã sửa — kiểm tra Activity **trước** khi donate.
5. Lưu giờ thử (`TRIED_KEY`) ngay khi bắt đầu: không tới được Alliance Science cũng phải chờ đủ số giờ mới thử lại.
