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
| 04 | Màn hình March đã chọn đội có tướng chính (kính lúp `generalSearch.png` ở Main General) | `tap("JoinBoss/hanhquan.png")`. Nếu ảnh có `selectGeneral.png` thì chèn thêm các bước chọn tướng trước |
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

## Event — `tests/event/<event>/<nhiệm vụ>/` (VD `tests/event/gather_troops/cultivate_generals/`)
Hiện chỉ là stub (`TODO: real automation`, chỉ log và sleep 1 s). Flow test tạm thời là `[Step("01_home.png", end())]`. Khi activity được viết thật thì thay bằng flow đầy đủ.

## Event — `tests/event/<event>/<nhiệm vụ>/` (VD `tests/event/gather_troops/cultivate_generals/`)
Settings: `{"gather_troops_cultivate_generals": {"enabled": True, "day": 1}}`
Hiện chỉ có nhiệm vụ Cultivate Generals (Gather Troops), đi qua dòng Go "300 / 500" (OCR 300) rồi bấm Cultivate x100 / Cancel 7 lần tới 1000.

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn hình chính còn quà đăng nhập | `tap_at(361, 148)` (icon `Event/LoginGift/icon.png`) |
| 02 | Super Value Return, tab Login Gifts | `tap_at(37, 197)` (hộp quà dưới chữ `LoginGift/title.png` + (-19, 56), không phụ thuộc ngày), `back()` |
| 03 | Màn hình chính (`Server/listActivity.png`) | `tap_at(369, 281)` (chữ `Event/eventCenter.png` + (10, 40)) |
| 04 | Danh sách event (Wine Festival Event) | `tap("Event/GatherTroops/icon.png")` |
| 05 | Gather Troops, tab "Be Prepared" | `tap("Event/GatherTroops/CultivateGenerals/recruitMore.png")` |
| 06 | Gather Troops, tab "Recruit More" | `tap_at(335, 344)` (Go gần tab nhất) |
| 07 | Danh sách Generals, tim lọc chưa tích (`07_generals_heart_off.png`, `JoinBoss/favoriteOff.png`) | `tap_at(139, 208)` (bấm tích) |
| 07 | Danh sách Generals, tim lọc đã tích (`JoinBoss/favoriteOn.png`) | `swipe(50, 85, 50, 15)` × 6, `tap_at(40, 634)` (10%, 90%), chờ màn đổi |
| 09 | Chi tiết tướng, hàng 3 nút | `tap("Event/GatherTroops/CultivateGenerals/CultivateButton/1.png")` |
| 12 | Chi tiết tướng, hàng 4 nút (có Specialty) | `tap("Event/GatherTroops/CultivateGenerals/CultivateButton/2.png")` |
| 10 | Màn Cultivate, tab "Cultivate Once" | `tap("Event/GatherTroops/CultivateGenerals/quickCultivate.png")` |
| 11 | Tab "Quick Cultivate" (`quickCultivateSelected.png`), có nút x100 | `tap("Event/GatherTroops/CultivateGenerals/cultivateX100.png")` (đã làm += 100) |
| 13 | Tab "Quick Cultivate", nút đổi thành Cancel | `tap("Event/GatherTroops/CultivateGenerals/cancel.png")`, quay lại 11; đạt 1000 thì `end()` và đánh dấu xong |

Nhánh phụ:
- `08` có nút "Claim All": `tap("Event/claimAll.png")` trước mọi thứ.
- Tab Recruit More hết Go: `end()`, đánh dấu `gather_troops_cultivate_generals` đã xong.
- Đã xong từ lần reset gần nhất / ô không tích: `end()` ngay.
- Danh sách event không có Gather Troops: `swipe(50, 80, 50, 50)` × 4, `back()`, rồi `end()`.
- Không qua dòng Go (không biết số đã làm): tới tab Quick Cultivate thì `end()`, không bấm x100.
- Event Center không có test riêng (theo yêu cầu).

