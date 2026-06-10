import unittest
from datetime import datetime

from main import naechste_tage, reservierung_ist_belegt


class TestInventarLogik(unittest.TestCase):
    def test_naechste_tage(self):
        start = datetime(2026, 6, 10) #fixer Starttag
        tage = naechste_tage(3, start) #3 Tage holen
        
        self.assertEqual(tage, ["10.06.2026", "11.06.2026", "12.06.2026"])
    
    def test_reservierung_ist_belegt(self):
        reservierungen = [
            {"artikel_id": "2001", "datum": "10.06.2026"} #eine Reservierung
        ]
        
        self.assertTrue(reservierung_ist_belegt(reservierungen, "2001", "10.06.2026"))
        self.assertFalse(reservierung_ist_belegt(reservierungen, "2002", "10.06.2026"))


if __name__ == "__main__":
    unittest.main()
