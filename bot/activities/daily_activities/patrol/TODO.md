# Patrol — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (giống hệt King's Path, `patrol_rounds`, làm hết 10 lượt trong ngày). Đã chạy
   thật trên 21943 (2026-10-04, giao diện cũ): thẻ Patrol → Go → Tường thành (ảnh mẫu civ1) → 10 lượt Select All →
   Patrol → Refresh → Back về thành, ~2 phút. Còn: chạy thử trên máy giao diện mới; ~~`test_flow` phần sau Go~~ (đã có: `tests/daily_activities/patrol/test_flow.py` — đủ 10 lượt, đếm riêng với King's Path / hết Refresh, Patrol không xác nhận); nối vào
   `run.py` chung (xem [../TODO.md](../TODO.md)).
2. ~~`test_flow.py` + `screens/`~~: đã có (phần sau Go; phần mở nhiệm vụ / bấm Go chưa có ảnh dòng Patrol).
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.

## Chờ cố định cần xem (có nên đổi sang wait_for không?)

Chỗ chờ số giây viết cứng, không có vòng kiểm tra rồi thử lại. Xác nhận từng chỗ: cần `wait_for` thì sửa, không thì gạch.

### [run.py](run.py)

- [ ] [run.py:25](run.py#L25) (1s): `bot.back(delay=1)`

## Cần test (logic mới: lưu xong sớm + `daily_patrol_more`, bỏ `must_finish`)

- [ ] Chạy `tests/daily_activities/patrol/test_flow.py` (test mới `PatrolMoreFlow` chưa chạy lần nào, ảnh/bước `to_city` có thể cần chỉnh).
- [ ] Máy thật: sau lượt 1, `daily_patrol` đã vào DB ngay (ngắt giữa chừng bằng boss / hết 120 giây vẫn thấy xong).
- [ ] Máy thật: `daily_patrol_more` tìm thành → Tường thành → Patrol, đếm tiếp lượt (`daily_patrol_round_<n>`) tới 10 / hết Refresh, lưu `daily_patrol_more`.
- [ ] Ngắt giữa màn Patrol: nhiệm vụ kế tiếp có tự về màn thành sạch không.
- [ ] Task `daily_patrol_more` có bị bỏ qua đúng khi Daily Patrol chưa xong không (scheduler).
