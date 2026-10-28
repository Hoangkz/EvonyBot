"""
sources.py — ba nguồn nhận boss của Attack Boss. Mỗi nguồn có `poll(bot) -> list[BossOffer]`: các boss MỚI kể từ lần poll trước
(nguồn tự nhớ cái đã trả). Chỉ dùng một nguồn trong một lượt chạy (`make_source`).
"""
from dataclasses import dataclass

import time

import numpy as np

from ...ocr import read_chat

from .world import ensure_world
from .constants import (AGE_LIMIT_MIN, CHAT_BAR, CHAT_OPEN_WAIT, CHAT_THRESHOLD, CHAT_TITLE, MAX_PAGES, SAME_PAGE_DIFF, SCROLL, SCROLL_TIME,
                        SCROLL_WAIT, TAB_ALLIANCE, TAB_WAIT, CONVERSATION_WAIT, TAB_WHISPER, WHISPER_BATCH, WHISPER_KEEP)
from .constants import EMAIL_KEY, PASSWORD_KEY, PLAYER_KEY, SOURCE_API, SOURCE_DEFAULT, SOURCE_KEY, SOURCE_PLAYER


@dataclass(frozen=True)
class BossOffer:
    """Một boss được báo: toạ độ trên bản đồ; tên / cấp có thể thiếu (tin nhắn người chơi không chắc có)."""
    x: int | None = None
    y: int | None = None
    name: str | None = None
    level: int | None = None
    ident: int | None = None     # Whisper: không đọc toạ độ, boss chỉ có số thứ tự (ảnh cắt của tin nhắn)

    @property
    def coords(self):
        """Khoá của boss: toạ độ, hoặc (None, số thứ tự) khi không đọc toạ độ."""
        return (self.x, self.y) if self.x is not None else (None, self.ident)


class AllianceChatSource:
    """Tin nhắn liên minh: vào chat Alliance, chụp màn hình phần tin, cuộn lên chụp tiếp tới khi gặp tin cũ hơn AGE_LIMIT_MIN phút (hoặc hết tin);
    SAU ĐÓ mới OCR các ảnh: chỉ lấy tin "shared Coordinates:", đọc toạ độ, tên, cấp và giờ gửi."""

    def poll(self, bot) -> list[BossOffer]:
        return read_offers(capture(bot, TAB_ALLIANCE))


def capture(bot, tab: tuple[int, int]) -> list:
    """Mở chat ở tab `tab`, chụp trang hiện tại rồi cuộn lên chụp tiếp (mới -> cũ). Dừng khi: có tin cũ hơn AGE_LIMIT_MIN phút, không cuộn được nữa
    (trang không đổi), hoặc đủ MAX_PAGES. Cuối cùng đóng chat (Back)."""
    if not open_chat(bot, tab):
        return []
    pages: list = []
    for _ in range(MAX_PAGES):
        shot = bot.screenshot()
        if pages and _same(pages[-1], shot):
            break
        pages.append(shot)
        if _has_old(shot):
            break
        bot.swipe(*SCROLL, duration=SCROLL_TIME, delay=SCROLL_WAIT)
    bot.back(delay=1)
    return pages


def open_chat(bot, tab: tuple[int, int]) -> bool:
    """Từ bản đồ thế giới: bấm dòng chat ở đáy, chờ màn chat rồi bấm tab `tab`. False nếu màn chat không mở."""
    bot.tap(*CHAT_BAR, delay=0)
    for _ in range(round(CHAT_OPEN_WAIT / 0.5)):
        bot.sleep(0.5)
        if bot.find(CHAT_TITLE, threshold=CHAT_THRESHOLD) is not None:
            bot.tap(*tab, delay=TAB_WAIT)
            return True
    bot.log("Attack Boss: không mở được màn chat")
    return False


def _same(a, b) -> bool:
    top, bottom = read_chat.AREA
    return float(np.abs(a[top:bottom].astype(np.int16) - b[top:bottom].astype(np.int16)).mean()) < SAME_PAGE_DIFF


def _has_old(shot) -> bool:
    """Trang có tin cũ hơn AGE_LIMIT_MIN phút (giờ đọc được)."""
    for box in read_chat.bubbles(shot):
        age = read_chat.age_minutes(shot, *box)
        if age is not None and age > AGE_LIMIT_MIN:
            return True
    return False


def read_offers(pages: list) -> list[BossOffer]:
    """OCR các trang đã chụp: mỗi tin "shared Coordinates:" nằm trọn trong trang và gửi trong AGE_LIMIT_MIN phút (giờ không đọc được thì vẫn lấy)
    thành một BossOffer (toạ độ, tên, cấp). Cùng toạ độ chỉ lấy một lần (trang mới nhất trước)."""
    found: dict[tuple[int, int], BossOffer] = {}
    for shot in pages:
        for box in read_chat.bubbles(shot):
            if not read_chat.complete(box):
                continue
            coords = read_chat.read(shot, *box)
            if coords is None:
                continue
            age = read_chat.age_minutes(shot, *box)
            if age is not None and age > AGE_LIMIT_MIN:
                continue
            _, x, y = coords
            name, level = read_chat.name_and_level(shot, *box)
            found.setdefault((x, y), BossOffer(x, y, name, level))
    return list(found.values())


