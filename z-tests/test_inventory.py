# tests/test_inventory.py

import unittest
from model.inventory_model import InventoryModel
from database.db_manager import DatabaseManager
from model.product_fetcher import ProductFetcher

class FakeFetcher(ProductFetcher):
    def fetch_name(self, barcode):
        return "Test Product" if barcode == "123" else None

class TestInventoryFase2(unittest.TestCase):
    def setUp(self):
        # Door DatabaseManager te behouden in self.db, blijft de :memory: verbinding open
        self.db = DatabaseManager(":memory:")
        self.fetcher = FakeFetcher()
        self.model = InventoryModel(db_manager=self.db, fetcher=self.fetcher)

    def test_add_product_with_name(self):
        self.model.add_barcode("123")
        overview = self.model.get_inventory_overview()
        self.assertEqual(overview["123"]["name"], "Test Product")

    def test_persistence(self):
        self.model.add_barcode("123")
        items = self.db.get_all_items()
        self.assertEqual(items[0][1], "Test Product")

if __name__ == '__main__':
    unittest.main()

#python -m unittest z-tests/test_inventory.py