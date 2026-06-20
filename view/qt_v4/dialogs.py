# view/qt_v4/dialogs.py
"""Dialoog-pagina's — geen QDialog meer, maar QWidget pages in de stack.

Door ze als pagina in de QStackedWidget te plaatsen, blijft het virtueel
toetsenbord altijd zichtbaar en werkend. Resultaten worden via signals
teruggegeven in plaats van exec_()/accept()/reject().
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from .theme import C


# ── Basis stijl helpers ──────────────────────────────────────────────────────

def _btn_style_primary():
    return f"""
        QPushButton {{
            background-color: {C.GREEN};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            padding: 12px;
        }}
        QPushButton:pressed {{
            background-color: {C.GREEN_DK};
        }}
    """

def _btn_style_danger():
    return f"""
        QPushButton {{
            background-color: {C.RED_BG};
            color: {C.RED};
            border: 1px solid {C.RED};
            border-radius: 8px;
            font-size: 16px;
            padding: 12px;
        }}
        QPushButton:pressed {{
            background-color: {C.RED};
            color: white;
        }}
    """

def _btn_style_normal():
    return f"""
        QPushButton {{
            background-color: {C.ELEVATED};
            color: {C.TEXT};
            border: 1px solid {C.BORDER};
            border-radius: 8px;
            font-size: 16px;
            padding: 12px;
        }}
        QPushButton:pressed {{
            background-color: {C.GREEN_DK};
        }}
    """

def _btn_style_flat():
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {C.TEXT2};
            border: none;
            border-radius: 8px;
            font-size: 16px;
            padding: 12px;
        }}
        QPushButton:pressed {{
            background-color: {C.ELEVATED};
        }}
    """

def _input_style():
    return f"""
        background-color: {C.INPUT};
        color: {C.TEXT};
        border: 2px solid {C.BORDER};
        border-radius: 8px;
        padding: 14px 16px;
        font-size: 18px;
    """

def _card_frame():
    """Maak een gestijlde kaart-container."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {C.SURFACE};
            border: 2px solid {C.BORDER};
            border-radius: 8px;
        }}
    """)
    return frame


# ── ManualInputPage ──────────────────────────────────────────────────────────