class PlayerChatSource:
    """Whisper (KHÔNG OCR tin nhắn), mỗi lần MỘT boss: vào chat > tab Whisper > bấm cuộc trò chuyện có tên người đó (tên đọc ở danh sách) > trong
    WHISPER_BATCH (6) tin "shared Coordinates:" mới nhất, lấy tin ở vị trí y CAO NHẤT (mới nhất, ở dưới cùng) mà ảnh của nó KHÔNG giống ảnh nào đã cắt;
    cắt luôn đoạn tin nhắn đó thành một ảnh (`crops`) và trả boss đó (chat còn mở để `goto` bấm vào tin rồi `attack` tấn công). Boss tiếp theo: `run` poll
    lại, vào Whisper lại, lấy tin y cao nhất nhưng loại các tin giống ảnh đã cắt. Hết tin chưa cắt thì trả rỗng (chờ tin mới, ~5 phút có boss mới).
    Whisper không chọn boss: boss nào được gửi cũng đánh.

    Ảnh cắt đánh xong vẫn giữ (tối đa WHISPER_KEEP = 10 ảnh, quá thì bỏ ảnh cũ nhất): không đánh trùng boss, lần sau không phải tìm lại tin đó."""

    def __init__(self, player_name: str):
        self.player_name = player_name.strip()
        self.crops: dict[int, tuple] = {}     # số thứ tự boss -> (ảnh cắt của tin, vị trí bấm trong ảnh): boss đã gặp (đánh rồi vẫn giữ), tối đa 10
        self.count = 0                        # số boss đã gặp (cấp số thứ tự)
        self.inside = False                   # đang ở trong cuộc trò chuyện (sau poll, trước khi rời chat)

    def poll(self, bot) -> list[BossOffer]:
        shot = self._enter(bot)
        if shot is None:
            return []
        top = read_chat.CONVERSATION_TOP
        boxes = [box for box in read_chat.bubbles(shot, top=top)
                 if read_chat.complete(box, top) and read_chat.is_shared(shot, *box)][-WHISPER_BATCH:]
        for box in sorted(boxes, key=lambda box: -box[0]):      # y lớn nhất trước = mới nhất trước
            crop = read_chat.message_crop(shot, *box)
            if crop is None or any(read_chat.same_crop(crop[0], old[0]) for old in self.crops.values()):
                continue            # tin này đã cắt rồi (đã đánh / đang chờ): loại
            self.count += 1
            self.crops[self.count] = crop
            while len(self.crops) > WHISPER_KEEP:       # giữ tối đa WHISPER_KEEP (10) ảnh: quá thì bỏ ảnh cũ nhất
                del self.crops[next(iter(self.crops))]
            self.inside = True      # ở lại cuộc trò chuyện để `goto` bấm luôn vào tin này
            return [BossOffer(ident=self.count)]
        self.inside = False
        self._leave(bot)
        return []

    def goto(self, bot, offer: BossOffer) -> bool:
        """Tới boss bằng cách bấm vào toạ độ trong tin của nó ở Whisper (tìm tin bằng ảnh cắt). False nếu không có ảnh cắt / không tìm thấy tin."""
        crop = self.crops.get(offer.ident)
        if crop is None:
            return False
        image, (dx, dy) = crop
        for attempt in range(2):
            shot = self._enter(bot) if attempt or not self.inside else bot.screenshot()
            self.inside = False
            if shot is None:
                return False
            at = read_chat.find_crop(shot, image, read_chat.CONVERSATION_TOP)
            if at is not None:
                bot.tap(at[0] + dx, at[1] + dy, delay=0)
                return True
        return False

    def _enter(self, bot):
        """Vào cuộc trò chuyện với người chơi (từ bản đồ thế giới): ảnh chụp cuộc trò chuyện, hoặc None (không mở được chat / không thấy người đó)."""
        if not self.player_name or not ensure_world(bot) or not open_chat(bot, TAB_WHISPER):
            return None
        shot = bot.screenshot()
        rows = read_chat.bubbles(shot, x=read_chat.LIST_X)
        row = next((box for box in rows if read_chat.same_name(read_chat.list_name(shot, *box), self.player_name)), None)
        if row is None:
            bot.log(f"Attack Boss: không thấy cuộc trò chuyện với {self.player_name} trong Whisper")
            self._leave(bot)
            return None
        bot.tap(200, (row[0] + row[1]) // 2, delay=CONVERSATION_WAIT)
        return bot.screenshot()

    @staticmethod
    def _leave(bot) -> None:
        ensure_world(bot)


class ApiSource:
    """Boss gửi về từ IsCout (đăng nhập bằng email / password ở tab)."""

    def __init__(self, email: str, password: str):
        self.email = email.strip()
        self.password = password

    def poll(self, bot) -> list[BossOffer]:
        # TODO: đăng nhập IsCout bằng self.email / self.password rồi lấy boss mới (chưa có địa chỉ / định dạng API).
        return []


def make_source(settings: dict):
    """Nguồn theo cấu hình tab; giá trị lạ -> nguồn mặc định (tin nhắn liên minh)."""
    source = settings.get(SOURCE_KEY, SOURCE_DEFAULT)
    if source == SOURCE_PLAYER:
        return PlayerChatSource(str(settings.get(PLAYER_KEY, "")))
    if source == SOURCE_API:
        return ApiSource(str(settings.get(EMAIL_KEY, "")), str(settings.get(PASSWORD_KEY, "")))
    return AllianceChatSource()
