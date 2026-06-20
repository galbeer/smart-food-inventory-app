# view/qt_v4/pages.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QFrame, QScroller
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from .theme import C
from .components import InventoryItemWidget, ShoppingListItemWidget


def enable_touch_scroll(scroll_area):
    """Maakt scrolllijsten prettiger op een touchscherm."""
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    QScroller.grabGesture(scroll_area.viewport(), QScroller.LeftMouseButtonGesture)


class BasePage(QWidget):
    """Basis klasse voor schermen met een topbalk."""
    def __init__(self, title, show_back=True, header_color=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        bg_color = header_color or C.GREEN_DK
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setStyleSheet(f"background-color: {bg_color}; border: none;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 0, 14, 0)
        header_layout.setSpacing(10)

        if show_back:
            self.btn_back = QPushButton("<")
            self.btn_back.setFixedSize(48, 48)
            self.btn_back.setStyleSheet(
                "font-size: 24px; font-weight: bold; "
                "background: transparent; border: none; color: white;"
            )
            header_layout.addWidget(self.btn_back)
        else:
            header_layout.addSpacing(48)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_lbl, 1)

        self.layout.addWidget(self.header)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(12)
        self.layout.addWidget(self.content, 1)


class MenuPage(BasePage):
    go_add = pyqtSignal()
    go_list = pyqtSignal()
    go_shopping = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Mijn Voorraad", show_back=False, parent=parent)

        hero = QWidget()
        hero.setFixedHeight(112)
        hero.setStyleSheet(f"background-color: {C.GREEN_DK};")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 18, 24, 16)
        hero_layout.setSpacing(4)

        main_title = QLabel("Voorraadbeheer")
        main_title.setObjectName("title")
        main_title.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(main_title)

        self.summary_label = QLabel("0 producten | 0 stuks")
        self.summary_label.setObjectName("subtitle")
        self.summary_label.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(self.summary_label)

        self.layout.insertWidget(0, hero)
        self.header.hide()

        self.content_layout.setSpacing(12)

        self.shopping_summary = QLabel("Winkellijst leeg")
        self.shopping_summary.setAlignment(Qt.AlignCenter)
        self.shopping_summary.setStyleSheet(f"font-size: 14px; color: {C.TEXT2};")
        self.content_layout.addWidget(self.shopping_summary)

        btn_add = QPushButton("Scan product")
        btn_add.setObjectName("primary")
        btn_add.setFixedHeight(74)
        btn_add.clicked.connect(self.go_add.emit)
        self.content_layout.addWidget(btn_add)

        btn_list = QPushButton("Voorraadlijst")
        btn_list.setFixedHeight(70)
        btn_list.clicked.connect(self.go_list.emit)
        self.content_layout.addWidget(btn_list)

        btn_shopping = QPushButton("Winkellijst")
        btn_shopping.setFixedHeight(70)
        btn_shopping.setStyleSheet(f"""
            QPushButton {{
                background-color: {C.ORANGE_BG};
                color: {C.ORANGE};
                border: 2px solid {C.ORANGE};
                border-radius: 8px;
                font-size: 17px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:pressed {{
                background-color: {C.ORANGE_DK};
                color: white;
            }}
        """)
        btn_shopping.clicked.connect(self.go_shopping.emit)
        self.content_layout.addWidget(btn_shopping)

        self.content_layout.addStretch()

        btn_exit = QPushButton("Afsluiten")
        btn_exit.setObjectName("danger")
        btn_exit.setFixedHeight(54)
        btn_exit.clicked.connect(self.quit_app.emit)
        self.content_layout.addWidget(btn_exit)

    def set_summary(self, product_count, unit_count, shopping_open):
        product_text = "1 product" if product_count == 1 else f"{product_count} producten"
        unit_text = "1 stuk" if unit_count == 1 else f"{unit_count} stuks"
        self.summary_label.setText(f"{product_text} | {unit_text}")

        if shopping_open == 0:
            self.shopping_summary.setText("Winkellijst leeg")
        elif shopping_open == 1:
            self.shopping_summary.setText("1 item op winkellijst")
        else:
            self.shopping_summary.setText(f"{shopping_open} items op winkellijst")


class AddPage(BasePage):
    add_requested = pyqtSignal(str)
    manual_entry_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Toevoegen", parent=parent)

        prompt = QLabel("Scanner gereed")
        prompt.setObjectName("section")
        prompt.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(prompt)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode")
        self.barcode_input.setAlignment(Qt.AlignCenter)
        self.barcode_input.setProperty("virtualKeyboard", False)
        self.barcode_input.setInputMethodHints(Qt.ImhDigitsOnly)
        self.barcode_input.returnPressed.connect(self.on_submit)
        self.content_layout.addWidget(self.barcode_input)

        self.btn_confirm = QPushButton("Toevoegen")
        self.btn_confirm.setObjectName("primary")
        self.btn_confirm.setFixedHeight(58)
        self.btn_confirm.clicked.connect(self.on_submit)
        self.content_layout.addWidget(self.btn_confirm)

        self.btn_manual = QPushButton("Handmatig typen")
        self.btn_manual.setFixedHeight(52)
        self.btn_manual.clicked.connect(self.manual_entry_requested.emit)
        self.content_layout.addWidget(self.btn_manual)

        self.status_lbl = QLabel("Klaar om te scannen")
        self.status_lbl.setObjectName("subtitle")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.status_lbl)

        self.last_scan_lbl = QLabel("")
        self.last_scan_lbl.setAlignment(Qt.AlignCenter)
        self.last_scan_lbl.setWordWrap(True)
        self.last_scan_lbl.setStyleSheet(f"font-size: 16px; color: {C.GREEN_LT}; font-weight: bold;")
        self.content_layout.addWidget(self.last_scan_lbl)

        self.content_layout.addStretch()

    def on_submit(self):
        barcode = self.barcode_input.text().strip()
        if barcode:
            self.add_requested.emit(barcode)
            self.barcode_input.clear()
            self.barcode_input.setFocus()

    def set_busy(self, busy, pending=0):
        if busy:
            scan_text = "scan" if pending == 1 else "scans"
            self.status_lbl.setText(f"{pending} {scan_text} verwerken...")
        else:
            self.status_lbl.setText("Klaar om te scannen")

    def set_status(self, text):
        self.status_lbl.setText(text)

    def show_scan_success(self, name):
        self.last_scan_lbl.setText(name)


