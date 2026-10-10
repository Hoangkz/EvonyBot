# Kiểm thử Join Monster War

Thư mục này bảo vệ luồng Join Boss ở ba tầng. Khi sửa logic, hãy chạy toàn bộ thư
mục thay vì chỉ chạy test vừa thêm:

```powershell
python -m unittest discover -s tests/join_monster_war -p "test_*.py" -v
```

## Hợp đồng hành vi bắt buộc

| Quy tắc | Test chính |
| --- | --- |
| Tọa độ OCR trên màn March là mục tiêu thật; không dùng tọa độ danh sách để quyết định hành quân | `test_march_target_flow.py::test_march_screen_coordinate_is_the_source_of_truth` |
| Không đọc được tọa độ March thì Back trước khi chọn quân hoặc March | `test_march_target_flow.py::test_unreadable_march_coordinate_backs_out_before_troop_or_march` |
| Chỉ thấy tab PvP War không đủ để coi là thành công | `test_march_target_flow.py::test_pvp_war_without_matching_joined_row_is_not_success` |
| Không có tọa độ mục tiêu thì không được xác nhận thành công dù đã về PvP War | `test_march_target_flow.py::test_pvp_war_without_a_readable_target_is_not_success` |
| Phải thấy hàng Joined có đúng tọa độ mục tiêu mới ghi BossMemory | `test_march_target_flow.py::test_matching_joined_row_marks_actual_march_coordinate` |
| Hàng Joined sai tọa độ không được xác nhận nhầm | `test_march_target_flow.py::test_wrong_joined_coordinates_do_not_confirm_success` |
| Sau khi dùng thể lực chỉ bấm March lại với tọa độ cũ, không OCR / chọn đội lại | `test_march_target_flow.py::test_stamina_refill_presses_march_again_without_ocr_or_troop_pick` |
| Runtime không giữ trạng thái `pending` | `test_march_target_flow.py::test_runtime_has_no_pending_target_state` |
| Card ở danh sách đọc lỗi tọa độ phải bị blacklist để tránh kẹt vòng lặp | `test_edge_cases.py::test_unreadable_card_coordinates_are_blacklisted_for_current_screen` |
| Card OCR lỗi không được cản bot xét card hợp lệ kế tiếp | `test_march_target_flow.py::test_unreadable_list_card_does_not_block_the_next_valid_card` |
| Card dịch chuyển trước cú tap phải được tìm lại theo tọa độ | `test_edge_cases.py::test_join_tracks_same_boss_when_new_rally_moves_its_card` |
| Card biến mất trước cú tap thì không report và không tap | `test_edge_cases.py::test_join_aborts_when_target_disappears_before_tap` |
| Luồng ảnh thật Home → Join → March → Joined phải lưu đúng tọa độ | `test_current_code_flow.py::test_live_main_flow_home_join_march_joined` |

## Vai trò từng file

- `test_march_target_flow.py`: hợp đồng an toàn của thiết kế hiện tại. Đây là file
  nên đọc đầu tiên khi sửa luồng Join/March.
- `test_current_code_flow.py`: regression bằng bộ ảnh chụp thật của flow hiện tại.
- `test_flow.py`: các kịch bản UI cũ và tổ hợp nhiều trạng thái/boss. Một số ảnh ở
  đây đến từ các phiên game khác nhau nên phần nhận diện danh tính March được cô lập
  bằng mock; không dùng file này thay cho kiểm chứng ảnh thật hiện tại.
- `test_edge_cases.py`: lỗi hiếm, timeout, popup, OCR hỏng và các nhánh an toàn.
- `test_boss_memory.py`: TTL, giới hạn bộ nhớ và trạng thái boss.
- `test_boss_names.py`: OCR tên/lực/cấp boss và bộ lọc lựa chọn.
- `TODO.md`: ảnh thật còn thiếu để thay thế dữ liệu tổng hợp hoặc tăng độ phủ OCR.

## Khi nào test xanh vẫn chưa đủ

Unit test không chứng minh được template sẽ khớp trên mọi độ phân giải, theme hoặc
trạng thái game. Khi thay ảnh trong `Images/`, cần bổ sung ảnh chụp nguyên màn hình
vào `screens/`, thêm một regression test không mock nhận diện liên quan, rồi test
thực tế trên MEmu trước khi phát hành.
