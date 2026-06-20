# database/db_manager.py
"""DatabaseManager voor het afhandelen van alle SQLite-databasebewerkingen.

Gebruikt RLock voor thread-safe bewerkingen aangezien de PyQt5 GUI threads gebruikt
om API-aanroepen en database-schrijfopdrachten asynchroon uit te voeren.
"""

import sqlite3
from threading import RLock


class DatabaseManager:
    def __init__(self, db_path="inventory.db"):
        """Constructor: zet de verbinding op en initialiseert de tabellen."""
        self._path = db_path
        self._lock = RLock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._configure_connection()
        self._init_db()

    def _configure_connection(self):
        """Stelt de SQLite verbinding in voor responsief thread-veilig gebruik."""
        with self._lock:
            # Voorkom SQLITE_BUSY fouten in een multi-threaded omgeving
            self._conn.execute("PRAGMA busy_timeout = 3000")
            self._conn.execute("PRAGMA foreign_keys = ON")
            if self._path != ":memory:":
                try:
                    # Gebruik WAL-modus voor betere concurrency bij lees/schrijf-acties
                    self._conn.execute("PRAGMA journal_mode = WAL")
                except sqlite3.Error as e:
                    print(f"Waarschuwing: WAL-modus niet beschikbaar: {e}")

    def _init_db(self):
        """Initialiseert de tabellen en voert lichte schema-migraties uit."""
        with self._lock:
            cursor = self._conn.cursor()

            # Tabel voor de actuele voorraad
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    barcode TEXT PRIMARY KEY,
                    name TEXT,
                    count INTEGER NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabel voor het offline opzoeken van namen (lokale database)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_products (
                    barcode TEXT PRIMARY KEY,
                    name TEXT
                )
            """)

            # Tabel voor de winkellijst
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_list (
                    barcode TEXT PRIMARY KEY,
                    name TEXT,
                    quantity INTEGER DEFAULT 1,
                    checked INTEGER DEFAULT 0,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Schema-migratie: Controleer of de kolommen 'name' en 'added_date' bestaan in inventory
            cursor.execute("PRAGMA table_info(inventory)")
            columns = [column[1] for column in cursor.fetchall()]

            if "name" not in columns:
                cursor.execute("ALTER TABLE inventory ADD COLUMN name TEXT")

            if "added_date" not in columns:
                cursor.execute("ALTER TABLE inventory ADD COLUMN added_date TIMESTAMP")
                cursor.execute("UPDATE inventory SET added_date = CURRENT_TIMESTAMP WHERE added_date IS NULL")

            self._conn.commit()

    # ── Lokale Producten (Offline Cache) ──────────────────────────────────────

    def get_local_product_name(self, barcode):
        """Zoekt een productnaam in de lokale offline dataset."""
        try:
            with self._lock:
                cursor = self._conn.execute("SELECT name FROM local_products WHERE barcode = ?", (barcode,))
                row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Databasefout bij ophalen lokale productnaam: {e}")
            return None

    def add_to_local_products(self, barcode, name):
        """Slaat een handmatig ingevoerde of gecorrigeerde productnaam lokaal op."""
        query = "INSERT OR REPLACE INTO local_products (barcode, name) VALUES (?, ?)"
        try:
            with self._lock:
                self._conn.execute(query, (barcode, name))
                self._conn.commit()
            print(f"DEBUG: {name} toegevoegd aan lokaal geheugen.")
        except sqlite3.Error as e:
            print(f"Fout bij opslaan in local_products: {e}")

    # ── Voorraad (Inventory) ──────────────────────────────────────────────────

    def get_all_items(self):
        """Haalt alle items uit de voorraad op, inclusief datum van toevoegen."""
        with self._lock:
            cursor = self._conn.execute("SELECT barcode, name, count, added_date FROM inventory")
            return cursor.fetchall()

    def update_item(self, barcode, name, count, added_date):
        """Voegt een product toe of werkt het aantal/de naam bij (Upsert)."""
        query = """
            INSERT INTO inventory (barcode, name, count, added_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(barcode) DO UPDATE SET
                name = excluded.name,
                count = excluded.count
        """
        with self._lock:
            self._conn.execute(query, (barcode, name, count, added_date))
            self._conn.commit()

    def delete_item(self, barcode):
        """Verwijdert een product volledig uit de voorraad."""
        with self._lock:
            self._conn.execute("DELETE FROM inventory WHERE barcode = ?", (barcode,))
            self._conn.commit()

    # ── Winkellijst (Shopping List) ──────────────────────────────────────────

    def add_to_shopping_list(self, barcode, name, quantity=1):
        """Voegt een product toe of verhoogt het aantal als het al op de lijst staat."""
        query = """
            INSERT INTO shopping_list (barcode, name, quantity, checked)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(barcode) DO UPDATE SET
                quantity = shopping_list.quantity + excluded.quantity,
                checked = 0
        """
        try:
            with self._lock:
                self._conn.execute(query, (barcode, name, quantity))
                self._conn.commit()
        except sqlite3.Error as e:
            print(f"Fout bij toevoegen aan winkellijst: {e}")

    def get_shopping_list(self):
        """Haalt alle items op de winkellijst op, gesorteerd op afgevinkt en datum."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT barcode, name, quantity, checked, added_date "
                "FROM shopping_list ORDER BY checked ASC, added_date DESC"
            )
            return cursor.fetchall()

    def toggle_shopping_item(self, barcode):
        """Wisselt de afgevinkt-status (checked) van een product."""
        try:
            with self._lock:
                self._conn.execute(
                    "UPDATE shopping_list "
                    "SET checked = CASE WHEN checked = 0 THEN 1 ELSE 0 END "
                    "WHERE barcode = ?",
                    (barcode,),
                )
                self._conn.commit()
        except sqlite3.Error as e:
            print(f"Fout bij afvinken van winkellijst-item: {e}")

    def remove_from_shopping_list(self, barcode):
        """Verwijdert een product van de winkellijst."""
        try:
            with self._lock:
                self._conn.execute("DELETE FROM shopping_list WHERE barcode = ?", (barcode,))
                self._conn.commit()
        except sqlite3.Error as e:
            print(f"Fout bij verwijderen van winkellijst: {e}")

    def clear_shopping_list(self):
        """Leegt de volledige winkellijst."""
        try:
            with self._lock:
                self._conn.execute("DELETE FROM shopping_list")
                self._conn.commit()
        except sqlite3.Error as e:
            print(f"Fout bij legen winkellijst: {e}")

    def is_on_shopping_list(self, barcode):
        """Controleert of een product op de winkellijst staat."""
        with self._lock:
            cursor = self._conn.execute("SELECT 1 FROM shopping_list WHERE barcode = ?", (barcode,))
            return cursor.fetchone() is not None

    def update_shopping_quantity(self, barcode, quantity):
        """Werkt het aantal bij voor een specifiek product op de winkellijst."""
        try:
            if quantity <= 0:
                self.remove_from_shopping_list(barcode)
            else:
                with self._lock:
                    self._conn.execute(
                        "UPDATE shopping_list SET quantity = ? WHERE barcode = ?",
                        (quantity, barcode),
                    )
                    self._conn.commit()
        except sqlite3.Error as e:
            print(f"Fout bij bijwerken winkellijst-aantal: {e}")

    # ── Afsluiten ─────────────────────────────────────────────────────────────

    def __del__(self):
        """Sluit de databaseverbinding netjes wanneer het object wordt vernietigd."""
        if hasattr(self, "_conn"):
            with self._lock:
                self._conn.close()

