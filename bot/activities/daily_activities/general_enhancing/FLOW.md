# Flow: General Enhancing

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Như Gather Troops Cultivate Generals (`event/gather_troops/cultivate_generals`, dùng lại ảnh / bước tới màn tướng),
nhưng **Gold Cultivate** (6000 vàng/lần, không tốn kim cương) thay Quick Cultivate x100, đúng **5 lần** (nhiệm vụ
"Cultivate Generals for 5 time(s)").

1. Go → danh sách **Generals**: tim lọc yêu thích chưa tích → bấm (ảnh Event, giao diện cũ chỉ 0,86 → ngưỡng 0,8);
   đã tích → kéo nhanh xuống cuối 6 lần → mở tướng cuối (10 %, 90 %).
2. Màn tướng: **Cultivate** → màn Cultivate (giao diện cũ: Gems Cultivate / Gold Cultivate + thanh Quick Cultivate).
3. Mỗi lần: **Gold Cultivate** → chờ kết quả (Cancel / Confirm, tối đa 5 s) → +1 → **Cancel** (bỏ kết quả như Event,
   không đổi chỉ số tướng).
4. Đủ 5 lần → Back 3 lần về thành, đánh dấu xong hôm nay.
5. Bấm Gold Cultivate mà không ra kết quả (thiếu vàng / game chậm) → không tính, dừng, không đánh dấu.
