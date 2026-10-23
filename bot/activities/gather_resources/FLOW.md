# Gather Resources (thu thập tài nguyên)

Tab **Gather Resources** (ui/tabs/gather_resources_tab.py): nút **+ Add troop** thêm một dòng (tối đa `MAX_TROOP` = 6), mỗi dòng là
một đội ("Troop n" = dòng thứ n), chọn loại mỏ (Food, Wood, Stone, Iron, Gems) và cấp mỏ (Lv 15 → 1, mặc định 10). **Không chọn preset**:
ở màn March bấm March luôn với quân / tướng game chọn sẵn. Cấu hình (cột `gather_resources` của DB):
`{"squads": [{"resource": "food", "level": 10}, ...]}`.

## Điểm vào

- `run(bot, settings)` ở [run.py](run.py); dòng `gather_resources` trong [bot/worker/priority.py](../../worker/priority.py):
  `idle_only` (**cuối cùng**: chỉ khi hết mọi nhiệm vụ khác), `priority` 701 (trong các việc idle_only: trước Find Boss 700, vì chỉ tới
  lượt khi có đội đã về; Find Boss thì lúc nào rảnh cũng chạy).
- Việc theo giờ: `JOB.due` = có đội đã tới giờ rảnh (hoặc chưa gửi lần nào); `JOB.done` luôn False (không bao giờ "xong hôm nay").
  `JOB.enabled`: có ít nhất một dòng. tasks.py nhận `due` riêng của nhiệm vụ (dict `{"run", "enabled", "done", "due"}`).
- Giờ rảnh của đội n lưu trong daily_done: key `gather_resources_troop<n>_<epoch giây>` (mỗi đội giữ một key, gửi lại thì xoá key cũ).
- Lỗi thì `@save_errors(KEY)` lưu `gather_resources_error` vào DB.
- Một lần `run` gửi mọi đội đã tới giờ; trùng số đội ở tab thì lấy dòng đầu.

## Vòng lặp chính

```mermaid
flowchart TD
    A[run: các đội đã tới giờ] -->|không có| Z[return]
    A --> W{_to_world}
    W -- không ra được --> Z
    W --> S[mỗi đội: kính lúp -> bảng Search]
    S --> T[_pick_type: chữ loại mỏ, không thấy thì vuốt chậm về đầu / cuối hàng]
    T --> L[_set_level: đọc ô số, bấm + / − đúng chênh lệch, đọc lại]
    L --> C[ô Only search ... full resources chưa tích thì tích]
    C --> Q[Search]
    Q -- No matching targets --> F[đội chờ FAIL_WAIT 10 phút, sang đội kế]
    Q -- menu tròn mở --> O[chờ menu đứng yên, Occupy]
    Q -- menu chưa mở, thấy ảnh mỏ ở giữa --> M[bấm mỏ] --> O
    O -- "You cannot send more troops." --> MF[hết đường march: mọi đội đến hạn chờ 10 phút, return] --> Z
    O -- "You can only send one army to the target..." --> F
    O -- không sang màn March --> S2[làm lại cả lượt, tối đa SEND_TRIES = 2] --> F
    O -- màn March --> N{nút March xám?}
    N -- có: hết lính --> B[Back, mọi đội đến hạn chờ 30 phút, return] --> Z
    N --> P[đọc giờ thu thập + giờ đi, bấm March luôn]
    P -- vẫn ở màn March --> B2[Back] --> F
    P --> R[lưu giờ rảnh = bây giờ + thu thập + 2 × đi + 30 giây] --> S
```

- `_to_world`: thấy kính lúp / bảng Search = đang ở thế giới. Màn March còn mở (lượt trước bị ngắt) thì Back. Màn thành sạch ("•••", không
  hộp "thoát game") thì bấm quả địa cầu (92 %, 93 %). Màn khác: `go_home` (Back popup, Cancel hộp thoát game, mở game). Tối đa 8 bước.
  **Không bấm mù góc dưới phải** như `find_boss.to_world`: ở màn March đó là nút March (gửi quân nhầm), ở popup là vật phẩm.
- Chờ màn hình: `bot.wait_for` / `_wait_any` / `_wait_gone`, xem lại mỗi 1 giây, tối đa 8 lần (`WAIT_INTERVAL`, `WAIT_TRIES`).
- Sau khi bấm Search: chờ `SEARCH_SETTLE` 1 giây (menu / mỏ cũ còn trên màn), rồi chỉ chờ Occupy hoặc "No matching". Chờ đủ 8 lần mà
  menu không mở mới bấm vào ảnh mỏ ở giữa: bấm mỏ lúc menu đang tự mở thì menu đóng lại và Occupy trượt (đã gặp với Gems).
- Thông báo "No matching targets" chỉ hiện ~1,2 giây; lỡ thì Search lại (SEARCH_TRIES), kết quả cuối cùng như nhau (đội chờ 10 phút).

## Thứ tự nhận diện (Images/Gather/)

