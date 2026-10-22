"""
angles.py — nút Auto của tab Find Boss: chia đều 0..360° cho các tài khoản cùng server.
"""
from .constants import ANGLE_STEP


def split_angles(count: int) -> list[tuple[int, int]]:
    """(góc bắt đầu, góc kết thúc) của từng tài khoản trong `count` tài khoản: các cung liền nhau phủ 0..360°, ranh giới là bội của ANGLE_STEP.
    Nhiều tài khoản hơn số cung thì cung được dùng lại (tài khoản k lấy cung k % số cung)."""
    units = 360 // ANGLE_STEP
    out = []
    for k in range(count):
        lo, hi = round(k * units / count), round((k + 1) * units / count)
        if hi <= lo:
            lo, hi = k % units, k % units + 1
        out.append((lo * ANGLE_STEP, hi * ANGLE_STEP))
    return out
