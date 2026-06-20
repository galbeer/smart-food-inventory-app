# model/inventory_model.py
"""Model voor het voorraadbeheersysteem.

Beheert de business logica van de voorraad en de winkellijst, en communiceert
met de database (DatabaseManager) en de API-fetcher.
"""

from datetime import datetime
from threading import RLock

from .exceptions import BarcodeNotFound, InvalidBarcode
from .patterns import Subject
from .product_fetcher import OpenFoodFactsFetcher


class InventoryItem:
    """Klasse die een individueel product in de voorraad vertegenwoordigt."""
    def __init__(self, barcode, name="Onbekend Product", added_date=None):
        """Initialiseert een voorraaditem."""
        self._barcode = barcode
        self._name = name
        self._count = 1
        self._added_date = added_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_count(self):
        """Retourneert het huidige aantal in voorraad."""
        return self._count

    def get_barcode(self):
        """Retourneert de barcode van het product."""
        return self._barcode

    def get_name(self):
        """Retourneert de naam van het product."""
        return self._name

    def get_added_date(self):
        """Retourneert de datum waarop het product voor het eerst werd toegevoegd."""
        return self._added_date

    def set_name(self, name):
        """Stelt een nieuwe naam in voor het product."""
        self._name = name

    def __iadd__(self, value):
        """Ondersteunt de += operator om het aantal te verhogen."""
        if isinstance(value, int):
            self._count += value
            return self
        return NotImplemented

    def __isub__(self, value):
        """Ondersteunt de -= operator om het aantal te verlagen (minimaal 0)."""
        if isinstance(value, int):
            self._count -= value
            if self._count < 0:
                self._count = 0
            return self
        return NotImplemented


