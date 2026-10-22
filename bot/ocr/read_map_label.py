"""
read_map_label.py — nhãn tên quái / boss trên bản đồ thế giới, VD "4 Legendary Bayar Knight" hay "1 (Boss) Zombie": chữ be kem nhỏ (~11 px, nét 1 px) trên băng tối.

Chữ quá nhỏ và dính nhau để tách từng chữ theo cột trống như read_boss_name, nên đọc kiểu khác: so MẪU TỪNG CHỮ trượt dọc dòng rồi chọn TÊN TRONG DANH SÁCH (lexicon)
khớp nhất. Mẫu ở Images/OCR/MapName/ (sinh bằng make_map_samples.py từ font của game, mỗi chữ 4 độ lệch dưới điểm ảnh):

    labels = lines(screen)                       # [(x, y, w, h)] mọi dòng chữ có thể là nhãn trên màn hình
    lexicon = Lexicon(["(Boss) Zombie", "Legendary Bayar Knight", ...])     # chữ HOA đầu từ như trong game
    found = read(ink(screen, labels[0]), lexicon)     # {"text", "mean", "min"} hoặc None

Với mỗi tên trong lexicon, quy hoạch động xếp các chữ của tên đó lần lượt dọc dòng (giữa hai chữ cách -1..2 cột, giữa hai từ 2..9 cột; cột có nét nằm ngoài chữ bị trừ điểm)
và cộng độ giống (TM_CCOEFF_NORMED) của từng chữ; các tên chung phần đầu dùng chung phép tính (cây tiền tố) và nhánh có điểm trung bình quá thấp bị cắt sớm.
Nhận tên nếu điểm trung bình >= MIN_MEAN và chữ yếu nhất >= MIN_LETTER (nhãn quái thường / chữ lạ không đạt).
"""
import cv2
import numpy as np

from . import world_mask
from ._digits import OCR_DIR, read_image

FONT = "MapName"
STRIP_H = 16            # dòng chữ cắt từ y - 2 xuống chừng này hàng (đủ chữ cao + đuôi g, y, p)
PAD_X = 3               # cột lấy thêm hai bên hộp dòng chữ (đầu / cuối chữ nhạt bị bộ dò bỏ sót)
PAD = 6                 # cột / hàng trống thêm quanh dòng khi so mẫu
INK_FROM, INK_RANGE, CREAM = 80, 120, 70      # nét chữ: (r - 80) / 120 trong 0..1, chỉ điểm be kem (g >= 0.7 r: bỏ chữ số cam trong huy hiệu)
LINE_MIN_W, LINE_MIN_H, LINE_MAX_H = 35, 7, 16    # hộp dòng chữ (đã gộp các chữ gần nhau) hợp lệ
EDGE_TOL = 10           # px: chữ bắt đầu / kết thúc cách rìa màn hình (hoặc vùng giao diện bị che) không quá chừng này coi là bị cắt (có thể còn một từ ngắn nằm ngoài)
EDGE_MIN_W, EDGE_MIN_H = 14, 5     # dòng chữ sát rìa màn hình / vùng giao diện bị che: chỉ thấy một đoạn, hộp hẹp / thấp (chỉ còn chữ không có nét cao) tới chừng này vẫn giữ
MIN_PART = 4            # đọc một phần (nhãn bị cắt ở một đầu): ít nhất chừng này chữ cái nhìn thấy được mới đoán tên
MIN_FRAG = 4            # đọc một đoạn nằm bất kỳ trong tên (VD "omb" của Zombie): ít nhất chừng này chữ cái, và chỉ nhận khi đoạn đó thuộc đúng một tên
LETTER_GAPS = (-1, 0, 1, 2)       # cột cách giữa hai chữ trong một từ (-1: hai chữ chạm nhau)
WORD_GAPS = tuple(range(2, 10))   # cột cách giữa hai từ
# Mỗi bộ mẫu chữ (thư mục Images/OCR/<font>/) có khoảng cách chữ riêng vì cỡ chữ khác nhau: nhãn nhỏ "MapName" (mặc định), tên boss lớn trong cửa sổ thông tin "PopupName" (read_boss_popup.py).
FONT_GAPS = {"MapName": (LETTER_GAPS, WORD_GAPS), "PopupName": ((-2, -1, 0, 1, 2, 3, 4), tuple(range(4, 20))), "PopupName2": ((-2, -1, 0, 1, 2, 3), tuple(range(3, 13)))}
LAMBDA = 0.12           # trừ điểm cho mỗi cột có nét nằm ngoài các chữ
BEAM = 0.5              # nhánh có điểm trung bình mỗi chữ thấp hơn mức này (từ chữ thứ 2) bị bỏ
MIN_MEAN = 0.72         # độ giống trung bình tối thiểu để nhận tên (nhãn đúng 0.74-0.92, nhãn không có trong danh sách <= 0.81)
MIN_LETTER = 0.6        # chữ giống từ mức này là chữ chắc (nhãn đúng gần như mọi chữ >= 0.6, nhãn không có trong danh sách có nhiều chữ 0.45-0.62)
MAX_WEAK = 1            # nhãn thấy đủ: tối đa chừng này chữ yếu (< MIN_LETTER, đọc là "?"), VD "Zo?bie" vẫn nhận được. Nhãn bị cắt (read_partial, read_fragment) không cho chữ yếu nào: nhãn quái thường bị cắt đọc nhầm thành boss đều có một chữ yếu (0.52-0.55), đọc đúng thì chữ kém nhất >= 0.8
MIN_STRONG = 3          # ít nhất chừng này chữ chắc
SHORT_LEN, SHORT_BONUS = 6, 0.04     # đoạn ngắn hơn SHORT_LEN chữ phải đạt điểm TB cao hơn mỗi chữ thiếu SHORT_BONUS (đoạn ngắn dễ đoán sai)
_NEG = -1e9
_cache: dict = {}


