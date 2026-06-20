# import_offline_data.py
"""Script voor het importeren van OpenFoodFacts offline productgegevens.

Dit script leest een OpenFoodFacts CSV-bestand en importeert barcodes en namen
van producten uit relevante landen (België en Nederland) in de lokale SQLite database.
Dit maakt offline barcodeherkenning mogelijk.
"""

import csv
import sqlite3
import time
import sys

# Verhoog de limiet om de "field larger than field limit" fout te voorkomen
csv.field_size_limit(sys.maxsize)


def bootstrap_offline_db(csv_path, db_path):
    """Importeert productgegevens uit een CSV-bestand naar een SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Optimalisatie: SQLite sneller maken voor bulk-inserts
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")

    # Zorg dat de tabel voor lokale producten bestaat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_products (
            barcode TEXT PRIMARY KEY,
            name TEXT
        )
    """)

    print(f"--- Start import vanuit {csv_path} ---")
    start_time = time.time()
    count = 0
    skipped = 0

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            # OpenFoodFacts gebruikt tabulatoren (\t) als scheidingsteken
            reader = csv.DictReader(f, delimiter='\t')

            for row in reader:
                barcode = row.get('code', '').strip()
                name = row.get('product_name', '').strip()
                countries = row.get('countries_en', '').lower()

                # Filter: Alleen relevante landen om de databasegrootte te beperken
                relevant_countries = ['belgium', 'netherlands', 'luxembourg', 'be', 'nl']
                is_relevant = any(country in countries for country in relevant_countries)

                if barcode and name and is_relevant:
                    try:
                        cursor.execute(
                            "INSERT OR REPLACE INTO local_products (barcode, name) VALUES (?, ?)",
                            (barcode, name)
                        )
                        count += 1
                    except sqlite3.Error:
                        skipped += 1

                # Voortgangsmelding elke 5000 regels
                if (count + skipped) % 5000 == 0:
                    elapsed = time.time() - start_time
                    print(f"Bezig... {count} producten opgeslagen | {elapsed:.1f}s verstreken")

        conn.commit()
        total_time = time.time() - start_time
        print(f"\n--- SUCCES ---")
        print(f"Totaal geïmporteerd: {count} producten")
        print(f"Tijd: {total_time/60:.2f} minuten")
        print("Je kunt nu offline scannen!")

    except Exception as e:
        print(f"\nFOUT tijdens import: {e}")
        print("Controleer of de bestandsnaam exact klopt en het bestand niet open staat in een ander programma.")
    finally:
        conn.close()


if __name__ == "__main__":
    # Pas deze bestandsnaam aan als uw gedownloade CSV-bestand anders heet
    FILENAME = "en.openfoodfacts.org.products.csv"
    bootstrap_offline_db(FILENAME, "inventory.db")