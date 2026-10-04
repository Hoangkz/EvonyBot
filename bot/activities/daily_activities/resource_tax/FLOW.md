# Flow: Resource Tax

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

1. Tìm hàng `ActivitiesTaxResource.png`, bấm Go.
2. `CityTax/menuTax.png` (menu Chợ, ảnh dùng chung với King's Path City Tax): bấm Tax.
3. `CityTax/taxScreen.png` (màn Tax, 4 dòng Lúa / Gỗ / Đá / Sắt): `resource_tax/run.py tax_all` theo group
   "City Tax" của tab: loại tích Free trước, thu hết lượt free rồi cộng thêm số chọn ("+" từ số mặc
   định của popup); rồi các loại khác đúng số chọn (OCR ô số popup, "+" / "−"). Xong thì Back về thành, coi như xong hôm nay.
4. `CityTax/popupCost.png` (popup Tax còn mở): Back.
5. Các ảnh `TaxFinish2.png`, `TaxFinish.png`, `TaxFinish1.png` báo hoàn thành.