def lines(screen: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Hộp (x, y, w, h) các dòng chữ be kem trên màn hình thế giới (đã che vùng giao diện cố định): chữ cách nhau dưới 7 cột gộp thành một dòng."""
    masked = world_mask.mask_ui(screen)
    r, g = masked[..., 2].astype(np.int16), masked[..., 1].astype(np.int16)
    b = masked[..., 0].astype(np.int16)
    text = (((r > 185) & (g > 150) & (r - b > 20)) * 255).astype(np.uint8)
    merged = cv2.dilate(text, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 1)))
    count, _, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
    boxes = []
    for i in range(1, count):
        box = tuple(int(v) for v in stats[i][:4])
        if box[3] > LINE_MAX_H:
            continue
        if (box[2] >= LINE_MIN_W and box[3] >= LINE_MIN_H) or (box[2] >= EDGE_MIN_W and box[3] >= EDGE_MIN_H and edge_side(box)):
            boxes.append(box)
    return sorted(boxes, key=lambda box: (box[1], box[0]))


def edge_side(box: tuple[int, int, int, int]) -> str | None:
    """"left" / "right" nếu dòng chữ `box` bị cắt ở bên đó (sát rìa màn hình hoặc sát vùng giao diện bị che, chỉ thấy một phần nhãn), không thì None."""
    x, y, w, h = box
    cy = y + h // 2
    if x <= EDGE_TOL or world_mask.inside_excluded(x - EDGE_TOL, cy):
        return "left"
    if x + w >= world_mask.SIZE[0] - EDGE_TOL or world_mask.inside_excluded(x + w + EDGE_TOL, cy):
        return "right"
    return None


def ink(screen: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Ảnh nét chữ (0-1, STRIP_H hàng) của dòng `box` trên `screen`."""
    x, y, w, _ = box
    crop = screen[max(0, y - 2):y - 2 + STRIP_H, max(0, x - PAD_X):x + w + PAD_X + 1]
    r, g = crop[..., 2].astype(np.float32), crop[..., 1].astype(np.float32)
    return np.clip((r - INK_FROM) / INK_RANGE, 0, 1) * (g * 100 > r * CREAM)


def _label_char(label: str) -> str:
    return {"lp": "(", "rp": ")"}.get(label) or (label[2] if label.startswith("up") else label)


def _templates(font: str = FONT) -> dict[str, list[np.ndarray]]:
    """{chữ: [ảnh mẫu 0-1]} từ Images/OCR/<font>/, nhớ lại."""
    if ("templates", font) not in _cache:
        templates: dict[str, list[np.ndarray]] = {}
        for path in sorted((OCR_DIR / font).glob("*.png")):
            image = read_image(path, cv2.IMREAD_GRAYSCALE)
            if image is not None:
                templates.setdefault(_label_char(path.stem.split("_")[0]), []).append(image.astype(np.float32) / 255)
        if not templates:
            raise FileNotFoundError(f"Không có mẫu trong {OCR_DIR / font}: chạy python -m bot.ocr.make_map_samples <đường dẫn HeroDefault.ttf>")
        _cache[("templates", font)] = templates
    return _cache[("templates", font)]


class Lexicon:
    """Cây tiền tố các chuỗi cần nhận (VD "(Boss) Zombie", "Epic Bayar Knight"); chữ HOA đầu từ như trong game."""

    def __init__(self, strings, names=()):
        """`strings`: các nhãn đầy đủ; `names`: tên boss trơn (không "(Boss)" / tầng), dùng để đoán tên từ một đoạn nằm giữa (read_fragment)."""
        self.root: dict = {}
        for text in strings:
            node = self.root
            for ch in text:
                node = node.setdefault(ch, {})
            node["$"] = text
        self.strings = list(strings)
        self.names = list(names)
        self._suffix_root: dict | None = None
        self._fragment_root: dict | None = None

    def fragment_root(self) -> dict:
        """Cây các hậu tố của từng TÊN trơn (đọc đoạn con bất kỳ: dừng ở chữ bất kỳ, xem _search any_end)."""
        if self._fragment_root is None:
            root: dict = {}
            for name in self.names:
                for start in range(len(name)):
                    if name[start] == " ":
                        continue
                    node = root
                    for ch in name[start:]:
                        node = node.setdefault(ch, {})
                    node["$"] = name[start:]
            self._fragment_root = root
        return self._fragment_root

    def suffix_root(self) -> dict:
        """Cây các HẬU TỐ (từ một chữ bất kỳ tới hết nhãn, ít nhất MIN_PART chữ cái) của mọi chuỗi: để đọc nhãn bị cắt mất phần đầu."""
        if self._suffix_root is None:
            root: dict = {}
            for text in self.strings:
                for start in range(len(text)):
                    tail = text[start:]
                    if tail[0] == " " or len(tail.replace(" ", "")) < MIN_PART:
                        continue
                    node = root
                    for ch in tail:
                        node = node.setdefault(ch, {})
                    node["$"] = tail
            self._suffix_root = root
        return self._suffix_root


def _prepare(strip: np.ndarray, font: str = FONT) -> dict | None:
    """Điểm giống của từng mẫu tại từng cột của dòng; None nếu dòng không có nét."""
    columns = strip.max(axis=0)
    if columns.max() < 0.3:
        return None
    padded = np.pad(strip, ((4, 4), (PAD, PAD)))
    width = padded.shape[1]
    ink_before = np.concatenate([[0], np.cumsum(np.pad(columns, (PAD, PAD)))]).astype(np.float32)   # nét tích luỹ tới mỗi cột
    scores = {ch: [(m.shape[1], np.nan_to_num(cv2.matchTemplate(padded, m, cv2.TM_CCOEFF_NORMED).max(axis=0)))
                   for m in samples if m.shape[1] <= width]
              for ch, samples in _templates(font).items()}
    return {"width": width, "ink_before": ink_before, "scores": scores, "gaps": FONT_GAPS[font]}


def _shift_max(best: np.ndarray, gaps, ink_before: np.ndarray, back: bool = False):
    """moved[s] = max trên khoảng cách g của best[s - g] - LAMBDA * nét nằm trong khoảng trống; `back`: kèm g đã chọn."""
    size = len(best)
    moved = np.full(size, _NEG, np.float32)
    chosen = np.zeros(size, np.int32)
    for g in gaps:
        if g >= 0:
            cand = best[:size - g] - LAMBDA * (ink_before[g:size] - ink_before[:size - g])
            part, at = moved[g:], chosen[g:]
        else:
            cand = best[-g:]
            part, at = moved[:size + g], chosen[:size + g]
        better = cand > part
        part[better] = cand[better]
        at[better] = g
    return (moved, chosen) if back else moved


def _start(prepared: dict) -> np.ndarray:
    """Điểm khi bắt đầu ở cột bất kỳ: trừ nét bị bỏ sót bên trái."""
    return (-LAMBDA * prepared["ink_before"]).astype(np.float32)


def _finish(best: np.ndarray, prepared: dict) -> np.ndarray:
    """Điểm khi kết thúc ở cột bất kỳ: trừ nét bị bỏ sót bên phải."""
    ink_before = prepared["ink_before"]
    return best - LAMBDA * (ink_before[-1] - ink_before)


def _search(prepared: dict, root: dict, any_end: bool = False, min_letters: int = 1) -> tuple[float, str | None]:
    scores, ink_before = prepared["scores"], prepared["ink_before"]
    result = [(_NEG, None)]

    def walk(node: dict, best: np.ndarray, count: int, text: str = ""):
        if any_end and count >= min_letters and "$" not in node:       # đọc một phần: dừng ở chữ bất kỳ (nhãn bị cắt mất phần cuối)
            mean = float(_finish(best, prepared).max()) / count
            if mean > result[0][0]:
                result[0] = (mean, text)
        for ch, child in node.items():
            if ch == "$":
                if count >= min_letters:
                    mean = float(_finish(best, prepared).max()) / count
                    if mean > result[0][0]:
                        result[0] = (mean, child)
                continue
            if ch == " ":
                walk(child, _shift_max(best, prepared["gaps"][1], ink_before), count, text + ch)
                continue
            if ch not in scores:
                continue
            moved = _shift_max(best, prepared["gaps"][0], ink_before) if count else best
            new = np.full_like(best, _NEG)
            for width, score in scores[ch]:
                part = new[width:width + len(score)]
                np.maximum(part, moved[:len(score)] + score, out=part)
            if count + 1 >= 2 and new.max() / (count + 1) < BEAM:
                continue
            walk(child, new, count + 1, text + ch)

    walk(root, _start(prepared), 0)
    return result[0]


def _letter_scores(prepared: dict, text: str) -> list[float]:
    """Độ giống từng chữ của `text` khi xếp vào dòng theo cách tốt nhất (cùng quy hoạch động như _search, có lần ngược)."""
    scores, ink_before = prepared["scores"], prepared["ink_before"]
    best = _start(prepared)
    steps = []          # (chữ, khoảng cách chọn, mẫu chọn, điểm theo cột kết thúc)
    count = 0
    for ch in text:
        if ch == " ":
            best, gap = _shift_max(best, prepared["gaps"][1], ink_before, back=True)
            steps.append((" ", gap, None, None))
            continue
        moved, gap = _shift_max(best, prepared["gaps"][0], ink_before, back=True) if count else (best, np.zeros(len(best), np.int32))
        new = np.full_like(best, _NEG)
        pick = np.full(len(best), -1, np.int32)
        gain = np.zeros(len(best), np.float32)
        for index, (width, score) in enumerate(scores[ch]):
            cand = moved[:len(score)] + score
            part = new[width:width + len(score)]
            better = cand > part
            part[better] = cand[better]
            pick[width:width + len(score)][better] = index
            gain[width:width + len(score)][better] = score[better]
        steps.append((ch, gap, pick, gain, ch))
        best = new
        count += 1
    end = int(_finish(best, prepared).argmax())
    out = []
    for step in reversed(steps):
        if step[0] == " ":
            end -= int(step[1][end])
            continue
        _, gap, pick, gain, ch = step
        out.append(float(gain[end]))
        end -= scores[ch][int(pick[end])][0]
        end -= int(gap[end])
    return out[::-1]


def _check(scores: list[float], min_letters: int = 1, max_weak: int = MAX_WEAK) -> tuple[float, float, int] | None:
    """(điểm TB của các chữ chắc, điểm chữ kém nhất, số chữ yếu) nếu các điểm từng chữ `scores` đủ để nhận: không quá MAX_WEAK chữ yếu, đủ MIN_STRONG chữ chắc,
    điểm TB các chữ chắc >= MIN_MEAN; không thì None."""
    strong = [v for v in scores if v >= MIN_LETTER]
    weak = len(scores) - len(strong)
    need = MIN_MEAN + SHORT_BONUS * max(0, SHORT_LEN - len(scores))
    if len(scores) < min_letters or weak > max_weak or len(strong) < MIN_STRONG or float(np.mean(strong)) < need:
        return None
    return round(float(np.mean(strong)), 2), round(min(scores), 2), weak


def read(strip: np.ndarray, lexicon: Lexicon, font: str = FONT) -> dict | None:
    """Tên trong `lexicon` khớp nhất với ảnh nét chữ `strip` (xem ink()): {"text", "mean", "min", "weak"} (weak = số chữ yếu đọc là "?"), hoặc None nếu không đủ giống (xem _check)."""
    prepared = _prepare(strip, font)
    if prepared is None:
        return None
    mean, text = _search(prepared, lexicon.root)
    if text is None or mean < MIN_MEAN - 0.1:
        return None
    scores = _letter_scores(prepared, text)
    checked = _check(scores)
    if checked is None:
        return None
    return {"text": text, "mean": checked[0], "min": checked[1], "weak": checked[2]}


def read_partial(strip: np.ndarray, lexicon: Lexicon, side: str) -> dict | None:
    """Đọc dòng nhãn bị CẮT (xem edge_side): side "left" = mất phần đầu (đoạn thấy được là hậu tố của một nhãn), "right" = mất phần cuối (tiền tố). Chỉ cần thấy
    MIN_PART chữ cái (không kể chữ sát chỗ cắt: chỉ thấy một phần nên không tính điểm và bỏ khỏi `text`). {"text": đoạn đọc được, "mean", "min", "side"} hoặc None; đoạn đọc được có thể khớp
    nhiều nhãn (VD "ight"): người gọi tự tìm các nhãn có đoạn đó ở đầu / cuối (candidates)."""
    prepared = _prepare(strip)
    if prepared is None:
        return None
    if side == "left":
        mean, text = _search(prepared, lexicon.suffix_root(), min_letters=MIN_PART)
    else:
        mean, text = _search(prepared, lexicon.root, any_end=True, min_letters=MIN_PART)
    if text is None or mean < MIN_MEAN - 0.1:
        return None
    scores = _letter_scores(prepared, text)
    letters = [i for i, ch in enumerate(text) if ch != " "]
    cut = letters[0] if side == "left" else letters[-1]             # chữ sát chỗ cắt chỉ thấy một phần: không tin, bỏ khỏi kết quả
    inner = scores[1:] if side == "left" else scores[:-1]
    checked = _check(inner, MIN_PART, 0)
    if checked is None:
        return None
    text = text[cut + 1:].lstrip() if side == "left" else text[:cut].rstrip()
    return {"text": text, "mean": checked[0], "min": checked[1], "weak": checked[2], "side": side}


def read_fragment(strip: np.ndarray, lexicon: Lexicon) -> dict | None:
    """Đọc một đoạn ngắn nằm bất kỳ trong một tên boss (dòng chữ chỉ còn thấy đoạn đó, hai đầu đều bị cắt): ít nhất MIN_FRAG chữ cái, mọi chữ nhìn thấy được tính điểm.
    {"text", "mean", "min", "weak", "side": None} hoặc None. Đoạn khớp cả dòng vì nét chữ không nằm trong đoạn bị trừ điểm (xem LAMBDA)."""
    prepared = _prepare(strip)
    if prepared is None or not lexicon.names:
        return None
    mean, text = _search(prepared, lexicon.fragment_root(), any_end=True, min_letters=MIN_FRAG)
    if text is None or mean < MIN_MEAN - 0.1:
        return None
    text = text.strip()                                      # khoảng trắng đầu / cuối không phải chữ nhìn thấy được
    if len(text.replace(" ", "")) < MIN_FRAG:
        return None
    checked = _check(_letter_scores(prepared, text), MIN_FRAG, 0)
    if checked is None:
        return None
    return {"text": text, "mean": checked[0], "min": checked[1], "weak": checked[2], "side": None}


def candidates(lexicon: Lexicon, part: dict) -> list[str]:
    """Các nhãn trong `lexicon` (hoặc tên trơn, khi đoạn từ read_fragment) bắt đầu (side "right") / kết thúc (side "left") / chứa (side None) đoạn đọc được `part`."""
    text = part["text"]
    side = part.get("side", "full")
    if side is None:
        return [n for n in lexicon.names if text in n]
    if side == "full":
        return [text]
    if side == "left":
        return [s for s in lexicon.strings if s.endswith(text)]
    return [s for s in lexicon.strings if s.startswith(text)]
