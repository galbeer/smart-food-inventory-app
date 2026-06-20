# view/qt_v4/keyboard.py
"""Ingebouwd virtueel toetsenbord voor touch-invoer."""

# pyrefly: ignore [missing-import]
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QSizePolicy
)
# pyrefly: ignore [missing-import]
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from .theme import C


class VirtualKeyboard(QWidget):
    """On-screen toetsenbord met AZERTY en numeriek modus."""

    key_pressed  = pyqtSignal(str)   # Normaal teken
    enter_pressed = pyqtSignal()
    backspace_pressed = pyqtSignal()

    AZERTY = [
        list('azertyuiop'),
        list('qsdfghjklm'),
        list('wxcvbn'),
    ]
    NUMS_ROW = list('1234567890')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shift = False
        self._numeric_mode = False
        self.setMaximumHeight(0)          # Start verborgen
        self._target_height = 304
        self.setStyleSheet(f"background-color: {C.SURFACE};")
        self._build_alpha_layout()
        self._build_numeric_layout()
        self._alpha_widget.show()
        self._num_widget.hide()

    # ── Layouts bouwen ────────────────────────────────────────────────────────

    def _key_style(self, special=False):
        bg = C.GREEN_DK if special else C.ELEVATED
        return (
            f"QPushButton {{ background:{bg}; color:{C.TEXT}; border:1px solid {C.BORDER};"
            f"  border-radius:6px; font-size:19px; min-height:48px; }}"
            f"QPushButton:pressed {{ background:{C.GREEN}; }}"
        )

    def _make_key(self, label, width=1, special=False):
        btn = QPushButton(label)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setMinimumHeight(48)
        # CRITICAL: Prevent keyboard buttons from stealing focus from QLineEdit
        btn.setFocusPolicy(Qt.NoFocus)
        if width > 1:
            btn.setMinimumWidth(48 * width)
        btn.setStyleSheet(self._key_style(special))
        return btn

    def _build_alpha_layout(self):
        self._alpha_widget = QWidget(self)
        vbox = QVBoxLayout(self._alpha_widget)
        vbox.setContentsMargins(4, 6, 4, 4)
        vbox.setSpacing(4)

        # Rij 0: cijfers
        row = QHBoxLayout(); row.setSpacing(3)
        for ch in self.NUMS_ROW:
            b = self._make_key(ch)
            b.clicked.connect(lambda _, c=ch: self._on_char(c))
            row.addWidget(b)
        vbox.addLayout(row)

        # Rij 1-3: letters
        for i, chars in enumerate(self.AZERTY):
            row = QHBoxLayout(); row.setSpacing(3)
            if i == 2:  # Shift knop
                sb = self._make_key('\u21e7', special=True)
                sb.clicked.connect(self._toggle_shift)
                row.addWidget(sb)
            for ch in chars:
                b = self._make_key(ch)
                b.clicked.connect(lambda _, c=ch: self._on_char(c))
                row.addWidget(b)
            if i == 2:  # Backspace
                bb = self._make_key('\u232b', special=True)
                bb.clicked.connect(self.backspace_pressed.emit)
                row.addWidget(bb)
            vbox.addLayout(row)

        # Rij 4: spatiebalk etc.
        row = QHBoxLayout(); row.setSpacing(3)
        nb = self._make_key('123', special=True)
        nb.clicked.connect(self._switch_to_numeric)
        row.addWidget(nb)
        comma = self._make_key(',')
        comma.clicked.connect(lambda: self._on_char(','))
        row.addWidget(comma)
        space = self._make_key('spatie')
        space.clicked.connect(lambda: self._on_char(' '))
        row.addWidget(space, 4)
        dot = self._make_key('.')
        dot.clicked.connect(lambda: self._on_char('.'))
        row.addWidget(dot)
        enter = self._make_key('\u21b5', special=True)
        enter.clicked.connect(self.enter_pressed.emit)
        row.addWidget(enter)
        vbox.addLayout(row)

    def _build_numeric_layout(self):
        self._num_widget = QWidget(self)
        grid = QGridLayout(self._num_widget)
        grid.setContentsMargins(20, 6, 20, 4)
        grid.setSpacing(6)
        nums = [['1','2','3'],['4','5','6'],['7','8','9']]
        for r, row_data in enumerate(nums):
            for c_, ch in enumerate(row_data):
                b = self._make_key(ch)
                b.setMinimumHeight(52)
                b.setStyleSheet(self._key_style() + "QPushButton{font-size:24px;}")
                b.clicked.connect(lambda _, x=ch: self._on_char(x))
                grid.addWidget(b, r, c_)
        # Laatste rij
        ab = self._make_key('ABC', special=True)
        ab.clicked.connect(self._switch_to_alpha)
        grid.addWidget(ab, 3, 0)
        z = self._make_key('0')
        z.setMinimumHeight(52)
        z.setStyleSheet(self._key_style() + "QPushButton{font-size:24px;}")
        z.clicked.connect(lambda: self._on_char('0'))
        grid.addWidget(z, 3, 1)
        bb = self._make_key('\u232b', special=True)
        bb.clicked.connect(self.backspace_pressed.emit)
        grid.addWidget(bb, 3, 2)
        # Enter apart onderaan
        eb = self._make_key('\u21b5  OK', special=True)
        eb.setMinimumHeight(58)
        eb.clicked.connect(self.enter_pressed.emit)
        grid.addWidget(eb, 4, 0, 1, 3)

    # ── Acties ────────────────────────────────────────────────────────────────

    def _on_char(self, ch):
        if self._shift and ch.isalpha():
            ch = ch.upper()
            self._shift = False
        self.key_pressed.emit(ch)

    def _toggle_shift(self):
        self._shift = not self._shift

    def _switch_to_numeric(self):
        self._alpha_widget.hide()
        self._num_widget.show()
        self._numeric_mode = True

    def _switch_to_alpha(self):
        self._num_widget.hide()
        self._alpha_widget.show()
        self._numeric_mode = False

    # ── Tonen / Verbergen ─────────────────────────────────────────────────────

    def show_keyboard(self, numeric=False):
        if numeric and not self._numeric_mode:
            self._switch_to_numeric()
        elif not numeric and self._numeric_mode:
            self._switch_to_alpha()
        anim = QPropertyAnimation(self, b"kbHeight")
        anim.setDuration(200)
        anim.setStartValue(self.maximumHeight())
        anim.setEndValue(self._target_height)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim = anim
        anim.start()

    def hide_keyboard(self):
        anim = QPropertyAnimation(self, b"kbHeight")
        anim.setDuration(150)
        anim.setStartValue(self.maximumHeight())
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim = anim
        anim.start()

    # Custom property voor animatie (uses maximumHeight to avoid conflicts)
    @pyqtProperty(int)
    def kbHeight(self):
        return self.maximumHeight()

    @kbHeight.setter
    def kbHeight(self, h):
        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._alpha_widget.setGeometry(0, 0, w, h)
        self._num_widget.setGeometry(0, 0, w, h)
