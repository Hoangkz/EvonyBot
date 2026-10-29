"""
find_bosses.py — tìm boss trên một màn hình bản đồ thế giới (396 x 704): lọc màu cam sáng của vòng sáng dưới chân boss, rồi chỉ đọc các dòng nhãn nằm trong vùng từ vòng sáng đi xuống,
khớp tên với danh mục trong ui/tabs/boss.py.

    boss = find_bosses(screen)       # screen = ảnh BGR 396 x 704
    # [{"name": "Zombie", "level": 1, "tier": None, "tag": True, "text": "(Boss) Zombie", "pos": (x, y), "active": False, "score": 0.77, "region": (x1, y1, x2, y2)}, ...]

Các bước (nhanh -> chậm, bước sau chỉ chạy khi bước trước có dấu hiệu):
    1. Che các vùng giao diện cố định (world_mask.mask_ui), đếm điểm cam sáng (HSV); dưới GATE_MIN điểm thì không có boss -> trả [] ngay (khoảng 10 ms).
    2. Gộp điểm cam thành vài vùng, mỗi vùng mở rộng xuống dưới thành vùng nhãn (nhãn nằm ngay dưới chân boss).
    3. Tìm các dòng chữ trên màn hình (read_map_label.lines), giữ dòng nằm trong vùng nhãn, đọc từng dòng bằng mẫu chữ (read_map_label.read) so với danh sách các nhãn có thể có:
       "(Boss) <tên>" cho boss trùm, "<tầng> <tên>" cho boss sự kiện (tầng lấy từ boss.py); tên trơn là quái thường, không nhận. Boss sự kiện có thể hiện tên khác danh mục (Knight Bayard -> "Bayar Knight").
`name` = None nghĩa là có vòng sáng (nhiều khả năng là boss) nhưng không đọc ra tên trong danh mục: nên căn vị trí đó vào giữa màn rồi đọc lại.
`level`: boss trùm đọc từ huy hiệu cấp độ bên trái nhãn (read_map_level), boss sự kiện suy ra từ tầng (boss.py); None nếu không đọc được.
Nhãn bị cắt ở rìa màn hình / vùng giao diện chỉ đọc được một phần (read_map_label.read_partial, read_fragment): `partial` = True, `candidates` = các tên còn khả dĩ; `confirm` = True cho boss cần bấm vào xem lại.
"""
import threading

import cv2
import numpy as np

from . import read_boss_popup, read_map_label, read_map_level, world_mask

GLOW_LOW, GLOW_HIGH = (8, 170, 210), (20, 255, 255)      # HSV (OpenCV) của cam sáng ở vòng sáng
GATE_MIN = 60                                            # ít hơn chừng này điểm cam sáng (sau khi che giao diện) thì coi là không có boss (boss trùm 250-330 điểm, boss Event vòng yếu 70-100 điểm, khung không boss trung vị 26)
BLOB_MIN = 20                                            # vùng cam nhỏ hơn chừng này điểm: bỏ
EDGE_MAX_CANDIDATES = 2                                  # nhãn sát rìa không có vùng sáng: đoạn đọc được khớp quá nhiều tên (VD "Juni" -> mọi "Junior …") thì quá mơ hồ, bỏ
EDGE_GLOW_MIN = 8                                        # nhãn bị cắt sát rìa (vòng sáng dưới chân boss có thể nằm ngoài màn hình, không thành vùng): cần ít nhất chừng này điểm cam sáng trên nhãn (nhãn quái thường bị cắt đọc nhầm thành boss thường có 0-3)
MAX_REGIONS = 5                                          # tối đa số vùng nhãn mỗi màn
NAME_ALIASES = {"Knight Bayard": ["Bayar Knight"]}       # tên hiện trên nhãn khác tên trong boss.py
# Tên quái thường hay gặp trên bản đồ: đưa vào danh sách nhãn làm "mồi" (không phải boss). Nhãn bị cắt của quái thường (VD "…enegade") dễ bị đọc nhầm thành đuôi tên boss ("…ungandr");
# có mồi khớp hơn thì bộ đọc chọn mồi và bỏ nhãn đó.
DECOYS = ["Renegade", "Bloody Gladiator", "Invader", "Barbarian", "Bandit", "Robber", "Crafty Ranger", "Hypocritical Knight", "Ferocious Knight", "Dark Warrior", "Mysterious Witch",
          "Evil Knight", "Teutonic Berserker", "Scythian Knight", "Inferno Warrior", "Wraith Hunter", "Murderous Warrior", "Golden Skull Cup Warrior", "Monarch", "Skeleton Warrior"]
