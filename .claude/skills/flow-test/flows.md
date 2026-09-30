# Flow chính dự kiến của từng activity

Các flow dưới đây được suy ra từ code (`_targets()` và các handler). Khi chụp ảnh thật, nếu màn hình game khác với mô tả thì sửa file này cùng `FLOW` trong test. Đường dẫn template tính từ `Images/`.

Ký hiệu: `→` là action mong đợi trên màn hình đó.

---

## Open Gift Box — `tests/open_gift_box/`
Settings: `{"selection_gift_box": {"Gift Box Boss": True}}`

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính, thấy nút chức năng | `tap("OpenBox/Setup/chucnang.png")` |
| 02 | Menu chức năng | `tap("OpenBox/Setup/Items.png")` |
| 03 | Danh sách hộp quà (`Common.png`), có hộp Boss ở y < 650 | `tap("OpenBox/Boss/<n>.png")` |
| 04 | Popup hộp, có nút Use | `tap("OpenBox/Setup/Use.png")` (hoặc `Open.png`) |
| 05 | Hộp thoại số lượng | `tap("OpenBox/Setup/Max.png")`, `tap("OpenBox/Setup/Use2.png")` |
| 06 | Danh sách hộp, hết hộp Boss, thấy ảnh cuối danh sách (`OpenBox/CheckOpen/*`) | `end()` |

Nhánh phụ:
- Mở bằng `Open.png` (không phải Use): sau Use2, bot chờ `success.png` rồi `back()`.
- Hộp nằm dưới thanh đáy (y ≥ 650): bot `swipe(50, 50, 50, 36)`.

## Alliance Capacity — `tests/alliance_capacity/`
Settings: `{"times": "1"}` (1 lần donate bằng gems)

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính | `tap("JoinBoss/lienminh.png")` |
| 02 | Menu liên minh | `tap("Science/scienceclick.png")` |
| 03 | Danh sách khoa học, có mục được đề xuất | `tap("Science/1sciencekc.png")` |
| 04 | Màn hình donate (`CheckDonate.png`) | `swipe()` (giữ 5 s nút `Science/donate.png` trên cùng) |
| 05 | Hết lượt free, hiện donate bằng gems | `tap("Science/sciencekc.png")` |
| 06 | Hộp thoại mua gems (`Science/buyKc.png`) | `end()` |

Nhánh phụ:
- `times: "No"` thì dừng ngay ở màn hình 05 (`end()`).
- Popup rời liên minh (`JoinBoss/outLM.png`): `tap_at(góc + 40)`, sau đó `back()`.

## Daily Activities — `tests/daily_activities/`
Mỗi task là một flow riêng. Tối thiểu cần các test sau.

1. **Đã xong hết** (không cần chụp nhiều ảnh):
   - Settings: `{"Resource Tax": True}`.
   - `daily_done`: task đó và `"Activity Rewards"` đều có mốc thời gian hiện tại.
   - Flow: `[Step("01_home.png", end())]`, tức activity không được chụp màn hình hay bấm gì.
2. **Một task, ví dụ Resource Tax**. Settings: `{"Resource Tax": True}`

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính, nút Activities | `tap("DailyActivites/ActivitiesTaxResource/Click_Activities.png")` (hoặc biến thể `1`/`2`) |
| 02 | Danh sách activities, thấy dòng Resource Tax ở y ≤ 500 | `tap("DailyActivites/UseAllActivities/Go.png")`, `tap_pct(50, 50)` |
| 03 | Màn hình thuế (`Tax.png`) | `tap("DailyActivites/ActivitiesTaxResource/Tax.png")` |
| 04 | `TaxRevenue.png` | `tap_at(300, 280)` |
| 05 | `TapTax1.png` | `tap_at(200, 300)`, `shell("KEYCODE_DEL")`, `shell("input text 0")`, `shell("KEYCODE_ENTER")`, `tap_at(200, 440)`, `tap_at(195, 415)` |
| 06 | Lượt sau: thấy `TaxFinish*.png` | (không action, task được đánh dấu xong) |
| 07+ | Nhận thưởng `CollectionActivities`: `Click_Activities*`, `20`/`50`/`110`, `Claim_All` | `tap(...)` từng cái |
| cuối | `CollectionActivities/80.png` | `tap("DailyActivites/CollectionActivities/80.png")`, `end()` |

   Assert `"Resource Tax"` và `"Activity Rewards"` có trong dict daily_done sau khi chạy.
3. Mỗi task còn lại (Monster Killing, Offering, Gold Levy, Troop Training, ...) cần một method `test_<task>`. Toạ độ tap cứng của từng handler nằm trong `run.py`, nên dùng `tap_at` với đúng các toạ độ đó.

