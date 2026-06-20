# model/exceptions.py

class InventoryError(Exception):
    """Basis klasse voor alle inventory fouten."""
    pass

class InvalidBarcode(InventoryError):
    """Werpt wanneer barcode leeg of ongeldig is."""
    pass

class BarcodeNotFound(InventoryError):
    """Werpt wanneer een te verwijderen barcode niet bestaat."""
    pass

class ProductFetchError(InventoryError):
    """Basis voor fouten tijdens het ophalen van externe data."""
    pass

class NetworkError(ProductFetchError):
    """Werpt wanneer er geen internet is of de server niet reageert."""
    pass

class APIError(ProductFetchError):
    """Werpt wanneer de API een foutcode (bv. 500) teruggeeft."""
    pass