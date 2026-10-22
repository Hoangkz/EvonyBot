"""
world_mask.py — che các vùng giao diện cố định trên màn hình bản đồ thế giới trước khi OCR tên quái / boss, để OCR không đọc chữ của nút, thanh tài nguyên,
khung chat... (màn 396 x 704 của giả lập 21913).

Vùng bị che (x1, y1, x2, y2), tô một màu phẳng (màu trung bình của ảnh) để OCR không thấy chữ ở đó:
    thanh tài nguyên + ảnh đại diện (trên trái), nút event (trên phải), nhiệm vụ / bookmark / world map (dưới trái), info / liên minh / mail (dưới phải),
    nhãn khoảng cách "36Km" quanh nút về thành, và toàn bộ phần từ nút về thành trở xuống (toạ độ, khung tin nhắn).
"""
import numpy as np

SIZE = (396, 704)                                  # (rộng, cao) màn hình
EXCLUDE = {
    "thanh tài nguyên": (0, 0, 396, 48),
    "ảnh đại diện": (0, 0, 140, 100),
    "event": (318, 48, 396, 330),
    "nhiệm vụ": (0, 430, 80, 600),
    "info": (318, 430, 396, 600),
    "nút về thành và biểu tượng cạnh nó": (150, 525, 318, 600),
    "từ nút về thành trở xuống": (0, 600, 396, 704),
}


def mask_ui(screen: np.ndarray) -> np.ndarray:
    """Bản sao của `screen` (BGR, 396 x 704) với các vùng giao diện trong EXCLUDE tô phẳng màu trung bình của ảnh."""
    out = screen.copy()
    fill = screen.reshape(-1, screen.shape[-1]).mean(axis=0).astype(screen.dtype)
    for x1, y1, x2, y2 in EXCLUDE.values():
        out[y1:y2, x1:x2] = fill
    return out


def inside_excluded(x: float, y: float) -> bool:
    """Điểm (x, y) (toạ độ màn hình thật) có nằm trong vùng giao diện bị che không (dùng để bỏ kết quả OCR / khớp mẫu ở đó)."""
    return any(x1 <= x < x2 and y1 <= y < y2 for x1, y1, x2, y2 in EXCLUDE.values())
