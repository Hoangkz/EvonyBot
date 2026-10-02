---
name: flow-test
description: Viết test flow chính cho từng activity của EvonyBot bằng chuỗi ảnh chụp màn hình thật đặt trong tests/<activity>/screens/ — thiết bị giả trả ảnh theo từng bước và kiểm tra bot bấm/back/vuốt đúng như kịch bản. Dùng khi tạo test cho activity, thêm/sửa activity (mỗi activity bắt buộc có flow test), cập nhật ảnh flow, hoặc người dùng nói "test flow", "test theo ảnh", "kịch bản test activity".
---

# Flow test theo ảnh chụp

**Quy tắc project:** mỗi activity trong `ACTIVITIES` phải có một flow test chạy lại flow chính của nó trên ảnh chụp màn hình thật, không cần giả lập. Sửa activity hoặc template mà làm flow test hỏng thì phải sửa code hoặc cập nhật kịch bản kèm ảnh, không được xoá test.

## Cấu trúc thư mục

```
tests/
  __init__.py
  flow.py                       # harness dùng chung (FlowDevice, Step, các action, run_flow)
  <activity_snake>/             # trùng tên package trong bot/activities/
    __init__.py
    screens/
      01_home.png               # ảnh chụp TOÀN màn hình, đánh số theo thứ tự flow
      02_menu.png
      ...
    test_flow.py
```

- Ảnh trong `screens/` là **ảnh chụp nguyên màn hình**, cùng độ phân giải với giả lập chạy bot, vì template khớp theo pixel. Các `REGIONS` của Join Boss được đo trên 396×704. Không cắt, không resize, không nén.
- Đặt tên `NN_<mô tả ngắn>.png`. Một ảnh có thể được nhiều bước dùng lại (VD màn hình "Joined" cuộn nhiều lần).
- Không để ảnh test trong `Images/`, vì thư mục đó được ship theo installer.
- Chụp bằng `probe.py shot` của skill `template-images`, lưu thẳng vào `tests/<activity>/screens/`. Mỗi bước trong kịch bản cần đúng một ảnh ở trạng thái mà bot sẽ thấy **ngay trước** thao tác của bước đó.

## Kịch bản: `test_flow.py`

```python
import unittest
from pathlib import Path

from bot.activities import open_gift_box
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"

FLOW = [
    Step("01_home.png",     tap("OpenBox/Setup/chucnang.png")),
    Step("02_menu.png",     tap("OpenBox/Setup/Items.png")),
    Step("03_box_list.png", tap("OpenBox/Boss/1.png")),
    Step("04_box.png",      tap("OpenBox/Setup/Use.png")),
    Step("05_quantity.png", tap("OpenBox/Setup/Max.png"), tap("OpenBox/Setup/Use2.png")),
    Step("06_list_end.png", end()),     # activity phải return khi đang ở màn hình này
]
SETTINGS = {"selection_gift_box": {"Gift Box Boss": True}}


class OpenGiftBoxFlow(unittest.TestCase):
    def test_main_flow(self):
        run_flow(self, open_gift_box.run, SCREENS, FLOW, SETTINGS)


if __name__ == "__main__":
    unittest.main()
```

Mỗi `Step(screen, *actions)` nghĩa là: khi thiết bị đang hiển thị `screen`, bot phải thực hiện **đúng các action này, đúng thứ tự**. Làm xong action cuối thì thiết bị chuyển sang ảnh của bước kế tiếp.

| Action | Pass khi |
| --- | --- |
| `tap("Folder/x.png")` | tap nằm trong khung của template đó trên ảnh hiện tại. Harness tự tìm template, nên không cần ghi toạ độ |
| `tap_at(x, y, tol=15)` | tap cách (x, y) không quá `tol` px, dùng cho toạ độ cứng như `bot.tap(300, 660)` |
| `tap_pct(x, y, count=1, tol=15)` | như `tap_at` nhưng theo %, dùng cho `bot.tap_percent` |
| `back(count=1)` | gửi KEYCODE_BACK |
| `swipe(x1, y1, x2, y2, tol=3)` | vuốt theo % màn hình, dùng cho `swipe_percent`. Nếu không truyền toạ độ thì chấp nhận mọi lần vuốt, kể cả long-press `swipe(x, y, x, y, 5.0)` |
| `shell("input text 500")` | lệnh shell chứa chuỗi này |
| `end(result=...)` | activity phải `return` ở bước này, và nếu có `result` thì giá trị trả về phải bằng nó (VD `IDLE`) |

- Bước cuối là `end()` với activity tự kết thúc.
- Với activity chạy vô hạn (Join Boss khi `exit_when_idle=False`, Auction House), bước cuối không có `end()`: làm xong bước cuối thì harness bật Stop, và test pass khi activity ném `StopRequested`.

## Harness `tests/flow.py`: hành vi bắt buộc

`run_flow(testcase, run, screens_dir, flow, settings, *, ctx_settings=None, daily_done=None)`:

