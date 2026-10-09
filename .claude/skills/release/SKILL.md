---
name: release
description: Phát hành phiên bản mới của EvonyBot — tăng version.py, build installer (Nuitka + Inno Setup) và tạo GitHub Release để auto-updater nhận. Dùng khi người dùng nói "release", "build installer", "đóng gói", "lên version", "bump version", "phát hành bản mới".
disable-model-invocation: true
---

# Release EvonyBot

Chuỗi phát hành: `version.py` → [installer/build.ps1](../../../installer/build.ps1) → `dist/EvonyBot-Setup-<ver>.exe` → GitHub Release trên `Hoangkz/EvonyBot` → [updater.py](../../../updater.py) trên máy người dùng thấy bản mới.

## 1. Kiểm tra trước
- `git status` sạch (hoặc người dùng xác nhận những gì đang thay đổi sẽ đi vào bản build — build lấy code **trong working tree**, không phải commit).
- Test pass: `.\venv\Scripts\python.exe -m unittest discover -s tests -v`
- Import được toàn bộ app: `.\venv\Scripts\python.exe -c "import main, database, updater, bot.activities, ui.tabs"`

## 2. Tăng version
Sửa `__version__` trong [version.py](../../../version.py) theo semver (`X.Y.Z`). Hỏi người dùng muốn tăng patch/minor/major nếu chưa rõ. Updater so tag release với giá trị này — version phải **lớn hơn** bản đang phát hành.

## 3. Build
```powershell
venv\Scripts\poe build
# hoặc: powershell -NoProfile -ExecutionPolicy Bypass -File installer/build.ps1
```
Chạy lâu (Nuitka compile vài phút) → chạy nền với timeout dài. Yêu cầu: venv Python 3.12 64-bit có `nuitka`, MSVC Build Tools (hoặc Nuitka tự tải MinGW), Inno Setup 6. Lỗi thường gặp:
- `Inno Setup 6 (ISCC.exe) not found` → cần cài Inno Setup.
- `venv is Python X but the embedded runtime is 3.12` → venv sai phiên bản.
- `Nuitka compile failed` → đọc output Nuitka; thường là lỗi import/cú pháp trong code app.
- Thêm file dữ liệu mới ngoài `Images/`, `ui/assets/` (VD ảnh) → phải thêm `Copy-Item` trong build.ps1, không thì bản cài sẽ thiếu. Dữ liệu dạng `.py` (`boss.py`, `event.py`, `priority.py`, ...) được Nuitka compile cùng code, không cần copy.

Kết quả: `dist\EvonyBot-Setup-<version>.exe`. `venv\Scripts\poe clean` xoá output build (giữ zip Python embed đã cache).

## 4. Commit + GitHub Release
Chỉ làm khi người dùng đồng ý (đây là thao tác public, người dùng cuối sẽ tự update):
```powershell
git add version.py
git commit -m "Release v<version>"
git tag v<version>
git push; git push origin v<version>
```
Tạo release với tag `v<version>` và **đính kèm file .exe** (updater lấy asset đầu tiên có đuôi `.exe`; repo phải public):
- Có `gh`: `gh release create v<version> dist/EvonyBot-Setup-<version>.exe --title "v<version>" --notes "..."`
- Không có `gh` (máy hiện chưa cài): hướng dẫn người dùng tạo release trên github.com/Hoangkz/EvonyBot/releases/new và upload file .exe.

Release notes: tóm tắt thay đổi từ `git log <tag trước>..HEAD` (commit message trong repo thường chỉ là "a"/"test", nên đọc diff để viết).
