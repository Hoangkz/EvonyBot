"""
milestones.py — MỐC RƯƠNG của event (số ghi dưới mỗi rương ở đầu màn event). Game đổi mốc thì
chỉ sửa ở đây.

Gather Troops: 5 rương trái -> phải, số dưới mỗi rương (ảnh tests/event/claim_screens/
gather_chest_10.png: 5 / 10 / 30 / 50 / 70). Mốc cuối cũng là số sau "/" ở "Progress: x / 70"
(dùng để kiểm OCR). Giữ đủ 5 số, theo thứ tự trái -> phải.
"""
GATHER_TROOPS = [5, 10, 30, 50, 70]
