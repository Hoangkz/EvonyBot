"""
city_building.py — sau khi bấm Go của nhiệm vụ cần một công trình trong thành (King's Path:
City Tax / Patrol / Heal / Refine / Black Market / Train Troop; Gather Troops: train lính):
game đưa về thành và kéo công trình của nhiệm vụ vào giữa màn hình.

Hình công trình khác nhau theo nền văn minh (MAX_CIVS loại) nên không có ảnh mẫu cố định: bot
tự học ảnh công trình và tự xếp thiết bị vào nền văn minh 1, 2, 3 ... (lưu DB, cột
devices.civilization; bot.civilization / bot.set_civilization). Ảnh học dùng chung cho mọi máy
cùng nền văn minh: %LOCALAPPDATA%\\EvonyBot\\buildings\\civ<N>\\<công trình>\\<n>.png.
Ảnh có sẵn (cắt tay: trung vị 30 khung trong 30 s, ảnh gốc ở tests/event/city_building/screens)
nằm trong Images/Event/Building/civ<N>/<công trình>/ — dùng cùng ảnh học, bot không ghi vào đây.

Flow (tap_building rồi remember_building):
1. Tìm ảnh học của công trình ở vùng giữa (tối đa BUILDING_TIMEOUT giây): máy đã biết nền văn
   minh -> chỉ ảnh của nền văn minh đó; chưa biết -> ảnh của mọi nền văn minh (khớp civ N thì
   gán máy vào civ N) và ảnh tạm của máy (pending). Thấy -> bấm giữa, làm tiếp các bước sau.
2. Không thấy (hoặc chưa có ảnh): chờ camera đứng yên, GIỮ LEARN_FRAMES ảnh màn hình -> bấm giữa.
   Người gọi kiểm tra menu công trình: hiện đúng icon (Tax / Train / Heal ...) thì gọi
   remember_building -> cắt vùng ít thay đổi nhất của công trình (stable_crop) và lưu:
   - máy đã biết nền văn minh N: vào civ N;
   - chưa biết, chưa có nền văn minh nào: tạo civ 1, gán máy;
   - chưa biết, có nền văn minh đã học công trình này mà không khớp: nền văn minh mới (số kế
     tiếp, tối đa MAX_CIVS), gán máy;
   - chưa biết, chưa nền văn minh nào học công trình này: chưa xếp được -> lưu tạm theo máy
     (pending\\<serial>), chuyển vào civ N khi máy được gán.
   Sai icon thì không lưu gì. Mỗi công trình giữ tối đa MAX_SAMPLES ảnh (đầy thì thay ảnh cũ nhất).
"""
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from ...context.templates import TEMPLATE_DIR

MARKET = "market"                # Chợ: City Tax, Black Market
HOSPITAL = "hospital"            # Bệnh viện: Heal
FORGE = "forge"                  # Lò rèn: Refine
WALLS = "walls"                  # Tường thành: Patrol
BARRACKS = "barracks"            # Doanh trại: lính bộ
STABLES = "stables"              # Chuồng ngựa: lính kỵ
ARCHER_CAMP = "archer_camp"      # Trại cung: lính xa
WORKSHOP = "workshop"            # Xưởng: xe công thành
DEFENSE_FORCE = "defense_force"  # Công trình làm bẫy (Defense Force)
ACADEMY = "academy"              # Học viện (Daily: Resource Collecting -> Collection)
SHRINE = "shrine"                # Đền thờ (Daily: Offering)
KEEP = "keep"                    # Thành chính (Daily: Gold Levy)
PASTURE = "pasture"              # Pasture
ART_HALL = "art_hall"            # Art Hall
BATTLEFIELD = "battlefield"      # Battlefield
# King's Path Train Troop: game kéo tới công trình lính nào cũng được -> học vào TROOP, tìm
# trong mọi công trình lính (ảnh Gather Troops đã học cũng dùng được).
TROOP = "troop"
TROOP_BUILDINGS = (BARRACKS, ARCHER_CAMP, STABLES, WORKSHOP)

# Thư mục ảnh học (cạnh evonybot.db, xem database.DATA_DIR). Test đổi biến này sang thư mục tạm.
LEARNED_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EvonyBot" / "buildings"
# Ảnh có sẵn trong repo (đọc thêm, không ghi).
BUNDLED_DIR = TEMPLATE_DIR / "Event" / "Building"
PENDING = "pending"
MAX_CIVS = 7
MAX_SAMPLES = 3

