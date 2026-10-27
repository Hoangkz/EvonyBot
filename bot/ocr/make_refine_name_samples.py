"""
make_refine_name_samples.py — sinh mẫu tên thuộc tính tinh luyện (Images/RefineEquipment/Names/<tên>/) cho read_refine_lines.py.

Chữ ở màn Refine Equipment là Arial ~13 px (đo trên 21913: render Arial 13 khớp chữ thật 0,87 .. 0,91). Mỗi tên một thư mục:
    s.png                       tên trên MỘT dòng (chỉ khi vừa bề rộng ô tên)
    w<bề rộng>f<cỡ>_1.png / _2.png   tên xuống hai dòng khi ngắt theo bề rộng đó (tên dài; game ngắt dòng theo từ, bề rộng chính xác chưa biết nên sinh vài mức).
                                Khung đã cuộn (sau khi bấm Refine) chữ cỡ 13; khung chưa cuộn (có ổ khoá bên trái) tên dài chữ nhỏ hơn (~11) và ngắt dòng khác -> sinh cả cỡ 12, 11
Ảnh là mặt nạ chữ (nền 0, chữ 255) cắt sát chữ. Chạy một lần khi thêm / đổi tên thuộc tính (cần Arial của Windows); bản sinh ra được ship cùng Images/.

    python -m bot.ocr.make_refine_name_samples
"""
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..activities.refine_equipment.constants import FOLDER, SLOTS
from ..context.templates import TEMPLATE_DIR

FONT_FILE = "C:/Windows/Fonts/arial.ttf"
FONT_SIZE = 13
CELL_WIDTH = 186          # bề rộng ô tên (x 12 .. 198)
WRAP_WIDTHS = (90, 100, 110, 120, 130, 140, 150, 160, 170, 178, 186)   # khung chưa cuộn có ổ khoá nên ô tên hẹp hơn: tên ~110 .. 135 px cũng xuống 2 dòng
TWO_LINE_SIZES = (13, 12, 11)     # cỡ chữ của tên hai dòng


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _mask(text: str, font) -> np.ndarray:
    width = int(font.getlength(text)) + 8
    image = Image.new("L", (width, FONT_SIZE + 10), 0)
    ImageDraw.Draw(image).text((4, 3), text, fill=255, font=font)
    array = np.array(image)
    rows, cols = np.where(array > 40)
    return array[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def _wrap(text: str, font, width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and font.getlength(trial) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    return lines + [current]


def names() -> list[str]:
    return sorted({name for _slot, _label, _pos, catalog in SLOTS for name in catalog})


def main():
    root = TEMPLATE_DIR / FOLDER / "Names"
    fonts = {size: ImageFont.truetype(FONT_FILE, size) for size in TWO_LINE_SIZES}
    for name in names():
        folder = root / slug(name)
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        if fonts[FONT_SIZE].getlength(name) <= CELL_WIDTH:
            Image.fromarray(_mask(name, fonts[FONT_SIZE])).save(folder / "s.png")
        seen = set()
        for size, font in fonts.items():
            for width in WRAP_WIDTHS:
                lines = _wrap(name, font, width)
                if len(lines) != 2 or (size, tuple(lines)) in seen:
                    continue
                seen.add((size, tuple(lines)))
                for number, line in enumerate(lines, 1):
                    Image.fromarray(_mask(line, font)).save(folder / f"w{width}f{size}_{number}.png")
        print(f"{name}: {len(list(folder.iterdir()))} files")


if __name__ == "__main__":
    main()
