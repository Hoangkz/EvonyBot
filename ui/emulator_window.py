"""
emulator_window.py — phóng to / thu lại cửa sổ giả lập MEmu của một thiết bị (nút Maximize ở tab Initialization).

Serial ADB của MEmu là 127.0.0.1:<21503 + 10 * số máy> (VD 21913 -> máy 41). `memuc listvms` (cạnh MEmu.exe) in mỗi
máy một dòng "số máy,tên,handle cửa sổ,đang chạy,pid" -> lấy handle rồi phóng to bằng WinAPI. Chỉ đổi cỡ cửa sổ,
độ phân giải Android không đổi nên bot vẫn chạy bình thường.
"""
import ctypes
import os
import subprocess
from ctypes import wintypes

MEMU_BASE_PORT = 21503
MEMU_PORT_STEP = 10
MEMU_DIRS = [r"C:\Program Files\Microvirt\MEmu", r"D:\Program Files\Microvirt\MEmu"]
SW_RESTORE = 9


class EmulatorWindowError(Exception):
    """Không tìm được cửa sổ giả lập của thiết bị (lý do trong nội dung, hiện lên cho người dùng)."""


def memu_index(serial: str) -> int | None:
    """Số máy MEmu từ serial ADB "127.0.0.1:21913" -> 41; không phải cổng MEmu thì None."""
    try:
        port = int(serial.rsplit(":", 1)[1])
    except (IndexError, ValueError):
        return None
    index, rest = divmod(port - MEMU_BASE_PORT, MEMU_PORT_STEP)
    return index if index >= 0 and rest == 0 else None


def _memu_dirs() -> list[str]:
    """Thư mục cài MEmu: lấy từ cửa sổ MEmu.exe đang mở (cài ở ổ nào cũng thấy), rồi tới các chỗ cài mặc định."""
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    found: list[str] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(0x1000, False, pid.value)   # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)) \
                    and os.path.basename(buf.value).lower() == "memu.exe":
                folder = os.path.dirname(buf.value)
                if folder not in found:
                    found.append(folder)
            kernel32.CloseHandle(handle)
        return True

    user32.EnumWindows(visit, 0)
    return found + [d for d in MEMU_DIRS if d not in found]


def find_window(serial: str) -> int:
    """Handle cửa sổ MEmu của thiết bị `serial`; không tìm được thì EmulatorWindowError."""
    index = memu_index(serial)
    if index is None:
        raise EmulatorWindowError(f"{serial} is not a MEmu device")
    memuc = next((p for d in _memu_dirs() if os.path.isfile(p := os.path.join(d, "memuc.exe"))), None)
    if memuc is None:
        raise EmulatorWindowError("memuc.exe not found (MEmu is not installed?)")
    out = subprocess.run([memuc, "listvms"], capture_output=True, text=True, timeout=10,
                         creationflags=subprocess.CREATE_NO_WINDOW).stdout
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) >= 3 and parts[0].strip() == str(index):
            hwnd = int(parts[-3]) if parts[-3].strip().isdigit() else 0
            if hwnd and ctypes.windll.user32.IsWindow(hwnd):
                return hwnd
            raise EmulatorWindowError(f"MEmu {index} window is not open")
    raise EmulatorWindowError(f"MEmu {index} not found")


class _MonitorInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD)]


# {hwnd: (x, y, w, h)} vị trí cửa sổ trước khi phóng to, để bấm lại thì trả về đúng chỗ cũ.
_saved_rects: dict[int, tuple[int, int, int, int]] = {}


def _rect(r: wintypes.RECT) -> tuple[int, int, int, int]:
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def toggle_maximize(serial: str):
    """Phóng to cửa sổ giả lập vừa vùng làm việc của màn hình nó đang nằm (không đè taskbar: cửa sổ MEmu không viền nên
    SW_MAXIMIZE phủ cả taskbar); đang phóng to thì trả về vị trí / cỡ cũ. Rồi đưa cửa sổ lên trước."""
    user32 = ctypes.windll.user32
    hwnd = find_window(serial)
    if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    current = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(current))
    info = _MonitorInfo()
    info.cbSize = ctypes.sizeof(_MonitorInfo)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, 2), ctypes.byref(info))   # MONITOR_DEFAULTTONEAREST
    work = _rect(info.rcWork)
    if _rect(current) == work and hwnd in _saved_rects:
        user32.MoveWindow(hwnd, *_saved_rects.pop(hwnd), True)
    else:
        _saved_rects[hwnd] = _rect(current)
        user32.MoveWindow(hwnd, *work, True)
    user32.SetForegroundWindow(hwnd)