CENTER = (50, 50)                    # % màn hình: bấm giữa
# Ảnh mẫu = khung LỚN NHẤT mà gần như mọi pixel đứng yên qua LEARN_FRAMES khung (pixel "đứng yên":
# độ lệch chuẩn theo thời gian < STILL_STD mức xám; khung chứa tối đa MOVING_STEPS[i] pixel dao
# động, nới dần khi không có khung nào), không nhỏ hơn LEARN_MIN_SIZE; lấy trung vị các khung. Cỡ
# khung do công trình quyết định (Academy civ 1: 160x56; civ 4 chỉ mảng mái 48x32 vì sân có lính
# đi lại; Chợ: 40x28). Chỉ xét trong LEARN_AREA (% màn hình; 396x704: x 118 .. 278, y 318 .. 374):
# - trên: thanh thời gian + chữ khi nâng cấp / train / heal / nghiên cứu (Academy civ 1 y 282 ..
#   306, civ 4 chữ "Adv Siege Machine Armor" tới y 315; Barracks 276 .. 304; Hospital 252 .. 276),
#   bong bóng icon, búa event;
# - dưới: huy hiệu số cấp ở chân công trình (y >= 378, đổi khi nâng cấp);
# - ngang: trên thân công trình, không lấn ra nền đất / hàng rào (khác nhau giữa các thành).
LEARN_AREA = (29.8, 45.2, 70.2, 53.1)   # % màn hình: (x0, y0, x1, y1)
LEARN_MIN_SIZE = (10.1, 3.6)            # % màn hình: rộng, cao tối thiểu (40x25 px)
LEARN_FRAMES = 5                        # số khung chụp khi học (BUILDING_INTERVAL giây / khung)
STILL_STD = 2.0
MOVING_STEPS = (0.02, 0.05, 0.10, 0.20, 0.35)
BUILDING_REGION = (15, 25, 85, 70)      # % màn hình: vùng tìm ảnh học
# Ngưỡng tốt nhất đo trên ảnh mẫu (Academy civ 1-4, Shrine, Market civ 1; 30 khung / 30 s) với 403
# ảnh tests: khớp đúng thấp nhất 0,925 (Academy civ 1 đang nghiên cứu, mẫu chụp lúc rảnh), khớp nhầm
# cao nhất 0,612 (mẫu mái 48x32 của Academy civ 4) -> giữa hai mức, cách mỗi bên 0,157.
BUILDING_THRESHOLD = 0.77
BUILDING_TIMEOUT = 10   # giây chờ tối đa thấy ảnh học / camera đứng yên sau Go
BUILDING_INTERVAL = 1   # giây giữa hai lần chụp khi chờ
SETTLED_THRESHOLD = 0.9  # vùng giữa của hai ảnh liên tiếp giống nhau cỡ này = camera đứng yên


@dataclass
class BuildingTap:
    """Kết quả tap_building: đưa cho remember_building sau khi kiểm tra menu."""
    building: str          # công trình sẽ học (thư mục lưu)
    frames: list           # các ảnh màn hình (camera đứng yên) ngay trước khi bấm giữa
    known: bool            # True: đã thấy ảnh học trước khi bấm (không cần học lại)


# ---- thư mục ảnh học ------------------------------------------------------------------
def _civ_dir(civ: int) -> Path:
    return LEARNED_DIR / f"civ{civ}"


def _pending_dir(bot) -> Path:
    return LEARNED_DIR / PENDING / str(bot.serial).replace(":", "_")


def _known_civs() -> list[int]:
    """Các nền văn minh đã có thư mục ảnh (có sẵn hoặc đã học), tăng dần."""
    return [civ for civ in range(1, MAX_CIVS + 1)
            if _civ_dir(civ).is_dir() or (BUNDLED_DIR / f"civ{civ}").is_dir()]


def _samples(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.png")) if folder.is_dir() else []


def _civ_samples(civ: int, building: str) -> list[Path]:
    """Ảnh có sẵn rồi ảnh đã học của `building` ở nền văn minh `civ`."""
    return _samples(BUNDLED_DIR / f"civ{civ}" / building) + _samples(_civ_dir(civ) / building)


def _load(path: Path):
    return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)


