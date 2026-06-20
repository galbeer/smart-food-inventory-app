# main.py
"""Hoofdingang van het Slim Voedselvoorraadbeheersysteem.

Dit script initialiseert het databasebeheer, het model (met API-fetcher),
de Qt5-gebruikersinterface en de controller volgens het MVC-patroon.
"""

import sys
from database.db_manager import DatabaseManager
from model.inventory_model import InventoryModel
from model.product_fetcher import OpenFoodFactsFetcher
from controller.inventory_controller import InventoryController
from view.qt_v4.qt_view import QtView


def main():
    # 1. Initialiseer de database (inventory.db)
    db = DatabaseManager("inventory.db")

    # 2. Initialiseer de API fetcher voor online barcode opzoekingen
    api_fetcher = OpenFoodFactsFetcher()

    # 3. Initialiseer het model dat de business logica beheert
    model = InventoryModel(db_manager=db, fetcher=api_fetcher)

    # 4. Initialiseer de Qt5 GUI view
    view = QtView(model=model)

    # 5. Koppel de controller aan het model en de view
    controller = InventoryController(model, view)
    view.controller = controller  # Geef de view toegang tot de controller

    # 6. Registreer de view als Observer van het model voor automatische updates
    model.attach(view)

    # 7. Start de grafische gebruikersinterface
    if hasattr(view, 'run_view'):
        view.run_view()


if __name__ == "__main__":
    main()