class ManualInputPage(QWidget):
    """Pagina voor handmatige invoer van een productnaam bij onbekend product."""
    name_submitted = pyqtSignal(str, str)   # barcode, name
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._barcode = ""
        self._delete_armed = False

        self.setStyleSheet(f"background-color: {C.BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        # Titel
        title = QLabel("Product onbekend")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {C.TEXT};")
        outer.addWidget(title)

        outer.addSpacing(10)

        # Info
        self.barcode_label = QLabel("")
        self.barcode_label.setStyleSheet(f"font-size: 14px; color: {C.TEXT2};")
        outer.addWidget(self.barcode_label)

        outer.addSpacing(16)

        # Naam invoer
        lbl = QLabel("Geef een productnaam op:")
        lbl.setStyleSheet(f"font-size: 15px; color: {C.TEXT};")
        outer.addWidget(lbl)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Productnaam...")
        self.name_input.setStyleSheet(_input_style())
        self.name_input.returnPressed.connect(self._on_save)
        outer.addWidget(self.name_input)

        outer.addSpacing(16)

        # Knoppen
        btn_save = QPushButton("Opslaan")
        btn_save.setFixedHeight(56)
        btn_save.setStyleSheet(_btn_style_primary())
        btn_save.clicked.connect(self._on_save)
        outer.addWidget(btn_save)

        btn_cancel = QPushButton("Annuleren")
        btn_cancel.setFixedHeight(56)
        btn_cancel.setStyleSheet(_btn_style_normal())
        btn_cancel.clicked.connect(self.cancelled.emit)
        outer.addWidget(btn_cancel)

        outer.addStretch()

    def set_barcode(self, barcode):
        """Stel de barcode in en reset het formulier."""
        self._barcode = barcode
        self.barcode_label.setText(f"Barcode: {barcode}")
        self.name_input.clear()

    def _on_save(self):
        name = self.name_input.text().strip()
        if name:
            self.name_submitted.emit(self._barcode, name)


# ── EditProductPage ──────────────────────────────────────────────────────────

class EditProductPage(QWidget):
    """Pagina voor het bewerken of verwijderen van een product."""
    name_saved = pyqtSignal(str, str)       # barcode, new_name
    delete_requested = pyqtSignal(str)      # barcode
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._barcode = ""

        self.setStyleSheet(f"background-color: {C.BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        # Titel
        title = QLabel("Product bewerken")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {C.TEXT};")
        outer.addWidget(title)

        outer.addSpacing(10)

        self.barcode_label = QLabel("")
        self.barcode_label.setStyleSheet(f"font-size: 14px; color: {C.TEXT2};")
        outer.addWidget(self.barcode_label)

        outer.addSpacing(16)

        # Naam invoer
        lbl = QLabel("Productnaam:")
        lbl.setStyleSheet(f"font-size: 15px; color: {C.TEXT};")
        outer.addWidget(lbl)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(_input_style())
        self.name_input.returnPressed.connect(self._on_save)
        outer.addWidget(self.name_input)

        outer.addSpacing(16)

        # Knoppen
        btn_save = QPushButton("Naam opslaan")
        btn_save.setFixedHeight(56)
        btn_save.setStyleSheet(_btn_style_primary())
        btn_save.clicked.connect(self._on_save)
        outer.addWidget(btn_save)

        outer.addSpacing(8)

        self.btn_delete = QPushButton("Product verwijderen")
        self.btn_delete.setFixedHeight(56)
        self.btn_delete.setStyleSheet(_btn_style_danger())
        self.btn_delete.clicked.connect(self._on_delete)
        outer.addWidget(self.btn_delete)

        outer.addSpacing(8)

        btn_cancel = QPushButton("Annuleren")
        btn_cancel.setFixedHeight(56)
        btn_cancel.setStyleSheet(_btn_style_flat())
        btn_cancel.clicked.connect(self.cancelled.emit)
        outer.addWidget(btn_cancel)

        outer.addStretch()

    def set_product(self, barcode, current_name):
        """Stel product in en reset het formulier."""
        self._barcode = barcode
        self.barcode_label.setText(f"Barcode: {barcode}")
        self.name_input.setText(current_name)
        self._reset_delete()

    def _on_save(self):
        name = self.name_input.text().strip()
        if name:
            self.name_saved.emit(self._barcode, name)

    def _on_delete(self):
        if not self._delete_armed:
            self._delete_armed = True
            self.btn_delete.setText("Nogmaals tikken")
            QTimer.singleShot(2500, self._reset_delete)
            return
        self._reset_delete()
        self.delete_requested.emit(self._barcode)

    def _reset_delete(self):
        self._delete_armed = False
        if hasattr(self, "btn_delete"):
            self.btn_delete.setText("Product verwijderen")


# ── NotificationPage ─────────────────────────────────────────────────────────

class NotificationPage(QWidget):
    """Pagina voor het tonen van een melding."""
    dismissed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet(f"background-color: {C.BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 40, 20, 40)

        outer.addStretch()

        # Titel
        title = QLabel("Melding")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {C.TEXT};")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)

        outer.addSpacing(20)

        # Bericht
        self.msg_label = QLabel("")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setStyleSheet(f"font-size: 16px; color: {C.TEXT};")
        outer.addWidget(self.msg_label)

        outer.addSpacing(30)

        # OK knop
        btn_ok = QPushButton("Begrepen")
        btn_ok.setFixedHeight(56)
        btn_ok.setStyleSheet(_btn_style_primary())
        btn_ok.clicked.connect(self.dismissed.emit)
        outer.addWidget(btn_ok)

        outer.addStretch()

    def set_message(self, text):
        """Stel het bericht in."""
        self.msg_label.setText(text)