### Ground Troop — `tests/event/gather_troops/ground_troop/`
Settings: `{"ground_troop": {"value": 20000, "level": 13, "day": 2}}` (ô chọn 0 = tắt).
Bước 01–04 giống hệt Cultivate Generals (ảnh chép sang `screens/`); tới màn Gather Troops thì đếm ổ khoá `Event/dayLock.png` trên hàng tab Day:
- 4 ổ khoá (Day 2..5 khoá): lưu `ground_troop_locked` vào daily_done (bỏ qua tới lần reset) rồi `end()`.
- Ít hơn (VD `07_gather_day1.png` không khoá, `06_day_locked_tmp.png` chỉ Day 4–5 khoá): đi tiếp.

| # | Màn hình | Action |
| --- | --- | --- |
| 07 | Gather Troops, tab Day 1 | `tap("Event/GatherTroops/GroundTroop/day2.png")` |
| 08 | Day 2, tab phụ "Seize Time" | `tap("Event/GatherTroops/GroundTroop/groundTroop.png")` |
| 09 | Day 2, tab "Ground Troop" (`groundTroopSelected.png`) | OCR "0 / 500" trên Go đầu tiên, `tap_at(335, 344)` (chờ 10 s) |
| 10 | Thành, doanh trại ở giữa màn hình | `tap_at(198, 352)` (giữa màn hình); chưa thấy Train thì chờ 3 s, bấm giữa thêm 1 lần |
| 11 | Menu doanh trại (`Event/GatherTroops/Train/train.png`) | `tap("Event/GatherTroops/Train/train.png")` |
| train_tNN | Màn Train, cấp NN đang ở giữa (mở ở cấp train lần trước) | Chọn cấp (`gather_troops/troop_tier.py`): bấm cấp phải nhất để đi lên / trái nhất để đi xuống (cấp vừa bấm nhảy ra giữa) tới cấp người dùng chọn, hoặc cấp mở cao nhất dưới ổ khoá đầu tiên; cấp kết quả ở giữa thì OCR số tối đa một lần train (ô bên phải nút "+", font `TrainCount`), tính số lần, `tap(".../Train/trainButton.png")` |
| train_t13?training | Nút đã thành "Training Speedup" (biến thể: dán đáy ảnh thật `train_training.png`, không còn nút "+") | `tap(".../Train/trainingSpeedup.png")` (≈ (295, 672)) |
| speedup | Màn Training Speedup | Lần đầu: `tap(".../Train/speedupSettings.png")`; sau đó `tap(".../Train/finishAll.png")` |
| speedup_settings(_ticked) | Hộp Finish All | Ô góc dưới trái chưa tích thì `tap(".../Train/checkboxOff.png")`, rồi `tap(".../Train/confirm.png")` |
| train_t13 (sau Finish All) | Nút Train hiện lại, đã bấm đủ số lần | `end()`, đánh dấu `ground_troop` đã xong |

Biến thể màn Train: `locked_12` (dán ổ khoá lên XII, XIII của `train_t11`) → train cấp 11, mục tiêu 10000 theo event.json; ảnh thật `locked_1407xx.png` (tài khoản chỉ mở cấp I, cấp II+ khoá): mở ở VII → lưu `ground_troop_locked`; mở ở XII → bấm cấp trái nhất (X, VIII) tới khi thấy VII khoá → lưu `ground_troop_locked`.

Tab Ground Troop hết Go (biến thể `no_go`): `end()`, đánh dấu `ground_troop` đã xong.