class ListPage(BasePage):
    search_changed = pyqtSignal(str)
    sort_changed = pyqtSignal(str)
    item_decrease = pyqtSignal(str)
    item_increase = pyqtSignal(str)
    item_edit = pyqtSignal(str, str)
    item_shopping = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Voorraadlijst", parent=parent)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Zoek product")
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.content_layout.addWidget(self.search_input)

        self.count_label = QLabel("0 producten")
        self.count_label.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        self.content_layout.addWidget(self.count_label)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.filters = []
        for label, code in [("A-Z", "az"), ("1-9", "19"), ("9-1", "91"), ("Nieuw", "new")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.setStyleSheet("font-size: 13px; padding: 0 10px; border-radius: 8px;")
            if code == "az":
                btn.setChecked(True)
            btn.clicked.connect(lambda _, c=code: self.on_filter_click(c))
            filter_layout.addWidget(btn)
            self.filters.append((btn, code))

        self.content_layout.addLayout(filter_layout)

        self.scroll = QScrollArea()
        enable_touch_scroll(self.scroll)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 8, 0, 8)
        self.scroll.setWidget(self.list_container)
        self.content_layout.addWidget(self.scroll)

    def on_filter_click(self, selected_code):
        for btn, code in self.filters:
            btn.setChecked(code == selected_code)
        self.sort_changed.emit(selected_code)

    def refresh_list(self, items):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(items)
        self.count_label.setText("1 product" if count == 1 else f"{count} producten")

        if not items:
            empty = QLabel("Geen producten gevonden")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(f"font-size: 15px; color: {C.TEXT3}; padding: 36px 12px;")
            self.list_layout.addWidget(empty)
            return

        for barcode, info in items:
            w = InventoryItemWidget(
                barcode,
                info["name"],
                info["count"],
                info.get("added_date"),
                self,
            )
            w.decrease_clicked.connect(self.item_decrease.emit)
            w.increase_clicked.connect(self.item_increase.emit)
            w.clicked.connect(self.item_edit.emit)
            w.shopping_clicked.connect(self.item_shopping.emit)
            self.list_layout.addWidget(w)


class ShoppingListPage(BasePage):
    """Pagina voor de winkellijst."""
    item_toggle = pyqtSignal(str)
    item_remove = pyqtSignal(str)
    item_quantity = pyqtSignal(str, int)
    clear_all = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Winkellijst", header_color=C.ORANGE_DK, parent=parent)
        self._clear_armed = False

        self.info_label = QLabel("Nog te kopen")
        self.info_label.setStyleSheet(f"font-size: 14px; color: {C.TEXT2};")
        self.content_layout.addWidget(self.info_label)

        self.count_label = QLabel("0 producten")
        self.count_label.setStyleSheet(f"font-size: 13px; color: {C.ORANGE}; font-weight: bold;")
        self.content_layout.addWidget(self.count_label)

        self.scroll = QScrollArea()
        enable_touch_scroll(self.scroll)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 8, 0, 8)
        self.scroll.setWidget(self.list_container)
        self.content_layout.addWidget(self.scroll)

        self.btn_clear = QPushButton("Lijst legen")
        self.btn_clear.setFixedHeight(54)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: {C.RED_BG};
                color: {C.RED};
                border: 1px solid {C.RED};
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:pressed {{
                background-color: {C.RED};
                color: white;
            }}
        """)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.content_layout.addWidget(self.btn_clear)

    def _on_clear_clicked(self):
        if not self._clear_armed:
            self._clear_armed = True
            self.btn_clear.setText("Nogmaals tikken")
            QTimer.singleShot(2500, self._reset_clear_button)
            return

        self._reset_clear_button()
        self.clear_all.emit()

    def _reset_clear_button(self):
        self._clear_armed = False
        self.btn_clear.setText("Lijst legen")

    def refresh_list(self, items):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._reset_clear_button()

        if not items:
            empty = QLabel("Je winkellijst is leeg")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(f"font-size: 15px; color: {C.TEXT3}; padding: 40px 12px;")
            self.list_layout.addWidget(empty)
            self.count_label.setText("0 producten")
            self.btn_clear.hide()
            return

        self.btn_clear.show()
        total = len(items)
        checked = sum(1 for _, _, _, c, _ in items if c)
        product_text = "1 product" if total == 1 else f"{total} producten"
        self.count_label.setText(f"{product_text} | {checked} afgevinkt")

        for barcode, name, quantity, checked, added_date in items:
            w = ShoppingListItemWidget(barcode, name, quantity, checked, self)
            w.toggle_clicked.connect(self.item_toggle.emit)
            w.remove_clicked.connect(self.item_remove.emit)
            w.quantity_changed.connect(self.item_quantity.emit)
            self.list_layout.addWidget(w)