def _candidates(bot, buildings) -> list[tuple[int | None, np.ndarray]]:
    """[(nền văn minh của ảnh, ảnh)] để tìm: máy đã biết nền văn minh -> chỉ ảnh của nó; chưa
    biết -> ảnh của mọi nền văn minh và ảnh tạm của máy (nền văn minh None)."""
    civ = getattr(bot, "civilization", None)
    paths = []
    for owner in ([civ] if civ else _known_civs()):
        paths += [(owner, path) for name in buildings for path in _civ_samples(owner, name)]
    if not civ:
        paths += [(None, path) for name in buildings for path in _samples(_pending_dir(bot) / name)]
    found = []
    for owner, path in paths:
        image = _load(path)
        if image is not None:
            found.append((owner, image))
    return found


def _assign(bot, name: str, civ: int):
    """Gán máy vào nền văn minh `civ` (lưu DB qua bot.set_civilization) và chuyển ảnh tạm của
    máy vào civ đó."""
    bot.set_civilization(civ)
    bot.record(f"{name}: civilization {civ}")
    pending = _pending_dir(bot)
    if not pending.is_dir():
        return
    for folder in pending.iterdir():
        for path in _samples(folder):
            _save(_civ_dir(civ) / folder.name, _load(path))
    shutil.rmtree(pending, ignore_errors=True)


def _save(folder: Path, image):
    """Lưu `image` vào `folder`, giữ tối đa MAX_SAMPLES ảnh (xoá ảnh cũ nhất)."""
    if image is None:
        return
    folder.mkdir(parents=True, exist_ok=True)
    old = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime)
    for path in old[:max(0, len(old) - MAX_SAMPLES + 1)]:
        path.unlink()
    ok, data = cv2.imencode(".png", image)
    if ok:
        data.tofile(str(folder / f"{time.time_ns()}.png"))


# ---- màn hình ---------------------------------------------------------------------------
def _area(shape) -> tuple[int, int, int, int]:
    """LEARN_AREA theo px: (x0, y0, x1, y1)."""
    h, w = shape[:2]
    x0, y0, x1, y1 = LEARN_AREA
    return int(w * x0 / 100), int(h * y0 / 100), int(w * x1 / 100), int(h * y1 / 100)


def _center(screen: np.ndarray) -> np.ndarray:
    """Vùng LEARN_AREA: so hai ảnh liên tiếp xem camera đứng yên chưa."""
    x0, y0, x1, y1 = _area(screen.shape)
    return screen[y0:y1, x0:x1]


def _largest(moving: np.ndarray, min_w: int, min_h: int, limit: float):
    """Khung lớn nhất (>= min_w x min_h) trong `moving` (1 = pixel dao động) có tỉ lệ pixel dao
    động <= `limit`: (x, y, rộng, cao) trong `moving`, hoặc None."""
    integral = cv2.integral(moving)
    h_max, w_max = moving.shape
    best = None
    for bh in range(h_max, min_h - 1, -2):
        for bw in range(w_max, min_w - 1, -4):
            if best is not None and bw * bh <= best[2] * best[3]:
                continue
            for y in range(0, h_max - bh + 1, 2):
                row = (integral[y + bh, bw:] - integral[y, bw:]
                       - integral[y + bh, :w_max - bw + 1] + integral[y, :w_max - bw + 1])
                ok = np.flatnonzero(row <= limit * bw * bh)
                if ok.size:
                    best = (int(ok[0]), y, bw, bh)
                    break
    return best


def stable_window(frames: list) -> tuple[int, int, int, int]:
    """(x, y, rộng, cao) px của khung lớn nhất trong LEARN_AREA mà gần như mọi pixel đứng yên qua
    `frames` (cùng góc nhìn), xem LEARN_AREA / MOVING_STEPS."""
    x0, y0, x1, y1 = _area(frames[0].shape)
    h, w = frames[0].shape[:2]
    min_w, min_h = int(w * LEARN_MIN_SIZE[0] / 100), int(h * LEARN_MIN_SIZE[1] / 100)
    gray = np.stack([cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
                     for f in frames])
    moving = (gray.std(0) >= STILL_STD).astype(np.float32)
    for limit in MOVING_STEPS:
        found = _largest(moving, min_w, min_h, limit)
        if found is not None:
            x, y, bw, bh = found
            return x0 + x, y0 + y, bw, bh
    return x0, y0, x1 - x0, y1 - y0


def stable_crop(frames: list) -> np.ndarray:
    """Ảnh mẫu từ `frames`: trung vị các khung tại stable_window."""
    x, y, bw, bh = stable_window(frames)
    return np.median(np.stack([f[y:y + bh, x:x + bw] for f in frames]), 0).astype(np.uint8)