_caches: dict = {}                                       # {khoá lựa chọn: danh mục đã dựng}
_local = threading.local()                               # lựa chọn boss của luồng đang chạy (mỗi thiết bị một luồng): {tên boss: {các cấp được chọn}}; None = dùng cờ "active" của boss.py


def set_selection(selected: list[dict] | None):
    """Chọn boss cần tìm: `selected` = [{"name", "levels": [cấp, ...]}, ...] (cùng dạng "selected_bosses" của tab Join Monster War / Find Boss); boss không có cấp thì chỉ cần có tên.
    None: về lại cờ "active" của boss.py. Ảnh hưởng "active" của find_bosses / read_popup (boss_scan chỉ xử lý boss active)."""
    _local.selection = None if selected is None else {boss["name"]: set(boss.get("levels") or []) for boss in selected}


def _selection() -> dict | None:
    return getattr(_local, "selection", None)


def _state() -> dict:
    """Danh mục đã dựng cho lựa chọn boss hiện tại của luồng (nhớ lại theo lựa chọn)."""
    selection = _selection()
    return _caches.setdefault(None if selection is None else tuple(sorted((n, tuple(sorted(l))) for n, l in selection.items())), {})


def _catalog():
    """([(tên, {cấp: (tầng, đang_bật)}, đang_bật, nhóm)], {chữ trên nhãn: (tên, tầng, có (Boss))}, Lexicon của các nhãn) từ ui/tabs/boss.py, nhớ lại."""
    _cache = _state()
    if "catalog" not in _cache:
        from ui.tabs.boss import DATA
        entries, labels = [], {}
        for category in DATA["boss_categories"]:
            for boss in category["list"]:
                selection = _selection()
                if selection is None:
                    levels = {lv["level"]: (lv.get("tier"), bool(lv.get("active"))) for lv in (boss.get("levels") or [])}
                    boss_active = bool(boss.get("active"))
                else:
                    ticked = selection.get(boss["name"])
                    levels = {lv["level"]: (lv.get("tier"), ticked is not None and lv["level"] in ticked) for lv in (boss.get("levels") or [])}
                    boss_active = ticked is not None and not levels
                entries.append((boss["name"], levels, boss_active, category["label"]))
                for shown in [boss["name"]] + NAME_ALIASES.get(boss["name"], []):
                    labels[f"(Boss) {shown}"] = (boss["name"], None, True)
                    for tier, _ in levels.values():
                        if tier:
                            labels[f"{tier.capitalize()} {shown}"] = (boss["name"], tier.lower(), False)
        names = sorted({shown for e in entries for shown in [e[0]] + NAME_ALIASES.get(e[0], [])})
        _cache["boss_names"] = set(names)
        _cache["catalog"] = (entries, labels, read_map_label.Lexicon(sorted(labels) + DECOYS, names + DECOYS))
        # Tên ở đầu cửa sổ thông tin boss: boss trùm "(Boss) <tên>", boss sự kiện "<tầng> <tên>" (có thể cả "<tên>" trơn) ({chữ: (tên, tầng)}).
        popup = {text: (name, tier) for text, (name, tier, _) in labels.items()}
        popup.update({text.removeprefix("(Boss) "): (name, tier) for text, (name, tier, _) in labels.items()})
        _cache["popup"] = (popup, read_map_label.Lexicon(sorted(popup)))
        # Tên dài xuống hai dòng ("Legendary Bayar" / "Knight"): các cách chia tại ranh giới từ ({(nửa đầu, nửa sau): tên đầy đủ}) và danh sách từng nửa.
        pairs = {}
        for text in popup:
            words = text.split()
            for i in range(1, len(words)):
                pairs[(" ".join(words[:i]), " ".join(words[i:]))] = text
        _cache["popup_halves"] = (read_map_label.Lexicon(sorted({a for a, _ in pairs})), read_map_label.Lexicon(sorted({b for _, b in pairs})), pairs)
    return _cache["catalog"]


def read_popup(screen: np.ndarray) -> dict | None:
    """Boss trong cửa sổ thông tin (sau khi bấm Attack) trên `screen`: {"name", "tier", "level", "active", "text", "score"} theo danh mục boss.py, hoặc None nếu không đọc ra tên boss
    nào trong danh mục (không phải boss cần tìm). `level` suy ra từ tầng (boss trùm: None); `active`: boss (hoặc tầng đó) đang được bật."""
    entries, _, _ = _catalog()
    _cache = _state()
    popup, lexicon = _cache["popup"]
    read = read_boss_popup.read_name(screen, lexicon, _cache["popup_halves"])
    if read is None:
        return None
    name, tier = popup[read["text"]]
    levels, boss_active = next((e[1], e[2]) for e in entries if e[0] == name)
    level = next((lv for lv, (t, _) in levels.items() if tier and t and t.lower() == tier), None)
    return {"name": name, "tier": tier, "level": level, "active": levels[level][1] if level is not None else boss_active, "text": read["text"], "score": read["mean"]}