1. **Bỏ qua khi thiếu ảnh**: có ảnh nào của `flow` không tồn tại thì `testcase.skipTest("thiếu ảnh: ...")` và liệt kê từng file. Nhờ vậy suite vẫn chạy được trong lúc chưa chụp đủ ảnh. Template được tham chiếu trong `tap(...)` mà không có trong `Images/` thì fail ngay.
2. **FlowDevice** thay cho adbutils device:
   - `screenshot()` trả `PIL.Image` của bước hiện tại. Có thể gọi bao nhiêu lần cũng được, ảnh chỉ đổi khi bước hiện tại đã xong.
   - `click / swipe / keyevent / shell` so với action đang chờ. Sai thì fail, message ghi tên ảnh, số bước, action mong đợi và action thực tế (kèm toạ độ).
   - `window_size()` lấy từ kích thước ảnh.
   - `shell("dumpsys window")` trả một dòng `mCurrentFocus` chứa `com.topgamesinc.evony`, để `go_home()` không tưởng đang ở launcher. Lệnh shell không nằm trong kịch bản thì bỏ qua, chỉ ghi lại.
3. **Đồng hồ giả**: patch `time.monotonic` và dùng một subclass `BotContext` có `sleep(s)` gọi `check()` rồi cộng `s` vào đồng hồ thay vì chờ thật. Mỗi `screenshot()` cộng thêm 0.05 s để các vòng `wait_gone` / `wait_for` luôn kết thúc. Nhờ vậy test chạy trong vài giây dù activity có `delay` dài.
4. **Chống kẹt**: đặt `deadline = số bước × 120` giây giả. Nếu gặp `TimedOut` thì fail với message "kẹt ở bước NN (<ảnh>)", kèm action `find_first` nhận ra trên ảnh đó nếu tìm được.
5. **Kết thúc**:
   - Activity return khi chưa tới bước `end()` thì fail ("return sớm ở bước NN").
   - Tới `end()` mà activity vẫn gửi thêm thao tác thì fail.
   - Còn action chưa thực hiện thì fail.
6. **Context**:
   - `ctx.settings = ctx_settings or {}`.
   - `is_daily_done` / `mark_daily_done` dùng một dict thật, khởi tạo từ `daily_done`.
   - `report_boss` ghi vào `device.reported` để test assert được.
7. `run_flow` trả về device để test assert thêm, VD `device.reported == [(951, 663)]`; `device.ctx` là BotContext đã dùng.
8. `setup=lambda ctx: ...` được gọi ngay trước khi chạy, trong đồng hồ giả, để nạp sẵn trạng thái (VD `ctx.boss_memory` đã nhớ một boss).
9. Trạng thái có hạn dùng `time.monotonic()` (VD BossMemory) phải assert trong `with device.fake_time():`. Ra ngoài đồng hồ giả, nó bị so với giờ thật và coi như đã hết hạn.
10. Ảnh biến thể: `Step("x.png?ten_bien_the", ...)` + `run_flow(..., variants={"ten_bien_the": fn})`, trong đó `fn(ảnh BGR) -> ảnh BGR`. Đây là **ảnh tổng hợp** cho trạng thái chưa có ảnh chụp thật (VD Join Boss: `war_off` xoá dấu tích ô War). Chỉ dùng khi phần bị sửa không liên quan tới điều đang test, và thay bằng ảnh thật khi có.

Không dùng pytest. **Chỉ chạy test của activity vừa sửa**; chạy toàn bộ chỉ khi người dùng yêu cầu (xem bảng trong skill
`test-bot`, mục "Chỉ chạy test của phần vừa sửa"):

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests/event_center -t . -v   # một activity / một thư mục
.\venv\Scripts\python.exe -m unittest tests.event_center.crazy_eggs.test_flow -v # một file
.\venv\Scripts\python.exe -m unittest discover -s tests -t . -v                # toàn bộ (~3 phút) — chỉ khi được yêu cầu
```

`-t .` để `from tests.flow import ...` import được.

## Quy trình viết flow test cho một activity

1. Đọc `run.py` / `constants.py` (và `FLOW.md` nếu có) của activity. Xác định **flow chính**, tức con đường thành công phổ biến nhất, từ màn hình chính game tới lúc activity return. Flow dự kiến của từng activity hiện có nằm ở [flows.md](flows.md).
2. Viết `FLOW` trước, chưa cần ảnh. Chạy test sẽ bị skip và in ra danh sách ảnh cần chụp. Gửi danh sách này cho người dùng.
3. Người dùng chụp từng màn hình trên giả lập (hoặc Claude chụp bằng `probe.py shot` nếu có thiết bị và người dùng cho phép).
4. Chạy test. Nếu fail, đọc ảnh bằng Read và dùng `probe.py match --image` để đo template:
   - Template không khớp ảnh thật thì sửa template hoặc threshold (skill `template-images`).
   - Kịch bản sai so với hành vi đúng thì sửa `FLOW`.
   - Code sai thì sửa code.

   Nói rõ với người dùng là đang sửa cái nào.
5. Có nhánh phụ quan trọng (hết thể lực, hết gems, popup rời liên minh...) thì thêm method `test_<nhánh>` với `FLOW` riêng, dùng lại ảnh đã có nếu được.
6. Thêm hoặc đổi activity thì cập nhật [flows.md](flows.md).