class InventoryModel(Subject):
    """Model dat de gehele voorraad beheert en observers waarschuwt bij wijzigingen."""
    def __init__(self, db_manager=None, fetcher=None):
        """Initialiseert het model en laadt bestaande voorraad in uit de database."""
        super().__init__()
        self._db = db_manager
        self._fetcher = fetcher or OpenFoodFactsFetcher()
        self._items = {}
        self._lock = RLock()  # RLock voor thread-safe bewerkingen

        if self._db:
            self._load_from_db()

    def _load_from_db(self):
        """Laadt alle voorraadgegevens in vanuit de SQLite database."""
        rows = self._db.get_all_items()
        with self._lock:
            for barcode, name, count, added_date in rows:
                item = InventoryItem(barcode, name, added_date=added_date)
                item._count = count
                self._items[barcode] = item

    def _validate_barcode(self, barcode):
        """Valideert of een barcode bruikbaar is."""
        if not barcode or not str(barcode).strip():
            raise InvalidBarcode("Lege of ongeldige barcode.")

    def _normalise_barcode(self, barcode):
        """Valideert en normaliseert de barcode (witte regels verwijderen)."""
        self._validate_barcode(barcode)
        return str(barcode).strip()

    def _notify_inventory_changed(self):
        """Stelt alle gekoppelde observers (zoals de View) op de hoogte."""
        self.notify(self.get_inventory_overview())

    def _save_current_item(self, barcode):
        """Slaat de huidige staat van een product op in de database."""
        item = self._items[barcode]
        if self._db:
            self._db.update_item(
                barcode,
                item.get_name(),
                item.get_count(),
                item.get_added_date(),
            )

    def add_barcode(self, barcode):
        """Voegt een product toe aan de voorraad.

        Als het product al bestaat, wordt het aantal verhoogd met 1.
        Als het nieuw is, wordt de naam lokaal of via de API gezocht.
        """
        key = self._normalise_barcode(barcode)

        with self._lock:
            if key in self._items:
                self._items[key] += 1
                self._save_current_item(key)
                changed = True
            else:
                changed = False

        if changed:
            self._notify_inventory_changed()
            return True

        # Stap 1: Probeer de naam lokaal/offline te vinden
        name = self._db.get_local_product_name(key) if self._db else None

        # Stap 2: Probeer de naam online via de API op te halen
        if not name:
            try:
                name = self._fetcher.fetch_name(key)
            except Exception:
                name = None

        # Geen naam gevonden -> View moet handmatig invoerveld openen
        if not name:
            return False

        with self._lock:
            # Controleer of een andere thread dit item intussen heeft toegevoegd
            if key in self._items:
                self._items[key] += 1
            else:
                self._items[key] = InventoryItem(key, name)
            self._save_current_item(key)

        self._notify_inventory_changed()
        return True

    def add_custom_product(self, barcode, name):
        """Voegt een product met een handmatig opgegeven naam toe."""
        key = self._normalise_barcode(barcode)
        clean_name = str(name).strip()
        if not clean_name:
            raise InvalidBarcode("Productnaam mag niet leeg zijn.")

        with self._lock:
            if key in self._items:
                item = self._items[key]
                item.set_name(clean_name)
            else:
                item = InventoryItem(key, clean_name)
                self._items[key] = item

            if self._db:
                self._db.update_item(key, clean_name, item.get_count(), item.get_added_date())
                if hasattr(self._db, "add_to_local_products"):
                    self._db.add_to_local_products(key, clean_name)

        self._notify_inventory_changed()

    def decrease_barcode(self, barcode):
        """Verlaagt het aantal van een product met 1. Verwijdert het als count=0."""
        key = self._normalise_barcode(barcode)

        with self._lock:
            if key not in self._items:
                return

            self._items[key] -= 1
            item = self._items[key]

            if item.get_count() <= 0:
                del self._items[key]
                if self._db:
                    self._db.delete_item(key)
            else:
                self._save_current_item(key)

        self._notify_inventory_changed()

    def remove_barcode(self, barcode):
        """Verwijdert een product direct en volledig uit de voorraad."""
        key = self._normalise_barcode(barcode)

        with self._lock:
            if key not in self._items:
                return
            del self._items[key]
            if self._db:
                self._db.delete_item(key)

        self._notify_inventory_changed()

    def rename_item(self, barcode, new_name):
        """Wijzigt de naam van een bestaand product en slaat dit lokaal op."""
        key = self._normalise_barcode(barcode)
        clean_name = str(new_name).strip()
        if not clean_name:
            raise InvalidBarcode("Productnaam mag niet leeg zijn.")

        with self._lock:
            if key not in self._items:
                raise BarcodeNotFound(f"Barcode {key} niet gevonden.")
            item = self._items[key]
            item.set_name(clean_name)
            self._save_current_item(key)
            if self._db and hasattr(self._db, "add_to_local_products"):
                self._db.add_to_local_products(key, clean_name)

        self._notify_inventory_changed()

    def get_inventory_overview(self):
        """Retourneert een overzichtelijke dictionary van de gehele voorraad."""
        with self._lock:
            return {
                k: {
                    "name": v.get_name(),
                    "count": v.get_count(),
                    "added_date": v.get_added_date(),
                }
                for k, v in self._items.items()
            }

    # ── Winkellijst ──────────────────────────────────────────────────────────

    def add_to_shopping_list(self, barcode):
        """Voegt een product uit de voorraad toe aan de winkellijst."""
        key = self._normalise_barcode(barcode)
        with self._lock:
            if key in self._items:
                name = self._items[key].get_name()
            else:
                name = "Onbekend product"
        if self._db:
            self._db.add_to_shopping_list(key, name)

    def get_shopping_list(self):
        """Haalt de winkellijst op uit de database."""
        if self._db:
            return self._db.get_shopping_list()
        return []

    def toggle_shopping_item(self, barcode):
        """Wisselt de checked-status van een item op de winkellijst."""
        if self._db:
            self._db.toggle_shopping_item(self._normalise_barcode(barcode))

    def remove_from_shopping_list(self, barcode):
        """Verwijdert een item van de winkellijst."""
        if self._db:
            self._db.remove_from_shopping_list(self._normalise_barcode(barcode))

    def clear_shopping_list(self):
        """Wist alle items van de winkellijst."""
        if self._db:
            self._db.clear_shopping_list()

    def is_on_shopping_list(self, barcode):
        """Controleert of een product op de winkellijst staat."""
        if self._db:
            return self._db.is_on_shopping_list(self._normalise_barcode(barcode))
        return False

    def update_shopping_quantity(self, barcode, quantity):
        """Werkt de gewenste hoeveelheid van een item op de winkellijst bij."""
        if self._db:
            self._db.update_shopping_quantity(self._normalise_barcode(barcode), quantity)

