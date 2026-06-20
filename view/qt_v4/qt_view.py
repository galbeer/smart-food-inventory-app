# view/qt_v4/qt_view.py
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
    QLineEdit, QLabel
)
from PyQt5.QtCore import (
    Qt, QTimer, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
)

from model.exceptions import InventoryError
from model.patterns import Observer
from .theme import GLOBAL_QSS
from .pages import MenuPage, AddPage, ListPage, ShoppingListPage
from .dialogs import ManualInputPage, EditProductPage, NotificationPage
from .keyboard import VirtualKeyboard


class AddBarcodeSignals(QObject):
    added = pyqtSignal(str)
    unknown = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(str)


class AddBarcodeWorker(QRunnable):
    """Voert een barcode-toevoeging buiten de GUI-thread uit."""
    def __init__(self, model, barcode):
        super().__init__()
        self.model = model
        self.barcode = barcode
        self.signals = AddBarcodeSignals()

    @pyqtSlot()
    def run(self):
        try:
            success = self.model.add_barcode(self.barcode)
            if success:
                self.signals.added.emit(self.barcode)
            else:
                self.signals.unknown.emit(self.barcode)
        except InventoryError as e:
            self.signals.error.emit(f"Fout: {e}")
        except Exception as e:
            self.signals.error.emit(f"Onverwachte fout: {e}")
        finally:
            self.signals.finished.emit(self.barcode)


