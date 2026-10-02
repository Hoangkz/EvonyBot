---
name: add-activity
description: Tạo một activity mới cho EvonyBot (bot/activities/<tên>/) và nối nó vào registry ACTIVITIES, tab cấu hình UI, nút Select Activity, cột database. Dùng khi người dùng muốn thêm activity/chức năng bot mới, port một hàm C# cũ sang, hoặc hỏi "thêm activity", "tạo tab mới", "new activity".
---

# Thêm activity mới

Một activity = một package trong `bot/activities/<snake_name>/` exposing `run(bot, settings)`.
Tên hiển thị (VD `"Open Gift Box"`) là **khóa chung** ở 5 nơi — phải viết y hệt nhau.

## 1. Package activity

Tạo 3 file, theo mẫu [bot/activities/open_gift_box/](../../../bot/activities/open_gift_box/) (mẫu đơn giản nhất) hoặc [alliance_capacity/](../../../bot/activities/alliance_capacity/):

`__init__.py`
```python
"""
<snake_name> — "<Display Name>" activity (port of C# <TênC#> nếu có).

- run.py:       entry point, `run(bot, settings)`, and its helpers
- constants.py: image folders, limits and action names
"""
from .run import run

__all__ = ["run"]
```

`constants.py` — thư mục ảnh (tương đối với `Images/`), ngưỡng, và **tên action** dạng chuỗi (`TAP = "tap"`, `BACK = "back"`, ...).

`run.py` — vòng lặp nhận diện màn hình chuẩn của project:
```python
from ...common import click_images, delay, exit_images, find_first, go_home
from .constants import ...

def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "<Display Name>" tab's config."""
    targets = _targets()
    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == DONE:
            return
        elif action == TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BACK:
            bot.back()
            delay(bot, 2)
        else:
            go_home(bot, screen)   # không nhận ra màn hình -> launcher/lỗi load/BACK

def _targets() -> list[tuple[str, str]]:
    return [
        # ảnh đặc trưng nhất / trạng thái kết thúc lên đầu
        (f"{FOLDER}/done.png", DONE),
        ...
        *[(path, BACK) for path in exit_images()],   # popup đóng bằng BACK
        *[(path, TAP) for path in click_images()],   # nút cứ thấy là bấm
        # ảnh điều hướng chung (menu chức năng, ...) xuống cuối
    ]
```

Quy tắc bắt buộc:
- **Chỉ thao tác qua `bot`** (`tap`, `tap_percent`, `swipe_percent`, `back`, `find`, `find_all`, `wait_for`, `tap_image`, `sleep`, `shell`). Mọi lời gọi này tự `check()` Stop / timeout / BossAvailable — **không** dùng `time.sleep`, không gọi `adbutils` trực tiếp, không bắt `BotInterrupted` hay `Exception` chung trong activity.
- Thứ tự `_targets()` quyết định ưu tiên khi màn hình khớp nhiều ảnh.
- Tap theo offset từ góc trên-trái: truyền `top_left={ACTION}` cho `find_first`.
- Giới hạn vùng tìm (nhanh + ít khớp nhầm): `regions={path: (x0, y0, x1, y1)}` theo % màn hình.
- `return` bình thường = activity hoàn thành (worker bỏ khỏi pending). Activity có thể bị cắt giữa chừng (timeout 120 s / boss mới) và được gọi lại **từ đầu** → phải chạy lại được từ bất kỳ màn hình nào.
- Việc làm 1 lần/ngày: dùng `bot.is_daily_done(task)` / `bot.mark_daily_done(task)`.
- Cần cấu hình tab khác: `bot.settings["<Tab Title>"]`.
- Comment/docstring: tiếng Anh hoặc tiếng Việt như code xung quanh; docstring module ghi rõ "port of C# ..." nếu là port.

## 2. Đăng ký

1. [bot/activities/__init__.py](../../../bot/activities/__init__.py): `from . import <snake_name>` và thêm `"<Display Name>": <snake_name>.run` vào `ACTIVITIES`.
2. [database.py](../../../database.py) `TAB_COLUMNS`: thêm `"<Display Name>": "<snake_name>"`.
   ⚠️ `_reset_old_layout()` **DROP toàn bộ bảng `devices`** khi thiếu bất kỳ cột nào trong `_JSON_COLUMNS` → người dùng đang cài bản cũ sẽ mất hết cấu hình khi update. Trước khi thêm cột, hỏi người dùng có chấp nhận không; nếu không, thêm migration chạy trước `_reset_old_layout` trong `Database.__init__`:
   ```python
   columns = {row["name"] for row in conn.execute("PRAGMA table_info(devices)")}
   for c in _JSON_COLUMNS:
       if columns and c not in columns:
           conn.execute(f"ALTER TABLE devices ADD COLUMN {c} TEXT NOT NULL DEFAULT '{{}}'")
   ```
3. Tab UI `ui/tabs/<snake_name>_tab.py`:
   - Port 1:1 từ C# designer → kế thừa `DesignerTab` với `DESIGNER_DATA`/`COMBO_ITEMS`/`PAGE_SIZE` (mẫu: [open_gift_box_tab.py](../../../ui/tabs/open_gift_box_tab.py)).
   - Tab mới tự thiết kế → kế thừa `BaseTab` + helper `LabeledCombo`/`CheckGroup`/`RadioGroup` trong [tab_placeholder.py](../../../ui/tabs/tab_placeholder.py).
   - Cài `get_settings() -> dict` và `set_settings(data)`; key của dict chính là key activity đọc qua `settings.get(...)`. Dict phải JSON-serializable.
4. [ui/tabs/__init__.py](../../../ui/tabs/__init__.py): import + `__all__`.
5. [ui/device_view.py](../../../ui/device_view.py): tạo instance và `self._add_tab(tab, "<Display Name>")` — title này là khóa settings.
6. [ui/tabs/initialization_tab.py](../../../ui/tabs/initialization_tab.py): thêm nút vào `DESIGNER_DATA` và `ACTIVITY_BUTTON_TARGETS` để chọn được activity.
7. File dữ liệu ngoài `Images/` (VD json) cần ship → thêm `Copy-Item` trong [installer/build.ps1](../../../installer/build.ps1).

## 3. Ảnh template

Đặt ảnh vào `Images/<Folder>/` — xem skill `template-images` để chụp/cắt/kiểm ngưỡng.

## 4. Flow test (bắt buộc)

Mỗi activity phải có `tests/<snake_name>/test_flow.py` kèm ảnh chụp flow chính trong `tests/<snake_name>/screens/`. Làm theo skill `flow-test` và thêm flow của activity vào `.claude/skills/flow-test/flows.md`.

## 5. Kiểm tra

```powershell
.\venv\Scripts\python.exe -c "import bot.activities as a; print(list(a.ACTIVITIES))"
.\venv\Scripts\python.exe -c "import ui.tabs"
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```
Sau đó chạy app (`venv\Scripts\poe dev`), chọn activity trên một giả lập và xem log `[serial] ...` trong terminal. Nếu activity có flow phức tạp, viết `FLOW.md` cạnh `run.py` giống [join_monster_war/FLOW.md](../../../bot/activities/join_monster_war/FLOW.md).
