"""
make_caption_samples.py — sinh mẫu chữ cho dòng chữ vàng dưới icon ở hàng nút đáy màn thành ("Valuable Event", "Empire Depot", "Adventure"...), font "Caption",
đọc bằng find_valuable_event.py (qua read_map_label.read).

Không có file font của game nên dùng Segoe UI của Windows: gần nhất trong các font hệ thống (khớp cả từ 0.88-0.89 trên ảnh thật, Arial chỉ 0.70). Cách vẽ giống
make_map_samples.py (vẽ to, thu nhỏ theo 4 độ lệch ngang). Chạy một lần:

    python -m bot.ocr.make_caption_samples [C:/Windows/Fonts/segoeui.ttf]

Ra Images/OCR/Caption/<nhãn>_<n>.png, đặt tên như make_map_samples.
"""
import sys

import cv2
import numpy as np
from PIL import ImageFont

from ._digits import OCR_DIR
from .make_map_samples import CHARS, PHASES, SUPER, file_label, render

FONT = "Caption"
FONT_PATH = "C:/Windows/Fonts/segoeui.ttf"
EM, SX, SY = 13, 1.05, 1.0      # cỡ chữ vẽ, co ngang, co dọc (dò từ ảnh thật rộng 396 px)


def main(font_path: str = FONT_PATH):
    font = ImageFont.truetype(font_path, EM * SUPER)
    folder = OCR_DIR / FONT
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    for ch in CHARS:
        for n, image in enumerate(render(font, ch, EM, SX, SY), 1):
            cv2.imwrite(str(folder / f"{file_label(ch)}_{n}.png"), (np.clip(image, 0, 1) * 255).astype(np.uint8))
    print(f"đã sinh {len(CHARS) * PHASES} mẫu vào {folder}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
