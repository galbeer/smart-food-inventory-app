# model/patterns.py
"""Implementatie van het Observer-ontwerppatroon."""


class Observer:
    """Interface voor observers die updates van een Subject willen ontvangen."""
    def update(self, data):
        """Wordt aangeroepen wanneer het subject verandert."""
        pass


class Subject:
    """Basisklasse voor subjects die observers kunnen beheren en notificeren."""
    def __init__(self):
        """Initialiseert de lijst met observers."""
        self._observers = []

    def attach(self, observer):
        """Voegt een observer toe aan de lijst."""
        self._observers.append(observer)

    def notify(self, data=None):
        """Stelt alle geregistreerde observers op de hoogte van veranderingen."""
        for observer in self._observers:
            observer.update(data)