## Black Market (Market) — `tests/black_market/`
Settings: `{"black_market_items": {"Resources": True}, "refresh": "1", "quantity_buy": "ALL"}`

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính | `tap("Black Market/chucnang.png")` |
| 02 | Menu | `tap("Black Market/activites.png")` |
| 03 | Danh sách Daily Activities, chưa thấy Black Market | `swipe(50, 50, 50, 32)` |
| 04 | Thấy dòng Black Market có `goto.png` | `tap("Black Market/goto.png")`, `tap_pct(50, 49)` |
| 05 | `ChoDen.png` / `ResourcesTax.png` / `BlackMarketCheck.png` | `tap(...)` ảnh đó |
| 06 | Chợ đen (`Refresh.png`) có ô Resources mua được | `tap_at(<ô sau _cell>)`. Lượt scan đầu không có input |
| 07 | Xác nhận mua (`xacnhan.png`) | `tap("Black Market/xacnhan.png")` |
| 08 | Chợ đã mua hết ô muốn mua | `tap("Black Market/Refresh.png")` |
| 09 | Chợ sau Refresh (ô khác 08) | mua tiếp như 06–07, hoặc `end()` nếu không còn gì: refresh đã đạt giới hạn 1 |

Nhánh phụ:
- Hết gems (`buyKc.png`): `back(2)`, `end()`.
- Cuối danh sách không có Black Market (`DailyActivites/khoangden.png`): `back()`, `end()`.

## Black Market (Auction House) — `tests/black_market/` (method riêng)
Settings: `{"auction_is_buy": True, "auction_max_price": "100000"}`. Flow chạy vô hạn nên không có `end()`: harness bật Stop sau bước cuối.

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính | `tap("Black Market/AuctionHouse/Event.png")` |
| 02 | Event Center chưa thấy đấu giá | `swipe(70, 70, 50, 50)` |
| 03 | Thấy `daugia.png` | `tap("Black Market/AuctionHouse/daugia.png")` |
| 04 | `ragegoodsTemp.png` | `tap(...)` |
| 05 | Lô VIP 5000, giá hiện tại + 5000 ≤ max | `tap("Black Market/AuctionHouse/bid.png")` |
| 06 | `comfirm.png` | `tap(...)` |

## Battlefield Shop — `tests/battlefield_shop/`
Settings: `{"quantity_to_refresh": "0"}`, `open_box` / `black_market` để False. Code đang có `TODO: cần làm lại`, nên nếu viết test ngay thì phải xác nhận lại flow với người dùng.

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính | `tap("Black Market/chucnang.png")` |
| 02 | Menu | `tap("Black Market/activites.png")` |
| 03 | Danh sách Daily Activities | `swipe(50, 50, 50, 32)` cho tới khi thấy `BattlefieldShop/rss.png` / `openshop.png` |
| 04 | Dòng Battlefield Shop | `tap("BattlefieldShop/openshop.png")` (hoặc `rss.png`, `goto.png`) |
| 05 | `vaoshop.png` | `tap(...)` |
| 06 | Shop (`Black Market/Refresh.png`) có món trong `BattlefieldShop/buy` | `tap_at(<ô sau _cell>)` |
| 07 | `xacnhan.png` | `tap(...)` |
| 08 | Shop không còn món cần mua | `end()` (giới hạn refresh là 0) |

## Join Monster War — `tests/join_monster_war/`
Xem thêm [bot/activities/join_monster_war/FLOW.md](../../../bot/activities/join_monster_war/FLOW.md).

**Flow chính.** Settings: `{"troop": ["Troop 1"], "use_stamina": "No", "exit_when_idle": True}`

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính có `listboss.png` | `tap("JoinBoss/listboss.png")` |
| 02 | Danh sách War có nút Join (chữ không đỏ, 262 < y < 615) | `tap("JoinBoss/thamgia.png")` |
| 03 | Màn hình March (`hanhquan.png` + `bossMonster.png`) | `tap_pct(11, 11)` (Troop 1) |
| 04 | Màn hình March đã chọn quân (`checkLocam.png`) | `tap("JoinBoss/hanhquan.png")`. Nếu ảnh có `selectGeneral.png` thì chèn thêm các bước chọn tướng trước |
| 05 | Danh sách War chỉ còn `Joined.png` | `swipe(50, 65, 50, 40)` |
| 06 | (dùng lại ảnh 05) | `swipe(50, 65, 50, 40)` |
| 07 | (dùng lại ảnh 05) | `swipe(50, 40, 50, 65)` |
| 08 | (dùng lại ảnh 05) | `swipe(50, 40, 50, 65)` |
| 09 | (dùng lại ảnh 05) | `end(IDLE)` |

Assert `device.reported` có đúng 1 phần tử: toạ độ OCR được, hoặc `None` nếu ảnh không có icon location.

Nhánh phụ, mỗi nhánh một method:
- **Hết thể lực**, `use_stamina: "No"`: màn hình `hettheluc.png` → `end(None)`.
- **Không có boss**, `exit_when_idle: True`: màn hình chính có `lienminh.png`, không có `listboss.png` → `end(IDLE)`.
- **Boss chữ đỏ / boss không được tích** (`selected_bosses` không có tên đó): nút Join không được tap, toạ độ vào BossMemory `SKIPPED`, bot cuộn (`swipe`).
- **Dùng thể lực**, `use_stamina: "ALL"`: `tap(hettheluc)`, `tap(theluc)`, `tap_pct(28.9, 71.6, count=2)`, `tap(usetheluc)`, `back()`.

## Event — `tests/event/`
Hiện chỉ là stub (`TODO: real automation`, chỉ log và sleep 1 s). Flow test tạm thời là `[Step("01_home.png", end())]`. Khi activity được viết thật thì thay bằng flow đầy đủ.
