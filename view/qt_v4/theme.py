# view/qt_v4/theme.py
"""Kleurenpalet en globale QSS stylesheet."""


class C:
    """Kleurconstanten."""
    BG        = '#101211'
    SURFACE   = '#171a18'
    CARD      = '#202421'
    ELEVATED  = '#292d2a'
    INPUT     = '#0c0f0d'

    GREEN     = '#2fa866'
    GREEN_LT  = '#45c47a'
    GREEN_DK  = '#227a4b'
    GREEN_BG  = 'rgba(47,168,102,0.16)'

    TEXT      = '#f4f7f3'
    TEXT2     = '#b8c0b8'
    TEXT3     = '#778078'

    BORDER    = '#3a413b'

    RED       = '#ff6b5f'
    RED_BG    = 'rgba(255,107,95,0.16)'
    YELLOW    = '#e2b044'

    ORANGE    = '#f09a3e'
    ORANGE_DK = '#c97725'
    ORANGE_BG = 'rgba(240,154,62,0.16)'


GLOBAL_QSS = f"""
QWidget {{
    font-family: 'Segoe UI', 'Roboto', 'Noto Sans', 'DejaVu Sans', 'Arial', sans-serif;
    color: {C.TEXT};
    background-color: {C.BG};
}}

QPushButton {{
    background-color: {C.ELEVATED};
    color: {C.TEXT};
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 15px;
}}
QPushButton:pressed {{
    background-color: {C.GREEN_DK};
}}
QPushButton:disabled {{
    color: {C.TEXT3};
    background-color: {C.SURFACE};
}}
QPushButton#primary {{
    background-color: {C.GREEN};
    border: none;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton#primary:pressed {{
    background-color: {C.GREEN_DK};
}}
QPushButton#danger {{
    background-color: {C.RED_BG};
    color: {C.RED};
    border: 1px solid {C.RED};
}}
QPushButton#danger:pressed {{
    background-color: {C.RED};
    color: white;
}}
QPushButton#flat {{
    background-color: transparent;
    border: none;
    color: {C.TEXT2};
}}

QLineEdit {{
    background-color: {C.INPUT};
    color: {C.TEXT};
    border: 2px solid {C.BORDER};
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 19px;
}}
QLineEdit:focus {{
    border-color: {C.GREEN};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {C.BG};
    width: 22px;
    border-radius: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER};
    border-radius: 8px;
    min-height: 60px;
}}
QScrollBar::handle:vertical:pressed {{
    background: {C.GREEN_DK};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QLabel#title {{
    font-size: 28px;
    font-weight: bold;
}}
QLabel#subtitle {{
    font-size: 14px;
    color: {C.TEXT2};
}}
QLabel#section {{
    font-size: 15px;
    color: {C.TEXT2};
}}
QLabel#toast {{
    background-color: {C.ELEVATED};
    color: {C.TEXT};
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 15px;
    font-weight: bold;
}}
"""
