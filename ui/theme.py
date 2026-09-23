"""
Central theme definitions: colors, fonts and QSS stylesheet.
Import COLORS / FONT_FAMILY for ad-hoc styling, or call apply(app)
once at startup to install the global stylesheet.
"""
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CHECK_ICON = (ASSETS_DIR / "check.svg").as_posix()

FONT_FAMILY = "Segoe UI"

COLORS = {
    "bg_sidebar": "#1f2430",
    "bg_sidebar_hover": "#2a3040",
    "bg_sidebar_active": "#3a63f2",
    "bg_app": "#f4f5f7",
    "bg_panel": "#ffffff",
    "bg_group": "#ffffff",
    "border": "#e0e2e8",
    "text_primary": "#1f2430",
    "text_secondary": "#6b7280",
    "text_button_sidebar": "#abbddf",
    "text_on_dark": "#e8eaf0",
    "accent": "#3a63f2",
    "accent_hover": "#2f52d6",
    "success": "#2fb170",
    "danger": "#e5484d",
    "warning": "#e8a33d",
}

STYLESHEET = f"""
QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: 10.5pt;
    color: {COLORS['text_primary']};
}}

QMainWindow, #HomeView, #DeviceView {{
    background: {COLORS['bg_app']};
}}

/* ---- Sidebar ---- */
#Sidebar {{
    background: {COLORS['bg_sidebar']};
}}
#Sidebar QLabel#SidebarTitle {{
    color: {COLORS['text_primary']};
    font-size: 13pt;
    font-weight: 600;
    padding: 18px 16px 10px 16px;
}}
#Sidebar QPushButton {{
    text-align: left;
    color: {COLORS['text_primary']};
    background: "#ffffff" ;
    padding: 10px 12px;
    border-radius: 6px;
    margin: 0px 8px;
}}
#Sidebar QPushButton:hover {{
    background: '#edf0f8';
    color: {COLORS['text_secondary']};
}}
#Sidebar QPushButton:checked {{
    background: {COLORS['bg_sidebar_active']};
    color: {COLORS['text_on_dark']};
    font-weight: 600;
}}

/* ---- Tabs ---- */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background: {COLORS['bg_panel']};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: transparent;
    padding: 9px 24px;
    margin-right: 2px;
    color: {COLORS['text_secondary']};
}}
QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
}}

/* ---- GroupBox ---- */
QGroupBox {{
    background: {COLORS['bg_group']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {COLORS['text_primary']};
}}

/* ---- Buttons ---- */
QPushButton {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 14px;
}}
QPushButton:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['accent']};
}}
QPushButton#PrimaryButton, QPushButton[primary="true"] {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover, QPushButton[primary="true"]:hover {{
    background: {COLORS['accent_hover']};
    color: white;
}}
QPushButton#ApplyAllButton {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['accent']};
    color: {COLORS['accent']};
    font-weight: 600;
}}

/* ---- Inputs ---- */
QComboBox, QLineEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 5px 8px;
    background: {COLORS['bg_panel']};
}}
QCheckBox, QRadioButton {{
    padding: 3px 2px;
    spacing: 8px;
}}

/* Indicators keep their square/circle outline when checked; a tick
   (checkbox) or dot (radio) is drawn inside. */
QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    background: white;
    border: 1px solid #8a8f9c;
}}
QCheckBox::indicator {{
    border-radius: 3px;
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {COLORS['accent']};
}}
QCheckBox::indicator:checked {{
    border-color: {COLORS['accent']};
    image: url("{CHECK_ICON}");
}}
QRadioButton::indicator:checked {{
    border-color: {COLORS['accent']};
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 {COLORS['accent']}, stop:0.45 {COLORS['accent']},
        stop:0.55 white, stop:1 white);
}}
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
    background: #f0f1f4;
    border-color: #c5c8d0;
}}
"""


def apply(app):
    """Install the global stylesheet on a QApplication instance."""
    app.setStyleSheet(STYLESHEET)
