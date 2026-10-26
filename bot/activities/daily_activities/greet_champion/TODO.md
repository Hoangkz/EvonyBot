# TODO: Greet Champion

## Chưa kiểm chứng trên máy thật
- [ ] Chạy trọn `after_go` trên máy thật (`EVONY_TEST=greet`, xem `tests/real_run.py`): lần chạy trước khi sửa logic chỉ
      tới được màn Champion; ngày 2026-10-13 nhiệm vụ đã đủ 10/10 nên chưa chạy lại được. Chạy lại vào ngày sau.
- [x] Nút Greet khoá (ổ khoá + đếm ngược, ảnh Greet1/10 00:00:57): `Greet.png` khớp 0,55 (< 0,8), `GreetFull.png` 0,50
      (< 0,9), `Unlock.png` 0,37 -> bot coi là khoá, chỉ bấm giữa. Màn Champion có nền động (cảnh khác theo ngày) nên không cắt
      ảnh "khoá" riêng; chỉ cần nhận ra không phải Greet sáng.
- [ ] Bấm trái tim có ra thẳng màn Champion như bấm icon Champion không.
- [ ] Mũi tên đổi mỹ nữ bấm theo % cố định (94,50) / (5,50).

## Chưa làm
- [ ] Flow test từ Go (cần ảnh danh sách Activity + màn thành có trái tim + menu Keep + màn Champion các trạng thái;
      đã có ảnh Helen 0/10, Cleopatra / Coatlicue (Unlock), popup xác nhận, Helen 10/10 ở thư mục Screenshots của MEmu).

## Cần test (logic mới: lưu xong sau 5 lần chào + `daily_greet_champion_more`, bỏ `must_finish`)

- [ ] Viết flow test (chưa có `tests/daily_activities/greet_champion/`): đủ 5 lần → lưu `daily_greet_champion`; 10/10 / hết mỹ nữ → lưu `daily_greet_champion_more`; `more_done`.
- [ ] Máy thật: bot đếm lần chào bằng key `daily_greet_champion_greet_<n>` (đếm theo lần bấm Greet) có khớp số lần game tính không.
- [ ] Máy thật: bị ngắt giữa chừng, `daily_greet_champion_more` tìm thành → trái tim / Keep → Champion → chào tiếp tới 10/10.
- [ ] Ngắt giữa màn Champion: nhiệm vụ kế tiếp có tự về màn thành sạch không.
- [ ] `city_map.reach_building(KEEP)` trong `daily_greet_champion_more` (Keep đang thấy / có route → goto / chưa route → scan_city lưu DB → goto): chưa chạy, cần test thật.
