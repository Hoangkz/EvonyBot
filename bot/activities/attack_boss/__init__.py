"""
attack_boss — "Attack Boss" activity: tự đánh boss được báo về, chạy MỘT MÌNH (trừ Crazy Eggs).

Nguồn nhận boss (chỉ dùng một trong ba, chọn ở tab):
- alliance_chat: tin nhắn liên minh (boss do Find Boss / người chơi khác chia sẻ)
- player_chat:   Whisper, tin nhắn của một người chơi (nhập tên); không chọn boss, được gửi boss nào thì đánh boss đó
- api:           boss gửi về từ một API (TODO)

- run.py:     entry point, `run(bot, settings)`, vòng lặp nhận boss -> đánh
- sources.py: BossOffer và ba nguồn nhận boss
- constants.py: key cấu hình, tên nguồn
"""
from .run import run

__all__ = ["run"]
