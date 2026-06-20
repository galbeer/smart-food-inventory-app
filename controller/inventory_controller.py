# controller/inventory_controller.py
"""InventoryController die gebruikersacties uit de View omzet naar Model-operaties."""

from model.exceptions import InventoryError, NetworkError


class InventoryController:
    def __init__(self, model, view):
        """Initialiseert de controller met het model en de view."""
        self._model = model
        self._view = view

    def add(self, barcode):
        """Voegt een product toe aan de voorraad op basis van zijn barcode."""
        try:
            success = self._model.add_barcode(barcode)
            
            if not success:
                # Als het product online niet wordt gevonden, open de handmatige invoer
                self._view.open_manual_input_popup(barcode)
                
        except NetworkError:
            # Bij een netwerkfout openen we direct de handmatige invoer
            print("Netwerk traag/fout: open handmatige invoer.")
            self._view.open_manual_input_popup(barcode)
            
        except InventoryError as e:
            # Toon foutmelding bij overige inventaris-fouten
            self._view.show_message(f"Fout: {e}")

    def decrease(self, barcode):
        """Verlaagt het aantal van een product met 1."""
        try:
            self._model.decrease_barcode(barcode)
        except InventoryError as e:
            self._view.show_message(f"Fout bij verbruiken: {e}")

    def delete(self, barcode):
        """Verwijdert een product volledig uit de voorraad."""
        try:
            self._model.remove_barcode(barcode)
        except InventoryError as e:
            self._view.show_message(f"Fout bij verwijderen: {e}")

    def get_all(self):
        """Haalt een overzicht op van de volledige voorraad."""
        return self._model.get_inventory_overview()
    
    def rename_product(self, barcode, new_name):
        """Hernoemt een product in de database en het model."""
        try:
            self._model.rename_item(barcode, new_name)
        except InventoryError as e:
            self._view.show_message(f"Fout bij hernoemen: {e}")

    def add_custom(self, barcode, name):
        """Voegt een handmatig ingevoerd product toe."""
        try:
            self._model.add_custom_product(barcode, name)
        except InventoryError as e:
            self._view.show_message(f"Fout bij toevoegen: {e}")

    # ── Winkellijst ──────────────────────────────────────────────────────────

    def add_to_shopping_list(self, barcode):
        """Voegt een product toe aan de winkellijst."""
        try:
            self._model.add_to_shopping_list(barcode)
            self._view.show_message("Product toegevoegd aan winkellijst!")
        except Exception as e:
            self._view.show_message(f"Fout: {e}")

    def toggle_shopping_item(self, barcode):
        """Vinkt een winkellijst-item aan of uit."""
        self._model.toggle_shopping_item(barcode)

    def remove_from_shopping_list(self, barcode):
        """Verwijdert een item van de winkellijst."""
        self._model.remove_from_shopping_list(barcode)

    def clear_shopping_list(self):
        """Leegt de volledige winkellijst."""
        self._model.clear_shopping_list()

    def get_shopping_list(self):
        """Haalt de huidige winkellijst op."""
        return self._model.get_shopping_list()

    def update_shopping_quantity(self, barcode, quantity):
        """Werkt het gewenste aantal van een item op de winkellijst bij."""
        self._model.update_shopping_quantity(barcode, quantity)