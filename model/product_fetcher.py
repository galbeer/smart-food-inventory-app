# model/product_fetcher.py
"""API-fetcher om productgegevens online op te zoeken via OpenFoodFacts."""

from abc import ABC, abstractmethod
from .exceptions import InvalidBarcode

try:
    import requests
except ImportError:
    requests = None


class ProductFetcher(ABC):
    """Abstracte basisklasse voor het ophalen van productinformatie."""
    @abstractmethod
    def fetch_name(self, barcode):
        """Haalt de naam van een product op via de barcode."""
        pass


class OpenFoodFactsFetcher(ProductFetcher):
    """Haalt productnamen op via de OpenFoodFacts API met een korte GUI-vriendelijke timeout."""
    def __init__(self, timeout=(1.0, 2.0)):
        """Initialiseert de fetcher met een specifieke timeout (connect, read)."""
        self._timeout = timeout
        self._session = requests.Session() if requests else None

    def fetch_name(self, barcode):
        """Zoekt de naam van het product online op.

        Mocht de API offline zijn of het netwerk traag, dan faalt dit snel
        om de GUI niet te blokkeren.
        """
        if not barcode:
            raise InvalidBarcode("Geen barcode opgegeven.")

        if self._session is None:
            print("DEBUG: requests niet beschikbaar; online lookup overgeslagen")
            return None

        # API-URL met parameters voor Nederlandse taalvoorkeur
        url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json?lc=nl&tags_lc=nl"
        headers = {
            "User-Agent": (
                "MijnVoorraadApp/1.0 "
                "(Raspberry Pi; Contact: lander.berghmans@leerling.sintlambertus.be)"
            )
        }

        try:
            response = self._session.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                product = data.get("product", {})
                # Probeer eerst de Nederlandse naam, daarna de algemene naam
                name = (
                    product.get("product_name_nl")
                    or product.get("product_name")
                    or product.get("generic_name_nl")
                    or product.get("generic_name")
                )
                return name if name else "Onbekend product"

            return None
        except Exception as e:
            # Vang netwerk- en verbindingstime-outs op
            if requests and isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                print(f"DEBUG: Netwerkfout voor {barcode}")
                return None
            print(f"DEBUG: Fetcher fout voor {barcode}: {e}")
            return None

