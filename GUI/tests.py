#Wir importieren das Modul für Unit-Tests
import unittest

#Damit wir mit Datumsobjekten arbeiten können
from datetime import datetime

#Unsere App-Klasse aus der main.py importieren
from main import App

#Klasse mit allen Tests
class TestInventarsystem(unittest.TestCase):

    #Wird vor jedem einzelnen Test ausgeführt
    def setUp(self):
        #App-Objekt erstellen ohne das GUI-Fenster zu starten
        self.app = App.__new__(App)

    #Test für die Funktion datum_umwandeln()
    def test_datum_umwandeln(self):

        #Datum als Text an die Funktion übergeben
        datum = self.app.datum_umwandeln("24.06.2026")

        #Prüfen ob ein datetime-Objekt zurückkommt
        self.assertIsInstance(datum, datetime)

        #Prüfen ob das Jahr korrekt ist
        self.assertEqual(datum.year, 2026)

        #Prüfen ob der Monat korrekt ist
        self.assertEqual(datum.month, 6)

        #Prüfen ob der Tag korrekt ist
        self.assertEqual(datum.day, 24)

    #Test für die Funktion naechste_tage()
    def test_naechste_tage(self):

        #Die nächsten 3 Tage erzeugen lassen
        tage = self.app.naechste_tage(3)

        #Prüfen ob genau 3 Einträge erzeugt wurden
        self.assertEqual(len(tage), 3)

    #Test für die Funktion reservierung_ist_belegt()
    def test_reservierung_ist_belegt(self):

        #Beispiel-Liste mit einer Reservierung
        reservierungen = [
            {
                "artikel_id": "2001",
                "datum": "25.06.2026"
            }
        ]

        #Prüfen ob die vorhandene Reservierung gefunden wird
        self.assertTrue(
            self.app.reservierung_ist_belegt(
                reservierungen,
                "2001",
                "25.06.2026"
            )
        )

        #Prüfen ob ein freier Tag als nicht belegt erkannt wird
        self.assertFalse(
            self.app.reservierung_ist_belegt(
                reservierungen,
                "2001",
                "26.06.2026"
            )
        )

#Startet die Tests beim Ausführen der Datei
if __name__ == "__main__":

    #Führt alle Tests automatisch aus
    unittest.main()