class MainWindow(QMainWindow):
    refresh_requested = pyqtSignal()
    message_requested = pyqtSignal(str)
    manual_input_requested = pyqtSignal(str)

    def __init__(self, controller, model):
        super().__init__()
        self.controller = controller
        self.model = model
        self._active_input = None
        self._return_page = None
        self._pending_adds = 0

        self.worker_pool = QThreadPool()
        self.worker_pool.setMaxThreadCount(1)

        self.setWindowTitle("Voorraadbeheer")
        self.setStyleSheet(GLOBAL_QSS)
        self.setMinimumSize(480, 800)
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        # self.showFullScreen()  # Aanzetten op de Raspberry Pi in productie.

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.keyboard = VirtualKeyboard()
        self.main_layout.addWidget(self.keyboard)

        self.menu_page = MenuPage()
        self.add_page = AddPage()
        self.list_page = ListPage()
        self.shopping_page = ShoppingListPage()

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.add_page)
        self.stack.addWidget(self.list_page)
        self.stack.addWidget(self.shopping_page)

        self.manual_input_page = ManualInputPage()
        self.edit_product_page = EditProductPage()
        self.notification_page = NotificationPage()

        self.stack.addWidget(self.manual_input_page)
        self.stack.addWidget(self.edit_product_page)
        self.stack.addWidget(self.notification_page)

        self._setup_toast()
        self.setup_connections()

        self.refresh_requested.connect(self.refresh_visible_data)
        self.message_requested.connect(self.show_toast)
        self.manual_input_requested.connect(self.open_manual_input_page)

        QApplication.instance().focusChanged.connect(self.on_focus_changed)
        self.keyboard.key_pressed.connect(self.on_key_pressed)
        self.keyboard.backspace_pressed.connect(self.on_backspace)
        self.keyboard.enter_pressed.connect(self.on_enter_pressed)

        self.refresh_menu_stats()

    def setup_connections(self):
        self.menu_page.go_add.connect(lambda: self.switch_page(self.add_page))
        self.menu_page.go_list.connect(lambda: self.switch_page(self.list_page))
        self.menu_page.go_shopping.connect(lambda: self.switch_page(self.shopping_page))
        self.menu_page.quit_app.connect(QApplication.quit)

        self.add_page.btn_back.clicked.connect(lambda: self.switch_page(self.menu_page))
        self.list_page.btn_back.clicked.connect(lambda: self.switch_page(self.menu_page))
        self.shopping_page.btn_back.clicked.connect(lambda: self.switch_page(self.menu_page))

        self.add_page.add_requested.connect(self.on_add_requested)
        self.add_page.manual_entry_requested.connect(self.show_manual_barcode_keyboard)

        self.list_page.item_decrease.connect(self.controller.decrease)
        self.list_page.item_increase.connect(self.controller.add)
        self.list_page.item_edit.connect(self.open_edit_page)
        self.list_page.sort_changed.connect(lambda _: self.refresh_list())
        self.list_page.search_changed.connect(lambda _: self.refresh_list())
        self.list_page.item_shopping.connect(self.on_add_to_shopping_list)

        self.shopping_page.item_toggle.connect(self.on_shopping_toggle)
        self.shopping_page.item_remove.connect(self.on_shopping_remove)
        self.shopping_page.item_quantity.connect(self.on_shopping_quantity)
        self.shopping_page.clear_all.connect(self.on_shopping_clear)

        self.manual_input_page.name_submitted.connect(self.on_manual_name_submitted)
        self.manual_input_page.cancelled.connect(self.return_to_previous)

        self.edit_product_page.name_saved.connect(self.on_product_name_saved)
        self.edit_product_page.delete_requested.connect(self.on_product_delete)
        self.edit_product_page.cancelled.connect(self.return_to_previous)

        self.notification_page.dismissed.connect(self.return_to_previous)

    # Pagina navigatie

    def switch_page(self, page):
        """Navigeer naar een pagina en verberg het toetsenbord."""
        self.stack.setCurrentWidget(page)
        self.keyboard.hide_keyboard()
        self._active_input = None

        if page == self.menu_page:
            self.refresh_menu_stats()
        elif page == self.list_page:
            self.refresh_list()
        elif page == self.add_page:
            self.add_page.set_busy(self._pending_adds > 0, self._pending_adds)
            self.add_page.barcode_input.setFocus()
        elif page == self.shopping_page:
            self.refresh_shopping_list()

    def return_to_previous(self):
        """Keer terug naar de pagina van voor de dialog."""
        target = self._return_page or self.menu_page
        self._return_page = None
        self.switch_page(target)

    # Toastmeldingen

    def _setup_toast(self):
        self.toast_label = QLabel(self.central)
        self.toast_label.setObjectName("toast")
        self.toast_label.setWordWrap(True)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toast_label.hide()

        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast_label.hide)

    def show_toast(self, text, duration=2200):
        self.toast_label.setText(text)
        max_width = max(260, self.central.width() - 32)
        self.toast_label.setMaximumWidth(max_width)
        self.toast_label.adjustSize()
        hint = self.toast_label.sizeHint()
        width = min(max_width, max(240, hint.width() + 28))
        height = hint.height() + 18
        self.toast_label.resize(width, height)
        self._position_toast()
        self.toast_label.show()
        self.toast_label.raise_()
        self.toast_timer.start(duration)

    def _position_toast(self):
        if not hasattr(self, "toast_label"):
            return
        kb_height = self.keyboard.maximumHeight() if hasattr(self, "keyboard") else 0
        x = max(16, (self.central.width() - self.toast_label.width()) // 2)
        y = max(12, self.central.height() - kb_height - self.toast_label.height() - 16)
        self.toast_label.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_toast()

    # Dialog-pagina openers

    def open_edit_page(self, barcode, name):
        self._return_page = self.list_page
        self.edit_product_page.set_product(barcode, name)
        self.keyboard.hide_keyboard()
        self._active_input = None
        self.stack.setCurrentWidget(self.edit_product_page)
        self.edit_product_page.name_input.setFocus()

    def open_manual_input_page(self, barcode):
        self._return_page = self.add_page
        self.manual_input_page.set_barcode(barcode)
        self.stack.setCurrentWidget(self.manual_input_page)
        self.manual_input_page.name_input.setFocus()

    def show_notification(self, text):
        self.show_toast(text)

    # Add flow

    def on_add_requested(self, barcode):
        self._pending_adds += 1
        self.add_page.set_busy(True, self._pending_adds)

        worker = AddBarcodeWorker(self.model, barcode)
        worker.signals.added.connect(self.on_barcode_added)
        worker.signals.unknown.connect(self.on_barcode_unknown)
        worker.signals.error.connect(self.show_toast)
        worker.signals.finished.connect(self.on_add_finished)
        self.worker_pool.start(worker)

    def on_barcode_added(self, barcode):
        info = self.model.get_inventory_overview().get(barcode, {})
        name = info.get("name") or "Product"
        self.add_page.show_scan_success(name)
        self.show_toast(f"{name} toegevoegd")
        self.refresh_visible_data()

    def on_barcode_unknown(self, barcode):
        self.add_page.set_status("Productnaam nodig")
        self.open_manual_input_page(barcode)

    def on_add_finished(self, barcode):
        self._pending_adds = max(0, self._pending_adds - 1)
        self.add_page.set_busy(self._pending_adds > 0, self._pending_adds)
        if self.stack.currentWidget() == self.add_page:
            self.add_page.barcode_input.setFocus()

    def show_manual_barcode_keyboard(self):
        self._active_input = self.add_page.barcode_input
        self.add_page.barcode_input.setFocus()
        self.keyboard.show_keyboard(numeric=True)

    # Dialog resultaat-handlers

    def on_manual_name_submitted(self, barcode, name):
        self.controller.add_custom(barcode, name)
        self.add_page.show_scan_success(name)
        self.show_toast(f"{name} opgeslagen")
        self.return_to_previous()

    def on_product_name_saved(self, barcode, new_name):
        self.controller.rename_product(barcode, new_name)
        self.show_toast("Productnaam opgeslagen")
        self.return_to_previous()

    def on_product_delete(self, barcode):
        self.controller.delete(barcode)
        self.show_toast("Product verwijderd")
        self.return_to_previous()

    # Voorraadlijst

    def refresh_visible_data(self):
        current = self.stack.currentWidget()
        if current == self.menu_page:
            self.refresh_menu_stats()
        elif current == self.list_page:
            self.refresh_list()
        elif current == self.shopping_page:
            self.refresh_shopping_list()

    def refresh_menu_stats(self):
        data = self.model.get_inventory_overview()
        product_count = len(data)
        unit_count = sum(info.get("count", 0) for info in data.values())
        shopping_items = self.model.get_shopping_list()
        shopping_open = sum(1 for _, _, _, checked, _ in shopping_items if not checked)
        self.menu_page.set_summary(product_count, unit_count, shopping_open)

    def refresh_list(self):
        data = self.model.get_inventory_overview()
        search_term = self.list_page.search_input.text().lower().strip()
        sort_mode = "az"
        for btn, code in self.list_page.filters:
            if btn.isChecked():
                sort_mode = code
                break

        items = [
            (code, info) for code, info in data.items()
            if search_term in (info.get("name") or "").lower() or search_term in str(code)
        ]

        if sort_mode == "az":
            items.sort(key=lambda x: (x[1].get("name") or "").lower())
        elif sort_mode == "19":
            items.sort(key=lambda x: x[1]["count"])
        elif sort_mode == "91":
            items.sort(key=lambda x: x[1]["count"], reverse=True)
        elif sort_mode == "new":
            items.sort(key=lambda x: x[1].get("added_date") or "", reverse=True)

        self.list_page.refresh_list(items)

    # Winkellijst

    def refresh_shopping_list(self):
        items = self.model.get_shopping_list()
        self.shopping_page.refresh_list(items)

    def on_add_to_shopping_list(self, barcode):
        self.controller.add_to_shopping_list(barcode)
        self.refresh_menu_stats()

    def on_shopping_toggle(self, barcode):
        self.controller.toggle_shopping_item(barcode)
        self.refresh_shopping_list()
        self.refresh_menu_stats()

    def on_shopping_remove(self, barcode):
        self.controller.remove_from_shopping_list(barcode)
        self.refresh_shopping_list()
        self.refresh_menu_stats()

    def on_shopping_quantity(self, barcode, quantity):
        self.controller.update_shopping_quantity(barcode, quantity)

    def on_shopping_clear(self):
        self.controller.clear_shopping_list()
        self.refresh_shopping_list()
        self.refresh_menu_stats()
        self.show_toast("Winkellijst geleegd")

    # Toetsenbord management

    def on_focus_changed(self, old, new):
        if isinstance(new, QLineEdit):
            self._active_input = new
            if new.property("virtualKeyboard") is False:
                return
            is_numeric = (new == self.add_page.barcode_input)
            self.keyboard.show_keyboard(numeric=is_numeric)

    def on_key_pressed(self, char):
        if self._active_input and self._active_input.isVisible():
            self._active_input.insert(char)

    def on_backspace(self):
        if self._active_input and self._active_input.isVisible():
            self._active_input.backspace()

    def on_enter_pressed(self):
        if self._active_input and self._active_input.isVisible():
            self._active_input.returnPressed.emit()
        self.keyboard.hide_keyboard()


class QtView(Observer):
    def __init__(self, model):
        self.model = model
        self.controller = None
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = None

    def run_view(self):
        self.window = MainWindow(self.controller, self.model)
        self.window.show()
        sys.exit(self.app.exec_())

    def update(self, inventory_overview):
        if self.window:
            self.window.refresh_requested.emit()

    def show_message(self, text):
        if self.window:
            self.window.message_requested.emit(text)

    def open_manual_input_popup(self, barcode):
        if self.window:
            self.window.manual_input_requested.emit(barcode)