def glow_regions(screen: np.ndarray, masked: np.ndarray | None = None) -> list[tuple[int, int, int, int]]:
    """Vùng nhãn (x1, y1, x2, y2) nằm từ các mảng cam sáng đi xuống; [] nếu ít điểm cam hơn GATE_MIN."""
    masked = world_mask.mask_ui(screen) if masked is None else masked
    mask = cv2.inRange(cv2.cvtColor(masked, cv2.COLOR_BGR2HSV), GLOW_LOW, GLOW_HIGH)
    if cv2.countNonZero(mask) < GATE_MIN:
        return []
    merged = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (37, 19)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
    h, w = mask.shape
    regions = []
    for i in range(1, count):
        x, y, bw, bh, _ = stats[i]
        sparks = int(cv2.countNonZero(mask[y:y + bh, x:x + bw]))
        if sparks < BLOB_MIN or bw < 30:
            continue
        regions.append((sparks, (max(0, x - 70), max(0, y + int(bh * 0.25)), min(w, x + bw + 110), min(h, y + bh + 40))))
    regions.sort(reverse=True)
    out: list = []
    for _, r in regions[:MAX_REGIONS]:
        for k, o in enumerate(out):                      # gộp vùng chồng nhau
            if r[0] < o[2] and o[0] < r[2] and r[1] < o[3] and o[1] < r[3]:
                out[k] = (min(r[0], o[0]), min(r[1], o[1]), max(r[2], o[2]), max(r[3], o[3]))
                break
        else:
            out.append(r)
    return [tuple(int(v) for v in r) for r in out]


def glow_points(screen: np.ndarray, masked: np.ndarray | None = None) -> list[tuple[int, int]]:
    """Điểm của từng vòng sáng boss: (trung bình x, y lớn nhất) của các điểm cam sáng thuộc vòng đó, tức giữa đáy vòng sáng (khác `pos` của vùng nhãn nằm
    dưới thân boss). Cùng bộ lọc với glow_regions; [] nếu ít điểm cam hơn GATE_MIN."""
    masked = world_mask.mask_ui(screen) if masked is None else masked
    mask = cv2.inRange(cv2.cvtColor(masked, cv2.COLOR_BGR2HSV), GLOW_LOW, GLOW_HIGH)
    if cv2.countNonZero(mask) < GATE_MIN:
        return []
    merged = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (37, 19)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
    points = []
    for i in range(1, count):
        if stats[i][2] < 30:
            continue
        ys, xs = np.nonzero((labels == i) & (mask > 0))
        if len(ys) < BLOB_MIN:
            continue
        points.append((int(round(xs.mean())), int(ys.max())))
    return points


