# Flow: Troop Healing

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Giống King's Path Heal (`event/kings_path/heal`), dùng lại các bước và ảnh của nó.

1. Go → về thành, **Bệnh viện** ở giữa → bấm → menu Bệnh viện:
   - "Speed Up" (đang chữa dở) → Healing Speedup → (lần đầu Speedup Settings, tích ô, Confirm) → Finish All →
     mở lại menu (tối đa `MENU_ROUNDS` lần);
   - "Heal" → màn Hospital;
   - chỉ có Citizen / Detail / "Upgrade" → không có lính bị thương.
2. Màn Hospital: không có dòng lính (không có nút Dismiss) → không có lính bị thương.
3. Có lính: Reset (bỏ chọn hết) → cuộn xuống cuối danh sách (thấy khoảng trống trên khung tài nguyên —
   `kings_path/heal` `LIST_END` — thì thôi cuộn, tối đa 5 lần) → chọn **150 lính** (`HEAL_GOAL`) từ dòng dưới cùng
   (cấp thấp nhất) lên: OCR số lính bị thương mỗi dòng, bấm ô số → gõ min(còn thiếu, số lính) → OK.
4. Heal → Speed Up → Finish All → đánh dấu xong hôm nay (`mark_task_done`).
5. Không có lính bị thương → Back, cũng đánh dấu xong hôm nay (mai kiểm tra lại). Ít hơn 150 thì heal hết số có.

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ hàng `HealActivity.png`.
2. `Heal.png`: vào chức năng Heal.
3. `Heal-i.png`: mở thông tin và cuộn hai lần.
4. `HealSelect.png`: nhập 150, xác nhận hai lần.
5. `HealFinishAll.png`: bấm Finish All.
6. `HealFinish.png` hoặc `HealFinish1.png` báo hoàn thành.
