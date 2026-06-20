# Slim Voedselvoorraadbeheersysteem

Dit project is een gebruiksvriendelijk en modern voorraadbeheersysteem geschreven in Python met een grafische interface gebouwd in **PyQt5**. Het is ontworpen om soepel te functioneren op touchscreens (zoals een Raspberry Pi) en maakt gebruik van de Model-View-Controller (MVC) architectuur.

## Over het project

Dit voedselvoorraadbeheersysteem werd ontwikkeld als eindejaarsproject voor de studierichting Informatica- en Communicatiewetenschappen. De applicatie is gericht op gebruik op touchscreens en Raspberry Pi-systemen en ondersteunt zowel online als offline productbeheer.

## Features

- **Barcode Integratie:** Scan barcodes om producten direct toe te voegen. Het systeem haalt automatisch productinformatie op via de [OpenFoodFacts API](https://world.openfoodfacts.org/).
- **Offline Modus:** Mogelijkheid tot offline werking door een lokale productdataset te importeren.
- **Virtueel Toetsenbord:** Een ingebouwd on-screen toetsenbord (met AZERTY- en numerieke indeling) speciaal ontworpen voor touchscreens, zodat er geen fysiek toetsenbord vereist is.
- **Voorraadlijst:** Bekijk de actuele voorraad, zoek op naam of barcode en sorteer op alfabet (A-Z), aantal (laag/hoog) of toegevoegde datum.
- **Winkellijst:** Beheer een winkellijst met opties voor het aanpassen van aantallen, afvinken van gekochte items en het in één keer leegmaken van de lijst.

---

## Projectstructuur

Het project volgt een strikte scheiding van verantwoordelijkheden middels het **MVC-patroon**:

```text
voorraadbeheersysteem/
│
├── main.py                          # Hoofdingang van de applicatie
├── import_offline_data.py           # Script voor het bootstrappen van offline productdata
├── inventory.db                     # SQLite database (lokaal gegenereerd, niet in git)
│
├── database/
│   └── db_manager.py                # Database Manager voor SQLite & thread-safe queries
│
├── controller/
│   └── inventory_controller.py      # Vertaalt gebruikersacties naar model-operaties
│
├── model/
│   ├── inventory_model.py           # Bevat de business logica en voorraadgegevens
│   ├── product_fetcher.py           # API-fetcher voor OpenFoodFacts
│   ├── exceptions.py                # Applicatie-specifieke foutmeldingen (Exceptions)
│   └── patterns.py                  # Implementatie van het Observer & Subject patroon
│
├── view/
│   └── qt_v4/                       # Qt5 GUI implementatie
│       ├── qt_view.py               # Hoofdscherm en thread management (Workers)
│       ├── pages.py                 # Pagina's (Menu, Toevoegen, Voorraadlijst, Winkellijst)
│       ├── dialogs.py               # Dialoogschermen (Hernoemen, Handmatige invoer)
│       ├── components.py            # Herbruikbare GUI-componenten (Item-kaarten)
│       ├── keyboard.py              # Ingebouwd virtueel touch-toetsenbord
│       └── theme.py                 # Globaal kleurenpalet en QSS (stylesheet)
│
└── z-tests/
    └── test_inventory.py            # Unit-tests voor het model en persistentie
```

---

## Installatie & Vereisten

Zorg ervoor dat Python 3 geïnstalleerd is. Installeer vervolgens de vereiste bibliotheken met pip:

```bash
pip install PyQt5 requests
```

---

## Applicatie Starten

Start de grafische gebruikersinterface door het uitvoeren van `main.py`:

```bash
python main.py
```

---

## Unit Tests Uitvoeren

De unit-tests controleren de business logica en de database-persistentie via een in-memory database:

```bash
python -m unittest z-tests/test_inventory.py
```

---

## Offline Dataset Bootstrappen (Optioneel)

Om zonder internetverbinding barcodes te kunnen scannen en herkennen, kunt u een lokale database opbouwen:

1. Download de OpenFoodFacts CSV-export (`en.openfoodfacts.org.products.csv`) via hun officiële website: https://nl.openfoodfacts.org/data.
2. Plaats dit bestand in de hoofdmap van het project.
3. Start het import-script om relevante Belgische en Nederlandse producten in te laden in uw lokale SQLite-database:
   ```bash
   python import_offline_data.py
   ```

## Auteur

Lander Berghmans

Eindejaarsproject ontworpen als deel van de studierichting Informatica- en Communicatiewetenschappen aan het Sint-Lambertusinstituut Heist-op-den-Berg.

GitHub: https://github.com/galbeer

## Licentie

MIT License