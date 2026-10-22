"""Nhiều boss ở mép màn hình: thứ tự trên-trái trước và danh sách chờ theo toạ độ thế giới (hướng tới từng boss tính lại từ camera)."""
import unittest
from unittest import mock

from bot.common import boss_scan
from bot.common.arc_sweep import MIN_SWIPE, STEP_FRAC, SWIPE_FULL, SWIPE_FULL_V, px_to_world, world_to_px
from bot.common.boss_scan import CAMERA_PX, _shift, reading_order, restore_camera, same_boss, screen_of, visible, world_position


class EdgeBossTests(unittest.TestCase):
    def test_top_left_goes_first(self):
        positions = [(350, 560), (40, 100), (360, 90), (50, 540)]
        ordered = sorted(positions, key=reading_order)
        self.assertEqual(ordered[0], (40, 100))
        self.assertEqual(ordered[-1], (350, 560))

    def test_screen_of_is_inverse_of_world_position(self):
        camera = (600, 450)
        for pos in [(40, 100), (350, 560), (200, 350)]:
            world = world_position(camera, pos)
            back = screen_of(camera, world)
            self.assertLessEqual(abs(back[0] - pos[0]) + abs(back[1] - pos[1]), 2)

    def test_boss_at_camera_is_at_screen_centre(self):
        x, y = screen_of((600, 450), (600, 450))
        self.assertEqual(x, CAMERA_PX[0])
        self.assertTrue(visible((x, y)))

    def test_direction_to_boss_after_camera_moved(self):
        """Hai boss cách nhau; camera dời sang boss thứ nhất thì boss thứ hai ở đúng hướng (tính lại từ camera), không cần nhớ cú kéo."""
        far = (640.0, 410.0)                          # boss thứ hai (toạ độ thế giới)
        before = screen_of((600, 450), far)           # camera ở giữa ô quét
        after = screen_of((580, 470), far)            # sau khi xử lý boss thứ nhất, camera dời tới (580, 470)
        self.assertNotEqual(before, after)
        self.assertEqual(after, screen_of((580, 470), far))

    def test_far_boss_is_off_screen_in_its_direction(self):
        x, y = screen_of((600, 450), (600, 380))      # Y nhỏ hơn: boss ở phía trên-phải màn hình, rất xa
        self.assertFalse(visible((x, y)))
        self.assertLess(y, 70)                        # nằm phía TRÊN vùng nhìn thấy: phải kéo xuống để đón


class RestoreCameraTests(unittest.TestCase):
    def run_restore(self, cameras, expected=(600, 600)):
        swipes = []
        bot = mock.Mock()
        reads = iter(cameras)
        with mock.patch.object(boss_scan, "_camera", side_effect=lambda b, s=None: next(reads)), mock.patch.object(boss_scan, "settle", return_value="screen"),                 mock.patch.object(boss_scan, "_swipe", side_effect=lambda b, fx, fy, before, shift: (swipes.append((fx, fy)), (True, None))[1]),                 mock.patch.object(boss_scan, "safe_shift", return_value=None):
            result = restore_camera(bot, expected)
        return result, swipes

    def test_in_place_does_nothing(self):
        result, swipes = self.run_restore([(601, 599)])
        self.assertTrue(result)
        self.assertEqual(swipes, [])

    def test_drift_swipes_opposite_to_the_needed_camera_move(self):
        """Camera cần dời (+dX, 0) = sang phải một chút và xuống; ngón tay kéo ngược lại đúng hướng đó, rồi đọc lại thấy về chỗ cũ."""
        result, swipes = self.run_restore([(590, 600), (600, 600)])
        self.assertTrue(result)
        self.assertEqual(len(swipes), 1)
        px, py = world_to_px(10, 0)
        self.assertEqual(swipes[0], (-px, -py))

    def test_long_drift_is_clamped_to_swipe_box_and_repeated(self):
        result, swipes = self.run_restore([(450, 450), (500, 500), (600, 600)])
        self.assertTrue(result)
        self.assertEqual(len(swipes), 2)
        for fx, fy in swipes:
            self.assertLessEqual(abs(fx), STEP_FRAC * SWIPE_FULL + 1)
            self.assertLessEqual(abs(fy), STEP_FRAC * SWIPE_FULL_V + 1)

    def test_unreadable_camera_leaves_it_alone(self):
        result, swipes = self.run_restore([None])
        self.assertFalse(result)
        self.assertEqual(swipes, [])


class HelpersTests(unittest.TestCase):
    def test_same_boss_rules(self):
        self.assertTrue(same_boss({"name": "Ymir", "tier": None}, {"name": "Ymir", "tier": None}))
        self.assertFalse(same_boss({"name": "Ymir", "tier": None}, {"name": "Sphinx", "tier": None}))
        self.assertTrue(same_boss({"name": None}, {"name": "Sphinx", "tier": None}))     # đọc một phần: có thể cùng

    def test_shift_moves_camera_opposite_to_finger(self):
        """Boss ở (100, 300) được kéo tới (240, 330) => ngón tay kéo (+140, +30) => camera dời (-140, -30) px theo màn hình."""
        before = (600.0, 600.0)
        after = _shift(before, (100, 300), (240, 330))
        du, dv = px_to_world(-140, -30)
        self.assertAlmostEqual(after[0], before[0] + du)
        self.assertAlmostEqual(after[1], before[1] + dv)
        self.assertIsNone(_shift(None, (1, 1), (2, 2)))


if __name__ == "__main__":
    unittest.main()
