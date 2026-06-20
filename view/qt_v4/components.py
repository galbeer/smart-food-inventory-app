# view/qt_v4/components.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal

from .theme import C


class InventoryItemWidget(QFrame):
    """Widget voor een enkel item in de voorraadlijst."""
    clicked = pyqtSignal(str, str)
    decrease_clicked = pyqtSignal(str)
    increase_clicked = pyqtSignal(str)
    shopping_clicked = pyqtSignal(str)

    def __init__(self, barcode, name, count, added_date, parent=None):
        super().__init__(parent)
        self.barcode = barcode
        self.name = name

        self.setObjectName("item_card")
        self.setFrameShape(QFrame.StyledPanel)

        accent_color = C.RED if int(count) <= 1 else C.GREEN
        self.setStyleSheet(f"""
            QFrame#item_card {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-left: 4px solid {accent_color};
                border-radius: 8px;
            }}
            QLabel#item_name {{
                font-size: 17px;
                font-weight: bold;
                color: {C.TEXT};
            }}
            QLabel#item_barcode {{
                font-size: 12px;
                color: {C.TEXT2};
            }}
            QLabel#item_date {{
                font-size: 12px;
                color: {C.TEXT3};
            }}
            QLabel#count_label {{
                font-size: 22px;
                font-weight: bold;
                color: {accent_color};
            }}
            QPushButton {{
                border-radius: 8px;
                font-size: 17px;
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(8)

        name_label = QLabel(name)
        name_label.setObjectName("item_name")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        info_layout = QHBoxLayout()
        barcode_label = QLabel(f"#{barcode}")
        barcode_label.setObjectName("item_barcode")
        info_layout.addWidget(barcode_label)

        date_str = str(added_date)[:10] if added_date else "N.v.t."
        date_label = QLabel(date_str)
        date_label.setObjectName("item_date")
        info_layout.addStretch()
        info_layout.addWidget(date_label)
        layout.addLayout(info_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        btn_cart = QPushButton("Lijst")
        btn_cart.setStyleSheet(
            f"background-color: {C.ORANGE_BG}; color: {C.ORANGE}; "
            f"border: 1px solid {C.ORANGE}; min-height:48px; padding: 0 10px;"
        )
        btn_cart.clicked.connect(lambda: self.shopping_clicked.emit(self.barcode))
        controls_layout.addWidget(btn_cart, 1)

        btn_minus = QPushButton("-")
        btn_minus.setStyleSheet(
            f"background-color: {C.RED_BG}; color: {C.RED}; border: 1px solid {C.RED}; "
            "min-width:50px; max-width:50px; min-height:50px; max-height:50px;"
        )
        btn_minus.clicked.connect(lambda: self.decrease_clicked.emit(self.barcode))
        controls_layout.addWidget(btn_minus)

        self.lbl_count = QLabel(str(count))
        self.lbl_count.setObjectName("count_label")
        self.lbl_count.setAlignment(Qt.AlignCenter)
        self.lbl_count.setMinimumWidth(42)
        controls_layout.addWidget(self.lbl_count)

        btn_plus = QPushButton("+")
        btn_plus.setObjectName("primary")
        btn_plus.setStyleSheet(
            f"background-color: {C.GREEN}; color: white; border: none; "
            "min-width:50px; max-width:50px; min-height:50px; max-height:50px;"
        )
        btn_plus.clicked.connect(lambda: self.increase_clicked.emit(self.barcode))
        controls_layout.addWidget(btn_plus)

        layout.addLayout(controls_layout)

    def mouseReleaseEvent(self, event):
        child = self.childAt(event.pos())
        if event.button() == Qt.LeftButton and not isinstance(child, QPushButton):
            self.clicked.emit(self.barcode, self.name)
        super().mouseReleaseEvent(event)


class ShoppingListItemWidget(QFrame):
    """Widget voor een enkel item in de winkellijst."""
    toggle_clicked = pyqtSignal(str)
    remove_clicked = pyqtSignal(str)
    quantity_changed = pyqtSignal(str, int)

    def __init__(self, barcode, name, quantity, checked, parent=None):
        super().__init__(parent)
        self.barcode = barcode
        self.quantity = quantity
        self.checked = bool(checked)

        self.setObjectName("shopping_card")
        self.setFrameShape(QFrame.StyledPanel)

        accent = C.TEXT3 if self.checked else C.ORANGE
        text_color = C.TEXT3 if self.checked else C.TEXT

        self.setStyleSheet(f"""
            QFrame#shopping_card {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
            QPushButton {{
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(8)

        name_style = f"font-size: 17px; font-weight: bold; color: {text_color};"
        if self.checked:
            name_style += " text-decoration: line-through;"
        name_label = QLabel(name)
        name_label.setStyleSheet(name_style)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        barcode_label = QLabel(f"#{barcode}")
        barcode_label.setStyleSheet(f"font-size: 12px; color: {C.TEXT3};")
        layout.addWidget(barcode_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        btn_check = QPushButton("Vink af" if not self.checked else "Terug")
        check_bg = C.ORANGE if not self.checked else C.ELEVATED
        check_fg = "white" if not self.checked else C.TEXT2
        check_border = C.ORANGE if not self.checked else C.BORDER
        btn_check.setStyleSheet(
            f"background-color: {check_bg}; color: {check_fg}; border: 1px solid {check_border}; "
            "min-height:48px; padding: 0 8px;"
        )
        btn_check.clicked.connect(lambda: self.toggle_clicked.emit(self.barcode))
        controls_layout.addWidget(btn_check, 1)

        btn_qty_minus = QPushButton("-")
        btn_qty_minus.setStyleSheet(
            f"background-color: {C.ELEVATED}; color: {C.TEXT}; border: 1px solid {C.BORDER}; "
            "min-width:42px; max-width:42px; min-height:48px; max-height:48px;"
        )
        btn_qty_minus.clicked.connect(lambda: self._change_quantity(-1))
        controls_layout.addWidget(btn_qty_minus)

        self.qty_label = QLabel(str(quantity))
        self.qty_label.setAlignment(Qt.AlignCenter)
        self.qty_label.setMinimumWidth(30)
        self.qty_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {C.ORANGE};")
        controls_layout.addWidget(self.qty_label)

        btn_qty_plus = QPushButton("+")
        btn_qty_plus.setStyleSheet(
            f"background-color: {C.ORANGE}; color: white; border: none; "
            "min-width:42px; max-width:42px; min-height:48px; max-height:48px;"
        )
        btn_qty_plus.clicked.connect(lambda: self._change_quantity(1))
        controls_layout.addWidget(btn_qty_plus)

        btn_delete = QPushButton("Wis")
        btn_delete.setStyleSheet(
            f"background-color: {C.RED_BG}; color: {C.RED}; border: 1px solid {C.RED}; "
            "min-width:50px; min-height:48px;"
        )
        btn_delete.clicked.connect(lambda: self.remove_clicked.emit(self.barcode))
        controls_layout.addWidget(btn_delete)

        layout.addLayout(controls_layout)

    def _change_quantity(self, delta):
        """Pas het aantal aan en emit signal."""
        new_qty = max(1, self.quantity + delta)
        self.quantity = new_qty
        self.qty_label.setText(str(new_qty))
        self.quantity_changed.emit(self.barcode, new_qty)