| Template | Dùng ở | Vùng (%) / ngưỡng | Ghi chú |
| --- | --- | --- | --- |
| `search.png` | kính lúp ở bản đồ thế giới | cả màn / 0.85 | thấy = đang ở thế giới |
| `OpenBox/Setup/chucnang.png` | nút "•••" màn thành | cả màn / 0.85 | vẫn khớp 0.98 khi hộp thoát game phủ mờ: kiểm tra hộp trước |
| `searchButton.png` | nút Search của bảng | PANEL (0,78,100,100) / 0.85 | thấy = bảng Search đang mở |
| `type_<loại>.png` | chữ Farm / Sawmill / Quarry / Iron Mine / Gems Mine | TYPE_ROW (0,70,100,78) / 0.8 | bấm icon phía trên chữ 5 % |
| `plus.png`, `minus.png` | nút cấp | PANEL / 0.85 | ô số cấp đọc bằng `read_number` (px 305,568–375,592) |
| `unchecked.png` | ô "full resources" chưa tích | PANEL / 0.9 | đã tích chỉ khớp 0.73 |
| `occupy.png` | Occupy ở menu tròn | MENU (0,25,70,70) / 0.85 | menu ô đất trống cũng có Occupy: chỉ bấm ngay sau Search |
| `noTarget.png` | "No matching targets..." | cả màn / 0.8 | màn khác ≤ 0.44 |
| `marchFull.png` | "You cannot send more troops." (sau Occupy) | cả màn / 0.8 | hết đường march (số đường tuỳ tài khoản); màn khác ≤ 0.55 |
| `targetTaken.png` | "You can only send one army to the target at a time." (sau Occupy) | cả màn / 0.8 | Search ra mỏ đội mình đang tới; màn khác ≤ 0.50 |
| `rss_<loại>.png` | ảnh mỏ ở giữa màn | CENTER (25,35,75,62) / 0.7 | chỉ khi menu tròn chưa mở; không thấy thì không bấm mù |
| `marchTitle.png` | tiêu đề màn March | cả màn / 0.85 | |
| `noTroops.png` / `marchButton.png` | nút March xám / vàng | MARCH_BAR (55,90,100,98) / 0.95 | hai nút khớp chéo 0.85 |

OCR giờ ở màn March: `bot/ocr/read_march_time.py`, font `Images/OCR/MarchTime` (chữ trắng nhỏ, tách như `read_bubble_time`). Vùng px:
giờ thu thập (100,608)–(190,630), giờ đi (280,676)–(340,694). Không đọc được thì coi như 1 giờ.

## Ngưỡng đã đo

| Template | Màn đúng | Màn khác cao nhất | Ngưỡng |
| --- | --- | --- | --- |
| type_* | 1.00 (lệch nửa chữ 0.87) | 0.67 | 0.8 |
| unchecked | 1.00 | 0.75 (đã tích) | 0.9 |
| occupy | 1.00 | 0.42 | 0.85 |
| noTroops / marchButton | 1.00 | 0.85 (nút kia) | 0.95 |
| noTarget | 0.99–1.00 | 0.44 | 0.8 |
| marchFull | 1.00 | 0.55 | 0.8 |
| targetTaken | 0.99 | 0.50 | 0.8 |
| rss_* | 1.00 | 0.34 (loại khác) | 0.7 |

## Đo thật trên giả lập (21913, 2026-10-23)

- Bấm Search: camera kéo mỏ vào giữa và **menu tròn tự mở** (Occupy, Add Bookmark, Detail, Share); ô mỏ nhấp nháy xanh.
- Đổi loại mỏ thì cấp về **Lv 1** và ô "full resources" **bỏ tích**; mở lại bảng thì nhớ loại / cấp lần trước.
- Thanh cấp **lên quá 15** (đã thấy Lv 17) nên không dùng "bấm + tới 15 rồi trừ"; game có lúc lỡ một lần bấm → đọc ô số rồi bấm bù.
- Vuốt nhanh hàng loại mỏ thì văng tới nhóm quái cuối hàng (Ymir, Knight Bayard...); vuốt chậm 1 giây thì đúng nấc.
- Back khi bảng Search mở: đóng bảng (menu tròn còn). Back khi menu tròn mở: hộp "thoát game" (như menu công trình).
- Hết lính: màn March hiện 0 / 207,500 và nút March xám → dừng, chờ 30 phút.
- Hết đường march (alt 21913 có 5 đường, alt khác tới 8; bot không đếm số đường mà dựa vào thông báo): bấm Occupy không vào màn March, chữ "You cannot send more troops." hiện ~1 giây → dừng, chờ 10 phút
  (trước khi sửa: mỗi đội mất ~2 phút thử lại rồi mới bỏ).
- Search luôn ra mỏ gần nhất, kể cả mỏ đội mình đang đi tới → Occupy báo "You can only send one army to the target at a time."; Search lại
  vẫn ra mỏ đó → bỏ đội này lượt này (chờ 10 phút).
- Màn March mở ra đã có quân / tướng game chọn sẵn (có lúc "Select a Main General" nhưng vẫn March được, chỉ có lính).

## Test

[tests/gather_resources/test_flow.py](../../../tests/gather_resources/test_flow.py), ảnh thật trong `tests/gather_resources/screens/`:
flow chính (Food Lv 10, Troop 1), hết lính, hết đường march, mỏ đã có đội mình tới, không tìm thấy mỏ (Gems Lv 15).

## Chưa biết / cần ảnh

- Mỏ đã có người chiếm (nút Occupy đổi thành tấn công?) — chưa gặp; "full resources" chắc chắn là mỏ trống.
- Giờ thu thập trên màn March là giờ để đầy sức chở; mỏ ít hơn thì đội về sớm hơn giờ đã lưu (đội rảnh mà bot chưa gửi lại tới giờ).
- Không chọn preset: số lính mỗi đội do game quyết định (có khi gửi toàn bộ lính còn trong thành cho một đội).
- Không tìm thấy mỏ ở cấp đã chọn: chưa tự hạ cấp.
- `rss_stone.png` cắt từ ảnh có mỏ không ở đúng giữa màn (khớp 1.00 trên ảnh đó, chưa đo ở CENTER).
