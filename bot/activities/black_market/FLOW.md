# Flow: Black Market (activity)

Code: [run.py](run.py), hằng: [constants.py](constants.py), danh mục vật phẩm: [items.py](items.py) (icon ở
`Images/Black Market/Items/`). Tab UI: [ui/tabs/black_market_tab.py](../../../ui/tabs/black_market_tab.py). Màn Black
Market (tiêu đề, 6 ô, Confirm, Instant Refresh, icon kim cương) dùng chung ảnh / toạ độ với King's Path:
[event/kings_path/black_market/constants.py](../event/kings_path/black_market/constants.py). Test:
[tests/black_market/test_flow.py](../../../tests/black_market/test_flow.py). Việc còn lại: [TODO.md](TODO.md).

## Cấu hình (tab Black Market)

| Khoá | Ý nghĩa |
| --- | --- |
| `check_gold` | vàng < 2.000.000 thì dừng (kim cương < 50 thì **luôn** dừng) |
| `refresh` | số lần Instant Refresh tối đa ("ALL" = không giới hạn) |
| `quantity_buy` | số lần mua tối đa ("ALL" = không giới hạn) |
| `resources` | mua gói tài nguyên 4 loại lương thực / gỗ / đá / quặng (mặc định tích) |
| `items` | `{id: bool}` các món trong items.py (Chips 100 mặc định tích) |

Món `buy_with_gems: true` trong items.py (Stamina 50, các loại đá, Tactic Scroll, Medal — chỉ bán bằng kim cương)
được mua bằng kim cương; Resource và Chips **không bao giờ** mua bằng kim cương.

## Luồng

1. **Mở màn Black Market**: đang ở đó thì thôi. Không thì Back (tối đa 5 lần) tới màn chính (nút "•••"), rồi đưa Chợ
   vào giữa màn (`_market`), dừng ở cách đầu tiên được:
   1. Chợ có trên màn (ảnh mẫu civ / ảnh tự học) -> kéo vào giữa.
   2. Máy đã có **bản đồ thành** (DB, cột `devices.city_map`) -> tìm trên màn một công trình đã có trong bản đồ -> vuốt
      thẳng (chia đều vài cú) tới Chợ -> kéo bù ([city_map.py](city_map.py) `goto`).
   3. Go nhiệm vụ Daily **mua Black Market**, không có thì **Tax** (game kéo Chợ vào giữa) — không quét.
   4. Go nhiệm vụ Daily **Gold Levy** (game kéo Thành chính vào giữa): chưa có bản đồ -> **quét thành** (`scan`: đi vòng
      13 ô theo [city_tour.py](city_tour.py), kéo bù mỗi ô, ghi mọi công trình nhận ra được) -> lưu DB
      -> đi thẳng tới Chợ.
   5. Không nhiệm vụ nào còn Go -> **không làm Black Market**, ghi log.
   Bấm Chợ -> menu -> icon "Black Market" (ảnh mẫu chỉ túi tiền, ngưỡng 0,8) -> chờ tiêu đề.
2. **Mỗi bước chụp 1 ảnh**:
   1. Số dư (OCR `read_gems` / `read_gold`): kim cương < 50 -> dừng; vàng < 2.000.000 và `check_gold` -> dừng.
   2. Đủ `quantity_buy` lần mua -> dừng.
   3. **Quét 6 ô** (`scan`): ô có nút giá xanh (còn mua được) và có món được tích:
      - món thường: icon (phần hình phía trên ô, bỏ số lượng) khớp >= 0,8;
      - gói tài nguyên: icon gói 5M cùng loại khớp >= 0,8, hoặc chữ số lượng (`Items/Resource/*.png`, 10k .. 5M)
        khớp >= 0,85; gói vàng (icon Gold 50k / 100k khớp hơn) -> bỏ;
      - ô giá kim cương của món không được mua bằng kim cương -> bỏ khỏi danh sách.
   4. Còn ô chưa bấm trong bộ hàng này -> bấm ô đầu -> chờ hộp "Are you sure ...?" (tối đa 5 s) -> Confirm (+1 lần
      mua); không hiện -> bỏ ô đó.
   5. Hết ô: đủ `refresh` lần -> dừng; không thấy Instant Refresh -> dừng; còn lại -> Instant Refresh (miễn phí trước,
      hết thì 50 kim cương; có hộp xác nhận thì Confirm), chờ ô 1 đổi = bộ hàng mới, quét lại.
3. **Dừng**: ghi lý do (bot.record), Back đóng màn Black Market. 30 bước liên tiếp không làm được gì -> dừng (kẹt).

## Đã chạy thật

21943 (2026-10-05): `goto` Thành chính từ Trại cung thủ (4 cú, (196, 345)); `scan` 13 ô ~3,5 phút, 11 công trình
(lệch toạ độ ô đo tay 3 .. 27 px); `goto` Chợ từ Lò rèn (3 cú, (194, 350)).

Máy 21913 (2026-10-05): từ màn thành -> nhận ra Chợ (civ 1) -> Black Market -> Refresh 3 lần, mua 2 gói 5M (đá,
lương thực, giá 1.763.000 vàng) -> dừng ở giới hạn Refresh.