def _find_known(bot, candidates):
    """Chụp liên tục tới khi thấy một ảnh học (tối đa BUILDING_TIMEOUT giây). Trả (ảnh màn hình,
    nền văn minh của ảnh khớp, tâm chỗ khớp), hoặc (None, None, None). Nhiều ảnh cùng khớp thì lấy
    chỗ khớp cao nhất."""
    elapsed = 0.0
    while True:
        screen = bot.screenshot()
        best = None
        for owner, image in candidates:
            score, pos = bot.best_match(image, screen=screen, region=BUILDING_REGION)
            if pos is not None and score >= BUILDING_THRESHOLD and (best is None or score > best[0]):
                best = (score, owner, pos)
        if best is not None:
            return screen, best[1], best[2]
        if elapsed >= BUILDING_TIMEOUT:
            return None, None, None
        bot.sleep(BUILDING_INTERVAL)
        elapsed += BUILDING_INTERVAL


def _settled_frames(bot) -> list:
    """Chờ camera đứng yên (vùng giữa của hai lần chụp liên tiếp giống nhau, tối đa
    BUILDING_TIMEOUT giây) rồi trả LEARN_FRAMES ảnh liên tiếp (cách nhau BUILDING_INTERVAL giây)."""
    screen = bot.screenshot()
    elapsed = 0.0
    while elapsed < BUILDING_TIMEOUT:
        bot.sleep(BUILDING_INTERVAL)
        elapsed += BUILDING_INTERVAL
        nxt = bot.screenshot()
        score = cv2.matchTemplate(_center(nxt), _center(screen), cv2.TM_CCOEFF_NORMED).max()
        screen = nxt
        if score >= SETTLED_THRESHOLD:
            break
    frames = [screen]
    while len(frames) < LEARN_FRAMES:
        bot.sleep(BUILDING_INTERVAL)
        frames.append(bot.screenshot())
    return frames


# ---- API --------------------------------------------------------------------------------
def tap_building(bot, name: str, building: str, delay: float, also=()) -> BuildingTap:
    """Sau Go: tìm ảnh học của `building` (và các công trình `also`). Thấy -> bấm vào chỗ khớp
    (công trình có thể không nằm giữa, VD camera bị lướt lệch); không thấy -> bấm giữa màn hình
    để thử. Chờ `delay` giây. Trả BuildingTap để người gọi kiểm tra menu xong thì gọi
    remember_building."""
    candidates = _candidates(bot, (building, *also))
    screen, owner, pos = _find_known(bot, candidates) if candidates else (None, None, None)
    if screen is not None:
        bot.log(f"{name}: building recognized at {pos}, tapping it")
        if owner is not None and not getattr(bot, "civilization", None):
            _assign(bot, name, owner)
        bot.tap(*pos, delay=delay)
        return BuildingTap(building, [screen], True)
    if candidates:
        bot.log(f"{name}: learned building not found, tapping center to check")
    else:
        bot.log(f"{name}: building not learned yet, tapping center to check")
    frames = _settled_frames(bot)
    bot.tap_percent(*CENTER, delay=delay)
    return BuildingTap(building, frames, False)


def remember_building(bot, name: str, tap: BuildingTap | None):
    """Menu công trình đã hiện đúng icon sau `tap`: chưa nhận ra công trình trước khi bấm thì
    cắt công trình từ ảnh đã giữ và lưu (xếp nền văn minh: xem đầu file)."""
    if tap is None or tap.known:
        return
    image = stable_crop(tap.frames)
    try:
        civ = getattr(bot, "civilization", None)
        if not civ:
            known = _known_civs()
            if known and not any(_civ_samples(c, tap.building) for c in known):
                # Chưa nền văn minh nào học công trình này: chưa biết máy thuộc civ nào.
                _save(_pending_dir(bot) / tap.building, image)
                bot.log(f"{name}: learned building image ({tap.building}), civilization not known yet")
                return
            free = [c for c in range(1, MAX_CIVS + 1) if c not in known]
            if not free:
                bot.record(f"{name}: building matches none of {MAX_CIVS} civilizations, not saved")
                return
            civ = free[0]
            _assign(bot, name, civ)
        _save(_civ_dir(civ) / tap.building, image)
        bot.log(f"{name}: learned building image ({tap.building}, civilization {civ})")
    except OSError as e:
        bot.log(f"{name}: cannot save building image: {e}")
