# TODO — Craft

Việc còn dang dở của activity Craft (tab Craft, chế tạo trang bị). Mô tả luồng hiện tại: [FLOW.md](FLOW.md).

## Chưa làm

- [ ] **Nhận / đổi quà event** (`claim_event_gifts`, `gift_order`): tab đã có ô tích "Claim event gifts" và danh sách quà ưu tiên (Resource, Stamina), cấu hình được lưu
  nhưng **bot chưa dùng**. Cần: event nào, ảnh màn đổi quà, thêm quà còn thiếu vào `GIFTS` ([constants.py](constants.py)). Hiện nhiệm vụ chỉ chạy khi có tích
  trang bị (`JOB.enabled`): chỉ tích nhận quà mà không tích trang bị thì chưa chạy gì.

## Chưa kiểm chứng / thiếu ảnh

- [ ] Hộp **Finish All / Speedup Settings** lần đầu của tài khoản chưa đặt: code theo Heal nhưng chưa thấy chạy thật (tài khoản thử 21943 đã cài sẵn, bấm Finish All chạy thẳng).
- [ ] **Hết vật phẩm tăng tốc** / Finish All không đủ: chưa biết màn báo. Hiện không thấy bóng trang bị -> log "finished item not collected" rồi dừng cả nhiệm vụ.
- [ ] Màn ngay **sau Quick Compose** (hộp xác nhận? nút đổi thành Begin ngay hay chậm?): chưa chụp; có thể cần Quick Compose nhiều lần cho một trang bị.
- [ ] Chạy thật **từ thành** với trang bị vàng thật và nhiều loại (mới chạy thật với Iron Ring loại Nhẫn, đi hết một vòng: Lò rèn -> Craft -> Begin -> Speed Up -> Finish All -> nhận).
  Chưa thử loại khác (mũ, giáp, quần, giày, cung, giáo, rìu, kiếm, chuỳ) khi chuyển loại bằng vòng chọn.
- [ ] Chưa thử **tìm route Lò rèn** trên máy chưa có route (`reach_building` tự quét) và nền văn minh khác civ1 (route theo civ, xem bot/city/MEASURE_CIV.md).
- [ ] Nhánh `locked, skip` (trang bị khớp icon nhưng nằm bên phải ô khoá) chưa có ảnh test; mới test nhánh `behind a locked item`.
- [ ] Chạy cùng **Join Boss**: một vòng chế tạo ~90 s (sát giới hạn 120 s), bị ngắt thì làm lại từ đầu vòng. Cân nhắc `must_finish` hoặc rút ngắn (xem "Tối ưu").

## Lỗi / rủi ro đã biết

- [ ] Bị ngắt **ngay sau Finish All** (trong 3 s chờ, trước `consume_pending`): chưa trừ số còn lại và bóng trang bị chưa được nhận -> lần sau làm dư một cái. Cách sửa: trước mỗi
  vòng kiểm tra bóng trang bị trên Lò rèn, thấy thì nhận ngay (và trừ số).
- [ ] `_remaining`, `_pending`, `_done`, `_total` khoá theo `id(bot)` (giống Refine): Stop rồi Start mà đối tượng mới trùng `id` thì dùng nhầm số cũ. Nên gắn thuộc tính lên `bot`.
- [ ] Người dùng sửa số lượng ở tab **đúng lúc bot đang chạy**: bot trừ 1 rồi lưu cấu hình hiện tại của tab, chưa kiểm xem có ghi đè giá trị vừa sửa không.
- [ ] Hai trang bị khác nhau nhưng **trùng tên** bị gộp thành một khi lọc danh sách icon (chưa thấy trường hợp thật).

## Ảnh / dữ liệu

- [ ] Icon trong `Images/Craft/<loại>/` cắt lệch vài px (khớp 0,68 .. 0,81 với Consul's / Officer's / vài áo giáp, trang bị khác <= 0,58), ngưỡng 0,65 chỉ hơn 0,07 so với
  trang bị khác: nên cắt lại cho đúng khung (vài icon helmet / legs còn vạch đen mép trái hoặc rộng 42 px bù mép).
- [ ] Tên trang bị (tên file + ảnh `name/`) đọc bằng mắt từ ảnh chụp, có thể sai chính tả; kiểm lại.
- [ ] Ô "?" (chưa mở: Trap Factory / Warehouse Officer's Crown / Boots / Ring / Leg Armor ...) đang bỏ; muốn chế cả thì thêm icon.
- [ ] Ring chỉ bỏ 3 ô thấp (thiếu ô xanh đầu danh sách), các loại khác bỏ 4: kiểm lại ranh giới "vàng trở lên" từng loại.
- [ ] Ảnh `Craft/Category/staff.png` cắt từ ảnh người dùng chụp (Refine chưa có ảnh `active` cho chuỳ).

## Tối ưu / dọn

- [ ] **Chờ cứng** -> `wait_for`: sau bấm Begin / Quick Compose (3 s), sau chọn trang bị (2 s, đợi tên khớp), chờ bóng trang bị 4 s + bấm mò 4 lần (nên chờ hộp
  "Congratulations on getting"), sau Speed Up / Craft trong menu (2 s). `delay=2` ở `collect` và `delay=1` ở `finish_all` đang viết thẳng trong code. Cân nhắc `EXTRA_WAIT` như Heal cho máy chậm.
- [ ] `items_to_start` vuốt chậm mất 15 .. 30 s mỗi lần mở loại (đầu danh sách còn nảy lại nên mỗi cú vuốt ~4 s); có thể bỏ qua nếu đã ở đầu, hoặc nhớ vị trí.
- [ ] Log: chưa có dòng tổng kết khi lượt bị dừng sớm (không tới Lò rèn, kẹt vòng chọn loại); chỉ lượt hoàn tất mới in `summary`.
- [ ] Test: chưa có flow test cho `open_craft` / `run` toàn bộ (thiếu ảnh màn Lò rèn rảnh -> Craft), `collect` khi không thấy hộp, hộp Finish All lần đầu, `craft_next` nhiều loại.
- [ ] Chưa commit các thay đổi của activity Craft (code, ảnh `Images/Craft/`, test).
