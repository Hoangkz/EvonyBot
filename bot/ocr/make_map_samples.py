"""
make_map_samples.py — sinh mẫu chữ cho nhãn tên quái / boss trên bản đồ thế giới (font "MapName", đọc bằng read_map_label.py).

Nhãn dùng font Arial của game (file HeroDefault.ttf nằm trong gói tài nguyên của game; KHÔNG lưu font vào dự án), chữ nhỏ (~11 px) bị Unity vẽ lệch nửa điểm ảnh nên
mỗi chữ được vẽ ở độ phân giải cao rồi thu nhỏ theo 4 độ lệch ngang (EM, SX, SY dò từ ảnh thật: khớp 0.87-0.89). Chạy một lần, cần đường dẫn font:

    python -m bot.ocr.make_map_samples C:/duong/dan/HeroDefault.ttf [MapName | PopupName | PopupName2]

Ra Images/OCR/MapName/<nhãn>_<n>.png (ảnh xám 0-255, cao đúng một dòng chữ, rộng đúng một chữ). Nhãn: chữ thường như nó; chữ HOA là "up" + chữ ("upB_1.png",
vì tên file Windows không phân biệt hoa thường); "(" = "lp", ")" = "rp".
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ._digits import OCR_DIR

FONT = "MapName"
PRESETS = {"MapName": (12, 0.9, 0.92),       # nhãn tên trên bản đồ: cỡ chữ vẽ, co ngang, co dọc (dò từ ảnh thật)
           "PopupName": (23, 0.95, 0.95),    # tên boss trong cửa sổ thông tin sau khi bấm Attack (read_boss_popup.py)
           "PopupName2": (14, 1.05, 1.05)}   # tên boss dài xuống hai dòng trong cửa sổ đó: game thu chữ nhỏ lại (khoảng 2/3)
SUPER = 8                           # vẽ to gấp chừng này lần rồi thu nhỏ
PHASES = 4                          # số độ lệch ngang dưới một điểm ảnh
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz()"


def file_label(ch: str) -> str:
    return {"(": "lp", ")": "rp"}.get(ch) or ("up" + ch if ch.isupper() else ch)


def render(font: ImageFont.FreeTypeFont, ch: str, em: float, sx: float, sy: float) -> list[np.ndarray]:
    """Các ảnh xám (0-1) của chữ `ch` ứng với PHASES độ lệch ngang, cao đúng một dòng (từ đỉnh chữ cao tới đáy chữ có đuôi)."""
    ascent, descent = font.getmetrics()
    image = Image.new("L", (int(em * SUPER * 2), ascent + descent + 20), 0)
    ImageDraw.Draw(image).text((10, 10), ch, font=font, fill=255)
    big = np.array(image).astype(np.float32) / 255
    cols = np.flatnonzero(big.max(axis=0) > 0.05)
    big = big[10:10 + ascent + descent, cols[0]:cols[-1] + 1]
    h = max(1, round(big.shape[0] / SUPER * sy * PHASES))
    w = max(1, round(big.shape[1] / SUPER * sx * PHASES))
    big = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
    out = []
    for dx in range(PHASES):
        padded = np.pad(big, ((0, (-h) % PHASES), (dx, (-(w + dx)) % PHASES)))
        ph, pw = padded.shape
        out.append(padded.reshape(ph // PHASES, PHASES, pw // PHASES, PHASES).mean(axis=(1, 3)))
    return out


def main(font_path: str, name: str = FONT):
    em, sx, sy = PRESETS[name]
    font = ImageFont.truetype(font_path, em * SUPER)
    folder = OCR_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    for ch in CHARS:
        for n, image in enumerate(render(font, ch, em, sx, sy), 1):
            cv2.imwrite(str(folder / f"{file_label(ch)}_{n}.png"), (np.clip(image, 0, 1) * 255).astype(np.uint8))
    print(f"đã sinh {len(CHARS) * PHASES} mẫu vào {folder}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
