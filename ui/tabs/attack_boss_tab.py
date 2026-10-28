"""Attack Boss settings: giống Join Monster War (đội quân, thể lực, chọn boss) + nguồn nhận boss + Crazy Eggs."""
from PyQt5.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QRadioButton,
)
from bot.activities.attack_boss import constants as ab
from bot.activities.event_center.crazy_eggs import constants as eggs
from .join_monster_war_tab import VIKING_LEVEL_DEFAULT, VIKING_LEVELS, JoinMonsterWarTab


COMBO_WIDTH = 96      # Type và hai ô tăng tốc rộng bằng nhau
GENERAL_CONTROLS = ("checkBoxSelectGeneral", "checkBoxAssistantGeneral", "checkBoxDevelopmentGeneral")


def _hours_text(hours: int) -> str:
    return "0" if hours == 0 else f"{hours}h"


def _hours_value(text: str) -> int:
    return int(text.rstrip("h") or 0)


class AttackBossTab(JoinMonsterWarTab):
    def __init__(self, parent=None):
        super().__init__(parent, title=ab.TAB)
        # Viking có hai loại: "Viking share" (được gửi, nằm trong danh sách boss ở dưới, đi theo luồng chung) và Viking do chính mình gọi (group Viking trong Setting:
        # Summon + độ khó). Không chọn tướng (đội quân phải có sẵn tướng).
        for _, name, card in self.boss_cards:
            if name == ab.VIKING:
                card.setTitle("Viking share")
        for name in ("viking_summon", "viking_level"):      # Summon + độ khó của thẻ Viking cũ: thay bằng group Viking trong Setting
            self.controls[name].setVisible(False)
        setting = self._stamina_group
        # Nhóm Setting rộng 566 x 150 chia ba cột để không phải xuống hàng: Viking (x 14-154) | Use Stamina / Type / Crazy Eggs (x 166-364) | tăng tốc (x 382-554).
        viking = QGroupBox("Viking", setting)
        viking.setGeometry(14, 28, 140, 112)
        self.viking_summon = QCheckBox("Summon", viking)
        self.viking_summon.setGeometry(12, 24, 110, 26)
        self.viking_summon.setToolTip("Viking do chính mình gọi (Event Center > Viking Challenge): gọi boss, Ask for Help rồi tấn công luôn, không chia sẻ liên minh.")
        QLabel("Level: ", viking).setGeometry(12, 64, 46, 24)
        self.viking_level = QComboBox(viking)
        self.viking_level.setGeometry(58, 62, 74, 28)
        self.viking_level.addItems(VIKING_LEVELS)
        self.viking_level.setCurrentText(VIKING_LEVEL_DEFAULT)
        self.viking_level.setEnabled(False)
        self.viking_summon.toggled.connect(self.viking_level.setEnabled)
        for label in setting.findChildren(QLabel):          # Use Stamina của Join Monster War: dời sang cột giữa
            if label.text().strip() == "Use Stamina:":
                label.setGeometry(166, 39, 84, 24)
        self.controls["comboBoxUseStamina"].setGeometry(252, 36, 84, 30)
        for y, text, name in ((36, "March speed: ", "march_speed"), (75, "Return speed: ", "return_speed")):
            QLabel(text, setting).setGeometry(370, y + 3, 88, 24)
            combo = QComboBox(setting)
            combo.setGeometry(460, y, COMBO_WIDTH, 30)
            combo.addItems(ab.SPEEDUP_CHOICES)
            combo.setCurrentText(ab.SPEEDUP_DEFAULT)
            combo.setToolTip("Dùng vật phẩm tăng tốc: No = không tăng tốc; All = tới khi tới nơi / về xong; 5s ... 30s = tới khi thời gian còn lại không quá chừng đó; 1 ... 10 = dùng đúng chừng đó cái vật phẩm.")
            setattr(self, name, combo)
        self.controls["viking_summon"] = self.viking_summon     # get_settings / set_settings của Join Monster War đọc ghi hai ô này
        self.controls["viking_level"] = self.viking_level
        for name in GENERAL_CONTROLS:
            self.controls[name].setChecked(False)
            self.controls[name].setVisible(False)

        group = QGroupBox("Boss source")
        row = QHBoxLayout(group)
        row.setContentsMargins(16, 8, 16, 8)
        row.setSpacing(16)
        self._sources = QButtonGroup(self)    # chỉ một nguồn
        self.source_radios = {}
        for key, text in ab.SOURCES:
            radio = QRadioButton(text)
            self._sources.addButton(radio)
            self.source_radios[key] = radio
            row.addWidget(radio)
            if key == ab.SOURCE_PLAYER:
                self.player_name = QLineEdit()
                self.player_name.setPlaceholderText("Player name")
                self.player_name.setFixedWidth(160)
                row.addWidget(self.player_name)
            if key == ab.SOURCE_API:
                self.email = QLineEdit()
                self.email.setPlaceholderText("iScout email")
                self.email.setFixedWidth(180)
                self.password = QLineEdit()
                self.password.setPlaceholderText("Password")
                self.password.setEchoMode(QLineEdit.Password)
                self.password.setFixedWidth(130)
                row.addWidget(self.email)
                row.addWidget(self.password)
        row.addStretch()
        self.body_layout.insertWidget(2, group)    # dưới nhóm Troop / Setting, trên danh sách boss

        # Type và Crazy Eggs nằm trong nhóm Setting (cột giữa, dưới Use Stamina).
        for y, text in ((75, "Type: "), (111, "Crazy Eggs: ")):
            label = QLabel(text, setting)
            label.setGeometry(166, y + 3, 84, 24)
        self.attack_type = QComboBox(setting)
        self.attack_type.setGeometry(252, 75, COMBO_WIDTH, 30)
        self.attack_type.addItems(text for _, text in ab.ATTACK_TYPES)
        self.attack_type.setToolTip("Attack: đánh một mình. Alliance War: lập rally cho liên minh. Boss gửi qua Whisper "
                                    "luôn dùng Attack (có thể không có Alliance War).")
        self.crazy_eggs = QComboBox(setting)
        self.crazy_eggs.setGeometry(252, 111, 84, 30)
        self.crazy_eggs.addItems(_hours_text(h) for h in eggs.INTERVAL_CHOICES)
        self.crazy_eggs.setCurrentText(_hours_text(eggs.INTERVAL_DEFAULT))
        self.crazy_eggs.setToolTip("Đập trứng (Event Center > Crazy Eggs) xen giữa lúc đánh boss, chưa vỡ đủ 4 quả thì làm lại sau "
                                   "chừng này giờ. 0 = không làm.")
        self._sources.buttonToggled.connect(lambda *_: self._on_source_changed())
        self.source_radios[ab.SOURCE_DEFAULT].setChecked(True)

    def _selected_source(self) -> str:
        return next((key for key, radio in self.source_radios.items() if radio.isChecked()), ab.SOURCE_DEFAULT)

    def _on_source_changed(self):
        """Whisper: cần tên người chơi, ẩn phần chọn boss (boss nào được gửi thì đánh boss đó), Type luôn là Attack. IsCout: cũng ẩn phần chọn boss
        (bộ lọc đặt trên trang iScout, đánh từ trên xuống). Alliance: chọn boss như Join Monster War."""
        source = self._selected_source()
        whisper = source == ab.SOURCE_PLAYER
        self.player_name.setEnabled(whisper)
        self.email.setEnabled(source == ab.SOURCE_API)
        self.password.setEnabled(source == ab.SOURCE_API)
        if whisper:
            self.attack_type.setCurrentText(dict(ab.ATTACK_TYPES)[ab.TYPE_ATTACK])
        self.attack_type.setEnabled(not whisper)
        no_pick = source in (ab.SOURCE_PLAYER, ab.SOURCE_API)
        for _, group in self.boss_groups:       # không chọn boss nào (kể cả Viking share), boss nào có thì đánh
            group.setVisible(not no_pick)
        for _, _, card in self.boss_cards:
            card.setVisible(not no_pick)

    def get_settings(self) -> dict:
        settings = super().get_settings()
        for key in ("select_general", "select_assistant_general", "development_general"):
            settings.pop(key, None)
        settings[ab.SOURCE_KEY] = self._selected_source()
        settings[ab.PLAYER_KEY] = self.player_name.text().strip()
        settings[ab.MARCH_SPEED_KEY] = self.march_speed.currentText()
        settings[ab.RETURN_SPEED_KEY] = self.return_speed.currentText()
        settings[ab.EMAIL_KEY] = self.email.text().strip()
        settings[ab.PASSWORD_KEY] = self.password.text()
        settings[ab.TYPE_KEY] = next(k for k, text in ab.ATTACK_TYPES if text == self.attack_type.currentText())
        settings[ab.EGGS_KEY] = _hours_value(self.crazy_eggs.currentText())
        return settings

    def set_settings(self, data: dict):
        super().set_settings(data)
        for name in GENERAL_CONTROLS:       # set_settings của Join Monster War có thể bật lại: tab này không chọn tướng
            self.controls[name].setChecked(False)
        source = data.get(ab.SOURCE_KEY)
        self.source_radios[source if source in self.source_radios else ab.SOURCE_DEFAULT].setChecked(True)
        kind = data.get(ab.TYPE_KEY)
        self.attack_type.setCurrentText(dict(ab.ATTACK_TYPES).get(kind, dict(ab.ATTACK_TYPES)[ab.TYPE_DEFAULT]))
        self.player_name.setText(str(data.get(ab.PLAYER_KEY, "")))
        for combo, key in ((self.march_speed, ab.MARCH_SPEED_KEY), (self.return_speed, ab.RETURN_SPEED_KEY)):
            value = str(data.get(key, ab.SPEEDUP_DEFAULT))
            combo.setCurrentText(value if value in ab.SPEEDUP_CHOICES else ab.SPEEDUP_DEFAULT)
        self.email.setText(str(data.get(ab.EMAIL_KEY, "")))
        self.password.setText(str(data.get(ab.PASSWORD_KEY, "")))
        hours = data.get(ab.EGGS_KEY, eggs.INTERVAL_DEFAULT)
        self.crazy_eggs.setCurrentText(_hours_text(hours if hours in eggs.INTERVAL_CHOICES else eggs.INTERVAL_DEFAULT))
        self._on_source_changed()
