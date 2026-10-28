"""Attack Boss: đọc màn chat (ảnh chụp thật 396 x 704 từ giả lập): bong bóng, toạ độ, tên, cấp, giờ gửi, và OCR các trang đã chụp."""
import unittest
from pathlib import Path

import cv2

from bot.activities.attack_boss import sources
from bot.ocr import read_chat

SCREENS = Path(__file__).parent / "screens"


def load(name):
    return cv2.imread(str(SCREENS / name))


class ReadChatTests(unittest.TestCase):
    def test_alliance_page(self):
        shot = load("alliance_chat.png")
        complete = [box for box in read_chat.bubbles(shot) if read_chat.complete(box)]
        self.assertEqual(len(complete), 6)
        rows = [(read_chat.read(shot, *box), read_chat.name_and_level(shot, *box), read_chat.age_minutes(shot, *box))
                for box in complete]
        self.assertEqual(rows[0], ((1835, 550, 86), ("viking", 2), 1440))
        self.assertEqual(rows[4], ((1835, 538, 133), ("(boss) yasha", 7), 22))
        self.assertEqual(rows[5], ((1835, 572, 112), ("(boss) centaur", 3), 21))

    def test_whisper_conversation(self):
        shot = load("whisper_chat.png")
        box = [b for b in read_chat.bubbles(shot) if read_chat.complete(b)][0]
        self.assertEqual(read_chat.read(shot, *box), (1835, 572, 112))
        self.assertEqual(read_chat.name_and_level(shot, *box), ("(boss) centaur", 3))

    def test_only_shared_coordinates_messages(self):
        shot = load("alliance_chat.png")
        blank = shot.copy()
        blank[:, 66:200] = (221, 237, 245)      # xoá cụm "shared Coordinates:" và tên
        box = read_chat.bubbles(blank)[-1]
        self.assertIsNone(read_chat.read(blank, *box))


class WhisperTests(unittest.TestCase):
    def test_list_row_name(self):
        shot = load("whisper_list.png")
        rows = read_chat.bubbles(shot, x=read_chat.LIST_X)
        self.assertEqual(len(rows), 1)
        name = read_chat.list_name(shot, *rows[0])
        self.assertTrue(read_chat.same_name(name, "Shah Jahan."))
        self.assertFalse(read_chat.same_name(name, "Bob"))

    def test_latest_message_and_link(self):
        shot = load("whisper_chat.png")
        top = read_chat.CONVERSATION_TOP
        boxes = [b for b in read_chat.bubbles(shot, top=top) if read_chat.complete(b, top)]
        self.assertEqual(len(boxes), 2)                       # tin Yasha (cũ) rồi tin Centaur (mới nhất, ở cuối)
        self.assertEqual(read_chat.read(shot, *boxes[-1]), (1835, 572, 112))
        x, y = read_chat.link(shot, *boxes[-1])
        self.assertTrue(boxes[-1][0] < y < boxes[-1][1])      # điểm bấm nằm trong tin mới nhất

    def test_message_crop_identity(self):
        shot = load("whisper_chat.png")
        top = read_chat.CONVERSATION_TOP
        boxes = [b for b in read_chat.bubbles(shot, top=top) if read_chat.complete(b, top)]
        first, second = (read_chat.message_crop(shot, *b) for b in boxes)
        self.assertTrue(read_chat.same_crop(first[0], first[0]))
        self.assertFalse(read_chat.same_crop(first[0], second[0]))
        at = read_chat.find_crop(shot, second[0], top)         # tìm lại đúng tin bằng ảnh cắt
        self.assertEqual(at[1] + second[1][1], read_chat.blue_point(shot, *boxes[1])[1])


class OffersTests(unittest.TestCase):
    def test_only_recent_bosses(self):
        offers = sources.read_offers([load("alliance_chat.png")])
        self.assertEqual([(o.coords, o.name, o.level) for o in offers],
                         [((538, 133), "(boss) yasha", 7), ((572, 112), "(boss) centaur", 3)])

    def test_has_old(self):
        self.assertTrue(sources._has_old(load("alliance_chat.png")))
        self.assertFalse(sources._has_old(load("whisper_chat.png")))


if __name__ == "__main__":
    unittest.main()
