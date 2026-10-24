# Flow: Greet Champion

Nhiệm vụ Daily Activities "Greet the Champion 2 time(s)." (ô tích **Greet Champion** ở tab Daily Activities, ưu tiên
385). Ảnh / hằng số: [constants.py](constants.py), code: [run.py](run.py). Phần chung (mở Quests → Activity, tìm
dòng, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md).

Chào cho đủ **10/10** (không chỉ 2 lần). Cả nhiệm vụ không chờ giây nào, **trừ 3 s sau khi bấm mũi tên** đổi mỹ nữ.

```mermaid
flowchart TD
    A[Go -> về thành chính] --> B{Có trái tim trên đầu Keep?}
    B -->|có| C[Bấm thẳng vào trái tim]
    B -->|không| D["open_menu: bấm giữa Keep -> icon Champion"]
    C --> L
    D --> L
    L[Vòng lặp, mỗi vòng chụp màn hình] --> P{Popup Are you sure...?}
    P -->|có| P1[Tích Don't show again, Confirm] --> L
    P -->|không| T{Còn ở màn Champion?}
    T -->|không| X[Back về thành, không đánh dấu]
    T -->|có| F{Nút Greet đang thế nào?}
    F -->|"10/10 (nút đen)"| Z[Báo xong hôm nay, Back về thành]
    F -->|Unlock: mỹ nữ chưa mở khoá| G{Mũi tên phải còn vàng?}
    G -->|có| G1["Bấm phải, chờ 3 s"] --> L
    G -->|xám| G2{Mũi tên trái còn vàng?}
    G2 -->|có| G3["Bấm trái, chờ 3 s"] --> L
    G2 -->|xám cả hai| Z
    F -->|khoá: ổ khoá + đếm ngược| M[Bấm giữa màn 50%,50%] --> L
    F -->|sáng| H["Bấm Greet, rồi bấm giữa 10 lần"] --> L
```

- Chỉ khi thấy nút **Unlock** mới đổi mỹ nữ (phải trước, xám thì sang trái). Mũi tên còn bấm được màu vàng (độ bão hoà
  ~130-160), hết đường thì xám (~3).
- Greet 10/10: chữ vàng "10/10" cạnh "Greet" (`GreetFull.png`, `greet_full`). Chữ đè trong suốt lên nền mỹ nữ nên so màu đổi
  theo nền (mẫu cũ 0,72 trên Esmeralda; mẫu cắt trên Esmeralda chỉ 0,70 trên Helen) -> bot không nhận ra, chờ tới hết 600 s, không
  lưu xong, lần sau vào lại. Giờ so HÌNH chữ: mặt nạ điểm vàng của mẫu và của vùng `GREET_FULL_REGION`, ngưỡng 0,78. Đo: Esmeralda
  10/10 1,00 (có thông báo 0,96), Helen 10/10 0,875; Helen 2/10 0,60. Chạy thật 21913 (Helen 10/10): nhận ra sau ~9 s, lưu xong.
- Thông báo giữa màn "You cannot Empower anymore for today!" (`EmpowerLimit.png`): bấm giữa (vào mỹ nữ) đã hết lượt Empower.
  **Không** phải Greet 10/10 (chạy thật 21913: hiện cả lúc Greet 2/10 đang chờ hồi) -> chỉ thôi bấm giữa: Greet khoá thì chờ
  `LOCKED_WAIT` (1 s) rồi xét lại, Greet mở thì chào tiếp (vẫn bấm giữa `MIDDLE_TAPS` lần sau mỗi lần chào để đóng hoạt ảnh).
- `_leave`: Back một lần rồi chờ tới khi thấy "•••" (tối đa `SCREEN_WAIT`) mới Back tiếp. Trước đây thấy màn Champion vừa mất là
  Back thêm ngay, màn thành chưa vẽ xong "•••" -> Back ở màn thành sạch -> hỏi thoát game (gặp khi chạy thật 21913).
- Flow test: [tests/daily_activities/greet_champion/test_flow.py](../../../../tests/daily_activities/greet_champion/test_flow.py).
- Đủ `GREET_REQUIRED` = 2 lần chào (bot đếm `daily_greet_champion_greet_<n>` trong DB): **lưu ngay "xong hôm nay"** rồi chào tiếp tới 10/10 / hết mỹ nữ / bị ngắt; hai trường hợp đầu lưu thêm `daily_greet_champion_more`. Không còn `must_finish`.
- Việc nối tiếp `daily_greet_champion_more` (`run.MORE_JOB`, ưu tiên 385, không đi qua Go): bỏ qua khi Daily Greet chưa xong / đã lưu more / đủ 10 lần; chạy: về thành → tới Keep (`city_map.reach_building`: thấy Keep thì làm luôn; có route thì `goto`; chưa có route thì `scan_city` tìm và lưu DB rồi `goto`) → trái tim hoặc Keep → Champion → cùng vòng chào → lưu `daily_greet_champion_more`.
- Giới hạn cả nhiệm vụ `TASK_MAX_SECONDS` = 600 s (10 lần Greet ~ 10 phút).
- Giao diện Activity **bản cũ** (lưới thẻ): không làm nhiệm vụ này. Không có `Card.png` nên `open_task` trả TASK_UNKNOWN, bỏ qua, không đánh dấu.
- Keep là công trình cố định ở giữa thành (như Gold Levy) nên dùng chung `open_menu` + `KEEP`.
- Ảnh mẫu cắt từ ảnh chụp giả lập 396x704 (2026-10-13), thư mục `Images/DailyActivites/ActivitiesGreetChampion/`:
  `Title`, `Heart`, `Champion` (icon menu), `ChampionTitle`, `Greet`, `GreetFull`, `Unlock`, `DontShow`, `Confirm`.
- Back chỉ khi mất nút ••• (có popup); Back ở màn thành sạch = hỏi thoát game.
