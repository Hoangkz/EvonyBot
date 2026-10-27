# Flow: Golden Tree Rewards

Ảnh test: `tests/gift_claims/screens/valuable_event_golden_tree_rewards.png` (trang, chưa chọn quà) và
`valuable_event_golden_tree_rewards_popup.png` (popup Rewards, `Screenshot_20261025-223305`),
`valuable_event_golden_tree_rewards_coins_5.png` (5 xu, đã chọn vàng: số 1 và 5 trắng, 10 đỏ; `Screenshot_20261025-224503`),
`valuable_event_golden_tree_rewards_skip_unchecked.png` (ô Skip animation chưa tích, máy 21913).

1. Trong Valuable Event, tìm và mở tab `Golden Tree Rewards` bằng `tab_icon`.
2. Nếu **đồng thời** thấy giá của nút `5` và `10` màu đỏ thì DONE ngay; nút `1` không ảnh hưởng điều kiện này. Không bấm Skip, chọn quà hay dùng xu ở trạng thái này.
3. Nếu chưa thỏa điều kiện trên, ô `Skip animation` dưới bên phải chưa có dấu tích xanh thì bấm `(291, 573)` rồi xác minh lại. Không xác minh được thì giữ PENDING.
4. Ô quà mục tiêu bên trái còn dấu + (`slot_plus`) = chưa chọn quà:
   1. Bấm dấu +, mỗi 1s kiểm tra popup Rewards (`popup_title`, chữ "Click to select a reward!"), tối đa 5 lần.
   2. Bấm ô vàng 1M (`reward_gold`), nghỉ 1s, bấm `button_confirm`.
   3. Mỗi 1s kiểm tra đã về trang (thấy `page_header`) và hết dấu +, tối đa 5 lần.
   4. Bước nào chờ 5 lần không thấy (thiếu ô vàng / Confirm thì Back đóng popup) thì làm lại từ bước 4, tối đa 3 lượt.
5. Ba nút dưới cùng Shake Trunk (10) / Pest Control (5) / Water (1): số giá ở y ~91-93% ngay dưới icon nút (icon ~88%).
   Số đỏ = không đủ xu. Ưu tiên lớn xuống bé: bấm icon nút đầu tiên có số không đỏ, rồi mỗi 1s kiểm tra popup chữ
   "Congratulations!" (`Images/Event/congratulations.png`, ngưỡng 0.9) đã ra chưa: nút 1 xu tối đa 3 lần,
   nút 5 / 10 tối đa 5 lần. Ra popup: Back đóng, chờ về trang (1s x 5, không về thì
   giữ PENDING). Không ra popup: thôi. Cả hai đều quay lại bước tìm số không đỏ, bấm tiếp cho tới khi cả 3 số đều đỏ
   (tối đa 30 lần mỗi lần chạy).
6. Nếu không đạt điều kiện DONE sớm ở bước 2, DONE khi đã chọn quà (không còn dấu +) và cả 3 số đều đỏ. Còn lại giữ PENDING.