TODO: `06_day_locked_tmp.png` là ảnh tạm (màn King's Path); biến thể `day2_locked` dán thêm ổ khoá lên Day 2, Day 3. Thay bằng ảnh Gather Troops thật khi có.
Nhánh phụ: đã lưu `ground_troop_locked` / ô chọn 0 → `end()` ngay; danh sách event không có Gather Troops → giống Cultivate Generals.

### Mounted Troop — `tests/event/gather_troops/mounted_troop/`
Settings: `{"mounted_troop": {"value": 20000, "level": 13, "day": 3}}`. Flow chung với Ground Troop (`gather_troops/train_troop/`, mỗi nhiệm vụ khai báo một `TroopTask`), chỉ khác:

| # | Màn hình | Action |
| --- | --- | --- |
| 07 | Gather Troops, tab Day 1 | `tap("Event/GatherTroops/MountedTroop/day3.png")` |
| 08 | Day 3, tab phụ "Mounted Troop" (mặc định, `mountedTroopSelected.png`) | OCR "0 / 500", `tap_at(335, 344)` |
| 09 | Day 3, tab phụ "Ranged Troop" đang chọn | `tap("Event/GatherTroops/MountedTroop/mountedTroop.png")` |
| 10 / 11 | Thành, chuồng ngựa (Stables) ở giữa / menu Stables | giống Ground Troop |
| train_tNN | Màn Train lính kỵ (ảnh cấp `MountedTroop/Tier/<cấp>.png`, I..XV) | giống Ground Troop; `train_t13` OCR 40785 / lần |

- 3 ổ khoá (Day 3..5 khoá, biến thể `day3_locked` trên ảnh tạm `06_day_locked_tmp.png`): lưu `mounted_troop_locked`.
- Ảnh thật `locked_1754xx.png` (chỉ mở cấp I): mở ở I → lưu `mounted_troop_locked`; `locked_175511` (X..XIII khoá) → bấm X, IX → thấy VI..IX khoá → lưu `mounted_troop_locked`.
- Màn Training Speedup / hộp Finish All dùng chung ảnh với Ground Troop (chép `speedup*.png`).
- `train_training.png` (ảnh thật, Mounted / Ranged / Siege mỗi loại một ảnh): vừa vào màn Train đã đang train → `tap(".../Train/trainingSpeedup.png")`, Finish All trước rồi mới chọn cấp (không lưu `*_locked` dù cấp ở giữa không có nút "+").

### Ranged Troop — `tests/event/gather_troops/ranged_troop/`
Settings: `{"ranged_troop": {"value": 20000, "level": 13, "day": 3}}`. Giống Mounted Troop (cùng Day 3, cùng ảnh `MountedTroop/day3.png`), nhưng tab phụ bên phải:

| # | Màn hình | Action |
| --- | --- | --- |
| 08 | Day 3, tab Mounted Troop (mặc định) | `tap("Event/GatherTroops/RangedTroop/rangedTroop.png")` |
| 09 | Day 3, tab Ranged Troop (`rangedTroopSelected.png`) | OCR "0 / 500", `tap_at(335, 344)` |
| train_tNN | Màn Train lính cung (`RangedTroop/Tier/<cấp>.png`, I..XVI) | giống Ground Troop; `train_t13` OCR 28266 / lần |

- `locked_180037` (I..IV) → bấm IV → `locked_180045` (V, VI khoá) → lưu `ranged_troop_locked`; `locked_180117` (XII..XVI khoá) → bấm XII, X, VIII → `locked_180100` → lưu `ranged_troop_locked`.
- `10_after_go.png` / `11_train_menu.png`: trại cung (Archer Camp); icon Train trên menu này chỉ khớp 0,86 (ngưỡng 0,8).

### Siege Machine — `tests/event/gather_troops/siege_machine/`
Settings: `{"siege_machine": {"value": 20000, "level": 13, "day": 4}}`. Giống Mounted Troop nhưng Day 4:

| # | Màn hình | Action |
| --- | --- | --- |
| 07 / 07_gather_day3 | Gather Troops, tab Day 1 / Day 3 | `tap("Event/GatherTroops/SiegeMachine/day4.png")` |
| 08 | Day 4, tab Siege Machine (mặc định, `siegeMachineSelected.png`) | OCR "0 / 500", `tap_at(335, 344)` |
| 09 | Day 4, tab Defense Force đang chọn | `tap("Event/GatherTroops/SiegeMachine/siegeMachine.png")` |
| train_tNN | Màn Train xe công thành (`SiegeMachine/Tier/<cấp>.png`, I..XV) | giống Ground Troop; `train_t13` OCR 20812 / lần |

- `06_day_locked_tmp.png` (Day 4, 5 khoá) dùng thẳng, không cần biến thể: lưu `siege_machine_locked`.
- `locked_201311` (I..IV) → bấm IV → `locked_201315` (V, VI khoá) → lưu `siege_machine_locked`; `locked_201352` (XII..XVI khoá) → bấm XII, X, VIII → `locked_201328` → lưu `siege_machine_locked`.
- `10_after_go.png` / `11_train_menu.png`: xưởng (Workshop) thật.
- Xưởng đang có mẻ train (áp dụng cho mọi loại lính, flow chung): bấm giữa sau Go → `11_speed_up_menu.png` (menu có Speed Up / Instant Finish / Cancel / View, không có Train; icon View khớp nhầm `train.png` 0,92) → `tap(".../Train/speedUp.png")` → `speedup_workshop.png` (Speedup Settings → Confirm → Finish All) → `12_after_finish_all.png` (về thành) → `tap_at(198, 352)` lần nữa → `11_train_menu.png` → Train như thường.

### Defense Force — `tests/event/gather_troops/defense_force/`
Settings: `{"defense_force": {"value": 7000, "level": 6, "day": 4}}`. Flow chung `train_troop` (TroopTask có `lowest=3`, `menu_icon=build.png`, `speedup_title` riêng), khác lính ở:

| # | Màn hình | Action |
| --- | --- | --- |
| 08 | Day 4, tab Siege Machine (mặc định) | `tap("Event/GatherTroops/DefenseForce/defenseForce.png")` |
| 09 | Day 4, tab Defense Force | OCR "0 / 1,000", `tap_at(335, 344)` |
| 10 / 11_build_menu | Thành, Trap Factory / menu có "Build" (không có Train) | `tap_at(198, 352)` / `tap(".../DefenseForce/build.png")` |
| 11_speed_up_menu | Trap Factory đang xây (Speed Up) | như lính: Speed Up → `speedup_trap.png` ("Trap Building Speedup") → Finish All → về thành → bấm giữa lại |
| train_<cấp>_<loại> | Màn Train bẫy: mỗi cấp 4 vòng Trap, Rock, Abatis, Fire Arrow (ảnh `DefenseForce/Tier/<cấp>_<loại>.png`, I..VII) | `troop_tier` lấy ảnh khớp cao nhất mỗi vòng; khoá theo từng loại, một cấp khoá khi cả 4 loại khoá; loại nào mở cũng train |

- Tài khoản A (`train_*`): Rock VII → bấm vòng trái nhất (Fire Arrow VI, Rock VI, ..., Rock IV) → bấm Fire Arrow III → train cấp 3.
- Tài khoản B (`b_*`): cấp IV khoá hết, Fire Arrow III khoá → train cấp III bằng loại khác. Bước cuối dùng `b_train_3_abatis.png` thay cho Fire Arrow III ở giữa (chưa có ảnh đúng).
- Chưa có ảnh tài khoản khoá cả cấp III (→ `defense_force_locked`).

### Quy tắc chung các nhiệm vụ Gather Troops (Cultivate Generals + 5 nhiệm vụ train)
Mỗi nhiệm vụ phải đi qua màn Gather Troops trong lượt chạy của nó: mở từ danh sách event, hoặc đang ở sẵn màn Gather Troops thì làm luôn tại đó (lần đầu thấy màn này: kiểm tra Day khoá). Rồi tab → bấm Go (đọc số đã làm) → các màn sau Go. Gặp màn sau Go (menu công trình / màn Train / speedup / danh sách Generals / Cultivate) trước khi bấm Go → `back()` (log `"<tên>: <action> before Go, back"`) cho tới khi về lại Gather Troops. Test: `test_started_on_train_screen_goes_back_to_event`, `test_started_on_gather_troops_continues_there`, `test_started_on_gather_troops_day_locked` (Mounted Troop); `test_started_on_gather_troops_continues_there`, `test_started_mid_flow_goes_back_to_event` (Cultivate Generals).
Sau Go: mỗi lần bấm giữa màn hình chờ thêm 2 s (`CENTER_TAP_EXTRA`) cho menu công trình hiện.

## Event / King's Path — `tests/event/kings_path/test_flow.py`
Settings: `{"kings_path_patrol": {"value": 200, "day": 2}}` (mỗi nhiệm vụ một key `kings_path_*`).
Chưa có ảnh icon King's Path trong danh sách event: test bắt đầu ngay ở màn King's Path và tạm patch `path_task.KINGS_PATH_ICON` sang icon Gather Troops.
Flow chung (path_task.py): Day khoá? -> tab Day -> tab phụ -> nút Go của nhiệm vụ (dòng trên cùng, hoặc dòng có tiêu đề `row_title`) -> OCR "a / b" -> đạt mục tiêu thì xong, chưa thì bấm Go (phần sau Go: TODO).
Biến thể ảnh: `claimed` (xoá nút Claim All), `not_kp` (xoá tiêu đề "King's Path" -> bot phải Back).

## Event Center / Crazy Eggs — `tests/event_center/crazy_eggs/test_flow.py`
`bot/activities/event_center/` KHÔNG phải activity (không có trong ACTIVITIES): chứa nhiệm vụ Event Center, nơi cần thì gọi `event_center.crazy_eggs.run(bot, settings)`.
Quả đập được = có icon búa (`EventCenter/CrazyEggs/hammer.png`) trong nhãn "Scout Cost:"; số quả theo vị trí búa (cột 1: x < 50 %, hàng 1: y < 70 % màn); bấm thẳng vào tâm búa. Kết thúc khi hết quả có búa hoặc hết búa (hộp thoại "You don't have enough Hammers" → Cancel; dự phòng: bấm mà số quả có búa không giảm).

| # | Màn hình | Action |
| --- | --- | --- |
| 01 | Màn chính | `tap_at(359, 216)` — bấm chính icon cúp Event Center (tâm chữ + (0, -25)) |
| 02 | Event Center, tab Limited (nhận bằng `EventCenter/competitionTab.png`) | `tap("EventCenter/activitiesTab.png")` |
| 03 | Tab Activities, đầu danh sách (không thấy icon) | `swipe()` |
| 03_activities_crazy_eggs | Tab Activities đã cuộn tới Crazy Eggs (ảnh thật) | `tap("EventCenter/CrazyEggs/icon.png")` |
| 04 | Crazy Eggs, 4 quả có búa | `tap_at(297, 393)` (búa quả 2) |
| 06 | Popup "Congratulations!" (ảnh thật của một lần đập khác) | `back()` |
| ?cracked_2 → ?cracked_23 → ?cracked_231 | Crazy Eggs, bớt dần quả có búa (nhãn lấy từ ảnh 05) | bấm quả 3, 1, 4 |
| 05 | Crazy Eggs, 4 quả "Waiting:" | búa vàng: `tap_at(250, 391)` (nhãn "Waiting:" quả 2) |
| 07 | Hộp thoại "Use the Lucky Hammer ... Confirm use?" | `tap("EventCenter/CrazyEggs/confirm.png")`, lưu `crazy_eggs_lucky_hammer` |
| 06 | Popup "Congratulations!" sau khi Confirm (giống đập thường) | `back()` |
| 05 | Crazy Eggs, 4 quả "Waiting:" | `end()` |

Nhánh phụ: bấm quả 2 mà ảnh không đổi → hết búa, quả 2 không chờ nên không dùng búa vàng, return; mọi quả "Waiting" + búa vàng đã dùng hôm nay → return ngay; bấm quả 2 dùng búa vàng mà không hiện hộp thoại → lưu đã dùng, return; quả 1 "Activated" (`08_egg_1_activated.png`, búa vàng đã dùng) → chỉ đập quả 3 → animation trứng vỡ (`10_egg_breaking.png`, màn tối) → `tap_pct(50, 95)` → popup trứng vỡ "Congratulations on activating the egg!" (`09_egg_activated_rewards.png`) → `back()` → return; số búa vàng trên màn là "0" (`12_all_activated.png`, 4 quả đã vỡ) → lưu đã dùng, return; bấm quả 3 khi hết búa → hộp thoại `11_not_enough_hammers.png` → `tap("EventCenter/CrazyEggs/cancel.png")` → return; màn Event Center không có tab Activities (`02?no_activities_tab`) → 3 lần (01 → 02 → `back()`), `shell("am force-stop")`, thêm 2 lần → lưu `crazy_eggs_done`, return; đã có `crazy_eggs_done` → return ngay; tab Activities không có icon (`03_activities.png` thật) → 3 lần (01 → 02 → 03 cuộn 8 lần → `back()`), `shell("am force-stop")`, thêm 2 lần → lưu `crazy_eggs_done`, return.
