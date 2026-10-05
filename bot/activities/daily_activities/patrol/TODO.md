# Patrol — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~**Luồng mới sau Go**~~: đã có `after_go` (giống hệt King's Path, `patrol_rounds`, làm hết 10 lượt trong ngày). Đã chạy
   thật trên 21943 (2026-10-04, giao diện cũ): thẻ Patrol → Go → Tường thành (ảnh mẫu civ1) → 10 lượt Select All →
   Patrol → Refresh → Back về thành, ~2 phút. Còn: chạy thử trên máy giao diện mới; ~~`test_flow` phần sau Go~~ (đã có: `tests/daily_activities/patrol/test_flow.py` — đủ 10 lượt, đếm riêng với King's Path / hết Refresh, Patrol không xác nhận); nối vào
   `run.py` chung (xem [../TODO.md](../TODO.md)).
2. ~~`test_flow.py` + `screens/`~~: đã có (phần sau Go; phần mở nhiệm vụ / bấm Go chưa có ảnh dòng Patrol).
3. Ảnh `Done.png` (bản cũ: thẻ đã nhận, tích xanh "Completed"): người dùng chụp sau khi làm xong.