def _entry(text: str, mean: float, box, region, badge_level: int | None) -> dict:
    """Kết quả cho nhãn đã đọc `text` (một nhãn trong danh sách)."""
    entries, labels, _ = _catalog()
    name, tier, tag = labels[text]
    levels, boss_active = next((e[1], e[2]) for e in entries if e[0] == name)
    level = next((lv for lv, (t, _) in levels.items() if tier and t and t.lower() == tier), None)
    active = levels[level][1] if level is not None else boss_active
    level = level if level is not None else badge_level
    x, y, w, _ = box
    return {"name": name, "level": level, "tier": tier, "tag": tag, "text": text, "active": active, "score": mean,
            "pos": (int(x + w // 2), int(y)), "region": region}


def _partial_entry(part: dict, lexicon, box, region, badge_level: int | None) -> dict | None:
    """Kết quả cho nhãn bị cắt đọc được đoạn `part`: biết tên nếu mọi nhãn chứa đoạn đó là cùng một boss (name = None, kèm "candidates" nếu còn nhiều boss).
    `partial` = True; `tier` / `tag` chỉ có khi mọi nhãn khả dĩ giống nhau; `active` = True nếu có khả năng là boss đang bật (không bỏ sót)."""
    entries, labels, _ = _catalog()
    found = read_map_label.candidates(lexicon, part)
    if part["side"] is None:                               # đoạn nằm giữa tên: chỉ biết tên, không biết tầng / (Boss)
        canonical = {alias: name for name, aliases in NAME_ALIASES.items() for alias in aliases}
        options = [(canonical.get(n, n), None, False) for n in found if n in _state()["boss_names"]]
        if not options or len(options) < len(found):        # đoạn nằm trong tên quái thường
            return None
    else:
        options = [labels[s] for s in found if s in labels]
        if not options or len(options) < len(found):        # có nhãn quái thường cũng khớp đoạn này (VD "…ladiator": Bloody Gladiator / Savage Tiger Gladiator): quá mơ hồ, bỏ
            return None
    names = sorted({o[0] for o in options})
    x, y, w, _ = box
    entry = {"name": names[0] if len(names) == 1 else None, "level": badge_level, "tier": None, "tag": False, "text": part["text"], "active": False,
             "score": part["mean"], "pos": (int(x + w // 2), int(y)), "region": region, "partial": True, "candidates": names}
    if options:
        tiers, tags = {o[1] for o in options}, {o[2] for o in options}
        entry["tier"] = next(iter(tiers)) if len(tiers) == 1 else None
        entry["tag"] = next(iter(tags)) if len(tags) == 1 else False
        for name, levels, boss_active, _ in entries:
            if name in names:
                entry["active"] |= boss_active or any(a for _, a in levels.values())
    return entry


def needs_confirm(boss: dict) -> bool:
    """Boss này chưa chắc tên / cấp (nhãn bị cắt chỉ đọc được một phần, hoặc không có cấp): nên bấm vào tên `pos`, bấm tấn công rồi đọc lại màn đó để có đủ tên, cấp, sức mạnh, tầng."""
    return bool(boss.get("partial")) or boss["name"] is None or boss["level"] is None


def find_bosses(screen: np.ndarray) -> list[dict]:
    """Boss (và vòng sáng không đọc ra tên) trên `screen`: xem docstring đầu file. Mỗi boss có thêm `confirm` (xem needs_confirm)."""
    found = _find(screen)
    for boss in found:
        boss["confirm"] = needs_confirm(boss)
    return found


def _find(screen: np.ndarray) -> list[dict]:
    regions = glow_regions(screen)
    boxes = read_map_label.lines(screen)
    _, _, lexicon = _catalog()
    found: list[dict] = []
    done: set[int] = set()                                 # các dòng chữ đã đọc trong vùng nhãn
    for region in regions:
        x1, y1, x2, y2 = region
        named = False
        for index, box in enumerate(boxes):
            cx, cy = box[0] + box[2] // 2, box[1] + box[3] // 2
            if not (x1 <= cx <= x2 and y1 <= cy <= y2):
                continue
            done.add(index)
            entry = _read_box(screen, box, region, lexicon)
            if entry:
                found.append(entry)
                named = True
        if not named:
            found.append({"name": None, "level": None, "tier": None, "tag": False, "text": "", "active": False, "score": 0.0,
                          "pos": ((x1 + x2) // 2, (y1 + y2) // 2), "region": region})
    glow = None
    for index, box in enumerate(boxes):                    # nhãn sát rìa: vòng sáng dưới chân boss nằm ngoài màn hình nên không có vùng nhãn, vẫn đọc một phần
        if index not in done and read_map_label.edge_side(box):
            if glow is None:
                glow = cv2.inRange(cv2.cvtColor(world_mask.mask_ui(screen), cv2.COLOR_BGR2HSV), GLOW_LOW, GLOW_HIGH)
            x, y, w, _ = box
            if cv2.countNonZero(glow[max(0, y - 80):y + 2, max(0, x - 70):x + w + 70]) < EDGE_GLOW_MIN:
                continue
            entry = _read_box(screen, box, (box[0], box[1], box[0] + box[2], box[1] + box[3]), lexicon, fragments=False)     # không có vòng sáng chắc chắn: chỉ đọc đầu / cuối nhãn, không đoán từ đoạn giữa ("City" -> "Sty")
            if entry and not (entry.get("partial") and len(entry.get("candidates", [])) > EDGE_MAX_CANDIDATES):
                found.append(entry)
    return found


def _read_box(screen: np.ndarray, box, region, lexicon, fragments: bool = True) -> dict | None:
    """Kết quả cho một dòng chữ `box` (None nếu không nhận ra boss nào): nhãn thấy đủ đọc cả dòng, nhãn bị cắt (sát rìa màn hình / vùng giao diện) đọc một phần."""
    strip = read_map_label.ink(screen, box)
    side = read_map_label.edge_side(box)
    if not side:
        read = read_map_label.read(strip, lexicon)
        if read and read["text"] in _catalog()[1]:
            return _entry(read["text"], read["mean"], box, region, read_map_level.run(read_map_level.badge(screen, box)))
        return None
    # nhãn bị cắt: đọc một phần ở đầu hoặc cuối nhãn, không được thì đoạn nằm giữa tên (đọc cả dòng dễ nhầm sang tên ngắn hơn)
    part = read_map_label.read_partial(strip, lexicon, side) or (read_map_label.read_fragment(strip, lexicon) if fragments else None)
    if part:
        return _partial_entry(part, lexicon, box, region, read_map_level.run(read_map_level.badge(screen, box)))
    return None
