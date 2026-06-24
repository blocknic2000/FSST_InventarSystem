#Imports für die verschiedenen Funktionen, die wir brauchen
import customtkinter as ctk #Das ist für die Benutzeroberfläche (Knöpfe, Fenster)
from PIL import Image #Damit können wir Bilder laden und anzeigen
import csv #Um unsere Excel-ähnlichen Daten zu lesen und zu speichern
from datetime import datetime, timedelta #Um mit Datum und Uhrzeit zu rechnen
import os #Um Dinge auf dem Betriebssystem-Level zu machen (wie Display)

#Display für Raspberry Pi einstellen
#Damit das Fenster später auf dem Touchscreen vom Pi richtig angezeigt wird
os.environ["DISPLAY"] = ":0"

#Dark Mode deaktivieren, wir nutzen das helle Design
ctk.set_appearance_mode("light")

#Config - Hier sammeln wir alle wichtigen Grundeinstellungen
class Config:
    CSV_DATEI = "ausleihen.csv" #Name der Datei für die Ausleihen
    RESERVIERUNG_DATEI = "reservierungen.csv" #Name der Datei für Reservierungen
    VERGROESSERUNG = 0.8 #Wie groß alles sein soll (1.0 = normal, 1.2 = größer)
    BILD_GROESSE_KLEIN = int(150 * VERGROESSERUNG) #Größe für die kleinen Bilder in der Übersicht
    BILD_GROESSE_GROSS = int(250 * VERGROESSERUNG) #Größe für das große Bild in der Detailansicht
    BILDSCHIRMSCHONER_ZEIT = 10000 #Wann der Schoner angeht (in Millisekunden, 10000 = 10 Sekunden)
    BILDSCHIRMSCHONER_TEXT = "Tippen!" #Text, der ganz unten im Schoner steht
    KALENDER_TAGE = 14 #Wie viele Tage wir im Voraus reservieren können
    KALENDER_SPALTEN = 4 #Wie viele Spalten das Kalender-Raster hat

#Unsere Artikel-Datenbank
#K=kleine Artikel(Menge wie z.B. 15 Widerstände), G=große Artikel(einzeln, keine Menge, wie 1 Monitor)
#Aufbau: [Typ, ID, Name, Kategorie, Ausgeliehen-Status/Menge]
ARTIKEL = [
    ["G", "2001", "Monitor", "IT", False],
    ["G", "2002", "Drucker", "IT", False],
    ["G", "2003", "Kamera", "Media", False],
    ["G", "2004", "Tastatur", "IT", False],
    ["G", "2005", "Maus", "IT", False],
    ["G", "2006", "Bohrmaschine", "Werkzeug", False],
    ["G", "2007", "Raspberry Pi 4", "IT", False],
    ["G", "2008", "Raspberry Pi 4", "IT", False],
    ["G", "2009", "Arduino", "Elektronik", False],
    ["K", "1001", "Widerstand", "Elektronik", 15],
    ["K", "1002", "Kondensator", "Elektronik", 75],
    ["K", "1003", "Dioden", "Elektronik", 200]
]

#Hauptklasse der App - hier passiert die ganze Magie
class App(ctk.CTk):

    #Initialisierung - wird 1x ganz am Anfang beim Starten aufgerufen
    def __init__(self):
        super().__init__() #Das startet das Grund-Fenster von CustomTkinter
        self.title("Inventarsystem") #Der Name oben in der Fensterleiste
        self.attributes('-fullscreen', True) #Vollbild
        #self.geometry("450x650") #Die Startgröße des Fensters (Breite x Höhe)
        
        #Daten vorbereiten
        #Wir machen eine frische Kopie unserer Artikel-Liste, damit wir sicher arbeiten können
        self.artikel = [a.copy() for a in ARTIKEL] 
        self.ausgeliehene = [] #Hier sammeln wir später alle Artikel, die aktuell weg sind
        self.gefiltert = self.artikel #Das ist die Liste, die gerade angezeigt wird (am Anfang alle)
        
        #Schriftarten zusammengefasst in einer Sammlung (Dictionary)
        #So müssen wir nicht immer ewig langen Code für Schriften schreiben
        self.fonts = {
            "klein": ctk.CTkFont("Arial", int(16 * Config.VERGROESSERUNG)),
            "normal": ctk.CTkFont("Arial", int(24 * Config.VERGROESSERUNG)),
            "gross": ctk.CTkFont("Arial", int(40 * Config.VERGROESSERUNG)),
            "uhr": ctk.CTkFont("Arial", int(80 * Config.VERGROESSERUNG)),
            "log": ctk.CTkFont("Courier New", int(16 * Config.VERGROESSERUNG))
        }
        
        #Status-Variablen für den Bildschirmschoner merken
        self.bildschirmschoner_frame = None #Merkt sich das schwarze Fenster
        self.bildschirmschoner_job = None #Merkt sich den Timer (die tickende Uhr)
        self.bildschirmschoner_aktiv = False #Merkt sich, ob der Schoner gerade zu sehen ist
        self.uhr_label = None #Label für die Uhrzeit im Schoner
        self.back_button = None #Merkt sich den roten X-Button oben rechts
        
        #Events binden (Maus, Tastatur)
        #Egal wohin der Nutzer klickt oder tippt, der Timer vom Schoner fängt wieder bei 0 an
        self.bind_all("<Button>", self.bildschirmschoner_reset) 
        self.bind_all("<Key>", self.bildschirmschoner_reset) 
        self.bind_all("<Motion>", self.bildschirmschoner_reset) 
        
        #Startvorgang
        self.load_ausgeliehene() #Wir lesen erstmal aus der CSV-Datei, was gerade ausgeliehen ist
        self.haupt_fenster() #Danach zeichnen wir das Hauptfenster
        self.bildschirmschoner_starten() #Und ganz am Ende starten wir den Timer für den Schoner

    #---------------- Hilfsfunktionen ----------------

    def datum_umwandeln(self, datum):
        #Macht aus einem normalen Text ("12.05.2023") ein echtes Datum, mit dem der PC rechnen kann
        try:
            return datetime.strptime(datum, "%d.%m.%Y")
        except ValueError:
            return None #Wenn es kein richtiges Datum war, geben wir Nichts (None) zurück

    def naechste_tage(self, anzahl, start=None):
        #Rechnet uns eine Liste der nächsten Tage aus (für unseren Kalender)
        if start is None:
            start = datetime.now() #Wenn kein Starttag angegeben ist, nehmen wir "Heute"
        tage = []
        for i in range(anzahl): #Wir zählen so oft hoch, wie wir Tage wollen
            tag = start + timedelta(days=i) #Tag draufrechnen
            tage.append(tag.strftime("%d.%m.%Y")) #Als schönen Text in die Liste packen
        return tage

    def reservierung_finden(self, reservierungen, artikel_id, datum):
        #Geht alle Reservierungen durch und schaut, ob an dem Tag für den Artikel schon was steht
        for r in reservierungen:
            #Wir vergleichen als Text (str), damit es keine Probleme zwischen Zahlen und Texten gibt
            if r["artikel_id"] == str(artikel_id) and r["datum"] == datum:
                return r #Gefunden! Wir geben die Info zurück
        return None #Nichts gefunden

    def reservierung_ist_belegt(self, reservierungen, artikel_id, datum):
        #Macht fast das gleiche wie drüber, sagt aber nur Wahr (True) oder Falsch (False)
        for r in reservierungen:
            if r["artikel_id"] == str(artikel_id) and r["datum"] == datum:
                return True #Ist schon belegt
        return False #Ist noch frei

    def naechste_reservierung(self, reservierungen, artikel_id, start=None):
        #Sucht uns das Datum raus, an dem der Artikel als nächstes gebraucht wird
        if start is None:
            start = datetime.now()
        start = datetime(start.year, start.month, start.day) #Uhrzeit wegschneiden, nur den Tag vergleichen
        
        beste_reservierung = None
        bestes_datum = None
        
        for r in reservierungen:
            if r["artikel_id"] != str(artikel_id):
                continue #Falscher Artikel, wir springen zum nächsten
            
            datum = self.datum_umwandeln(r["datum"])
            if datum is None:
                continue #Wenn das Datum kaputt ist, überspringen wir es
                
            #Wenn das Datum in der Zukunft liegt und wir noch kein besseres (früheres) gefunden haben
            if datum >= start and (bestes_datum is None or datum < bestes_datum):
                beste_reservierung = r #Das ist unsere vorerst nächste Reservierung
                bestes_datum = datum
                
        return beste_reservierung

    #---------------- Layout Sachen ----------------

    def clear(self):
        #Löscht alles vom Bildschirm, damit wir ein neues Fenster zeichnen können
        for i in self.winfo_children():
            i.destroy() #Zerstört alle Elemente, die gerade da sind
        self.back_button = None #Den X-Button haben wir jetzt auch gelöscht

    def back(self):
        #Zeichnet uns den roten X-Button oben rechts, um zurückzukommen
        self.back_button = ctk.CTkButton(self, text="X", fg_color="red", hover_color="darkred",
                                         font=self.fonts["normal"], width=50, command=self.haupt_fenster)
        #place() heißt, wir kleben ihn exakt an Koordinaten, egal was der Rest vom Fenster macht
        self.back_button.place(relx=1, x=-10, y=10, anchor="ne") 
        self.back_nach_vorne() #Wir rufen ihn ganz nach vorne
        self.after(50, self.back_nach_vorne) #Und zur Sicherheit 50 Millisekunden später nochmal

    def back_nach_vorne(self):
        #Zieht den X-Button über alle anderen Bilder und Texte, damit man ihn immer klicken kann
        try:
            if self.back_button is not None:
                self.back_button.lift()
        except Exception:
            pass #Wenn was schiefgeht, ignorieren wir es einfach

    def grid_zurücksetzen(self):
        #Löscht alle "Wachstums-Regeln" von unserem Fenster-Raster (Grid)
        #So verhindern wir, dass sich alte Fenster-Einstellungen ins neue Fenster reinschmuggeln
        for i in range(10):
            self.grid_rowconfigure(i, weight=0) #weight=0 heißt: NICHT wachsen
            self.grid_columnconfigure(i, weight=0)

    #---------------- Bildschirmschoner ----------------

    def bildschirmschoner_starten(self):
        #Stellt den Timer, wann der Schoner angehen soll
        if self.bildschirmschoner_job is not None:
            try:
                self.after_cancel(self.bildschirmschoner_job) #Alten Timer stoppen, falls noch einer läuft
            except Exception:
                pass
        #Startet einen neuen Timer. Wenn die Zeit abgelaufen ist, rufen wir bildschirmschoner_anzeigen auf
        self.bildschirmschoner_job = self.after(Config.BILDSCHIRMSCHONER_ZEIT, self.bildschirmschoner_anzeigen)

    def bildschirmschoner_reset(self, event=None):
        #Jedes Mal wenn jemand tippt oder die Maus bewegt:
        if self.bildschirmschoner_aktiv:
            self.bildschirmschoner_aus() #Schoner wegmachen, falls er an war
        self.bildschirmschoner_starten() #Timer wieder frisch auf 0 setzen

    def bildschirmschoner_anzeigen(self):
        #Malt uns ein großes schwarzes Fenster über alles drüber
        if self.bildschirmschoner_aktiv:
            return #Wenn er schon an ist, müssen wir nichts tun
        
        self.bildschirmschoner_job = None
        self.bildschirmschoner_aktiv = True
        
        #Komplett schwarzer Frame über das ganze Fenster
        self.bildschirmschoner_frame = ctk.CTkFrame(self, fg_color="black")
        self.bildschirmschoner_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        #Uhrzeit anzeigen
        uhr = datetime.now().strftime("%H:%M")
        self.uhr_label = ctk.CTkLabel(self.bildschirmschoner_frame, text=uhr, font=self.fonts["uhr"], text_color="white")
        self.uhr_label.pack(expand=True) #expand=True drückt es schön in die Mitte
        
        #Text drunter anzeigen
        text = ctk.CTkLabel(self.bildschirmschoner_frame, text=Config.BILDSCHIRMSCHONER_TEXT, font=self.fonts["normal"], text_color="white")
        text.pack(pady=40) #pady macht etwas Abstand nach oben/unten
        
        self.bildschirmschoner_frame.lift() #Schoner nach ganz vorne holen
        self.uhr_aktualisieren() #Live-Update der Uhr starten!

    def uhr_aktualisieren(self):
        #Aktualisiert die Uhrzeit, solange der Schoner an ist
        if self.bildschirmschoner_aktiv and self.uhr_label is not None:
            jetzt = datetime.now().strftime("%H:%M") #Aktuelle Zeit holen
            self.uhr_label.configure(text=jetzt) #Den Text im Label anpassen
            self.after(1000, self.uhr_aktualisieren) #Nach 1 Sekunde rufen wir uns selbst wieder auf! (Schleife)

    def bildschirmschoner_aus(self):
        #Macht den Schoner wieder weg
        if self.bildschirmschoner_frame is not None:
            self.bildschirmschoner_frame.destroy() #Frame komplett löschen
        self.bildschirmschoner_frame = None
        self.uhr_label = None
        self.bildschirmschoner_aktiv = False #Status wieder auf Aus setzen

    #---------------- CSV und Daten laden ----------------

    def load_ausgeliehene(self):
        #Unsere Haupt-Funktion, um alles frisch aus der Datei zu laden
        self.artikel_status_zuruecksetzen() #Erstmal alle auf "Verfügbar" setzen
        self.k_artikel_aktualisieren() #Dann schauen, wie viele Kleinteile weg sind
        self.g_artikel_aktualisieren() #Und dann schauen, welche Großgeräte weg sind

    def artikel_status_zuruecksetzen(self):
        #Setzt alle Artikel so zurück, wie sie ganz am Anfang in der "ARTIKEL" Liste stehen
        for a in self.artikel:
            if a[0] == "K":
                original = next((art for art in ARTIKEL if art[1] == a[1]), None)
                if original:
                    a[4] = original[4] #Originale Menge (z.B. 200) eintragen
            elif a[0] == "G":
                a[4] = False #Auf False (nicht ausgeliehen) setzen

    def k_artikel_aktualisieren(self):
        #Liest alle Ausleihen und Rückgaben für kleine Artikel (Schrauben, Widerstände)
        if not os.path.isfile(Config.CSV_DATEI):
            return #Keine Datei da, also müssen wir nichts machen
            
        try:
            k_artikel_netto = {} #Hier zählen wir, was aktuell FEHLT
            with open(Config.CSV_DATEI, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader, None) #Die erste Zeile in der Datei ist nur Text (Datum, Name...), die überspringen wir
                
                for row in reader:
                    if len(row) < 7:
                        continue #Wenn die Zeile unvollständig ist, gehen wir zur nächsten
                        
                    artikel_id = row[3].strip()
                    typ = row[5].strip()
                    menge = row[6].strip()
                    
                    try:
                        menge_int = int(menge) #Versuch, aus dem Text eine Zahl zu machen
                    except ValueError:
                        menge_int = 1 #Notfall-Zahl
                        
                    if artikel_id not in k_artikel_netto:
                        k_artikel_netto[artikel_id] = 0
                        
                    if typ == "Ausleihe":
                        k_artikel_netto[artikel_id] -= menge_int #Ausleihe zieht etwas ab
                    elif typ == "Rückgabe":
                        k_artikel_netto[artikel_id] += menge_int #Rückgabe packt es wieder drauf
                        
            #Jetzt haben wir die Info und schreiben sie in unsere App-Liste
            for a in self.artikel:
                if a[0] == "K" and a[1] in k_artikel_netto:
                    original = next((art for art in ARTIKEL if art[1] == a[1]), None)
                    if original:
                        #Original Menge (z.B. 200) + die errechnete Differenz (z.B. -15) = 185
                        a[4] = original[4] + k_artikel_netto[a[1]]
                        
        except Exception as e:
            print(f"Fehler bei kleinen Artikeln: {e}")

    def g_artikel_aktualisieren(self):
        #Großgeräte anpassen (Monitor, Kamera etc.)
        aktuelle_ausleihen = self.get_ausgeliehene_from_csv() #Holt sich alle offenen Ausleihen
        self.ausgeliehene = [] #Wir machen die Liste der offnen Ausleihen frisch
        
        #Für jeden Artikel, der laut unserer Logik gerade fehlt:
        for (artikel_id, name, klasse, artikel_name), info in aktuelle_ausleihen.items():
            ausgeliehen_artikel = {
                "id": artikel_id,
                "name": artikel_name,
                "person": info["person"],
                "klasse": info["klasse"],
                "menge": info["menge"],
                "datum": info["datum"]
            }
            self.ausgeliehene.append(ausgeliehen_artikel) #Merken wir uns in der Liste
            
            #Bei den Großgeräten in unserer Haupt-Liste ändern wir jetzt den Status auf True (ausgeliehen)
            for a in self.artikel:
                if a[0] == "G" and a[1] == artikel_id:
                    a[4] = True

    def get_ausgeliehene_from_csv(self):
        #Das hier ist die komplizierteste Funktion. Sie liest das Logbuch und kombiniert
        #Ausleihen und Rückgaben, damit wir genau wissen: Wer hat noch was zu Hause?
        ausgeliehene_dict = {}
        if not os.path.isfile(Config.CSV_DATEI):
            return ausgeliehene_dict
            
        try:
            offene_ausleihen = [] #Hier sammeln wir alle Ausleihen, die noch nicht zurück sind
            
            with open(Config.CSV_DATEI, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader, None) #Header überspringen
                
                for row in reader:
                    if len(row) < 7:
                        continue
                        
                    zeit, name, klasse, artikel_id, artikel_name, typ, menge = [x.strip() for x in row[:7]]
                    
                    try:
                        menge_int = int(menge)
                    except ValueError:
                        menge_int = 1
                        
                    if typ == "Ausleihe":
                        #Jemand leiht etwas aus -> ab in die "noch nicht zurückgegeben" Liste
                        offene_ausleihen.append({
                            "id": artikel_id,
                            "name": artikel_name,
                            "person": name,
                            "klasse": klasse,
                            "menge": menge_int,
                            "datum": zeit
                        })
                    elif typ == "Rückgabe":
                        rest = menge_int #So viel wird gerade zurückgebracht
                        #Wir suchen jemanden in unserer Liste, der genau diesen Artikel hat (mit gleichem Namen)
                        passende = [e for e in offene_ausleihen if e["id"] == artikel_id and e["name"] == artikel_name and e["person"] == name and e["klasse"] == klasse and e["menge"] > 0]
                        
                        if not passende:
                            #Wenn wir niemanden mit dem Namen finden, suchen wir nur nach dem Artikel
                            #(Vielleicht bringt jemand anders das Teil zurück)
                            passende = [e for e in offene_ausleihen if e["id"] == artikel_id and e["name"] == artikel_name and e["menge"] > 0]
                            
                        #Jetzt arbeiten wir die Rückgaben ab und ziehen sie ab
                        for e in passende:
                            if rest <= 0:
                                break #Schon alles abgerechnet
                            weg = min(e["menge"], rest) #Wie viel können wir hier maximal abziehen?
                            e["menge"] -= weg #Von der offenen Ausleihe abziehen
                            rest -= weg #Rest von dem was zurückkam verringern
                            
            #Alle abgerechneten offenen Ausleihen zusammenfassen
            for e in offene_ausleihen:
                if e["menge"] <= 0:
                    continue #Die sind ja komplett zurückgegeben worden, also überspringen
                    
                key = (e["id"], e["person"], e["klasse"], e["name"])
                if key not in ausgeliehene_dict:
                    #Neue Person/Artikel-Kombi eintragen
                    ausgeliehene_dict[key] = {"person": e["person"], "klasse": e["klasse"], "menge": "0", "datum": e["datum"]}
                    
                neue_menge = int(ausgeliehene_dict[key]["menge"]) + e["menge"] #Menge hochzählen
                ausgeliehene_dict[key]["menge"] = str(neue_menge)
                ausgeliehene_dict[key]["datum"] = e["datum"] #Datum updaten
                
            return ausgeliehene_dict #Zurückgeben
            
        except Exception as e:
            print(f"Fehler beim Lesen der CSV: {e}")
            return ausgeliehene_dict

    def daten_speichern(self, name, klasse, artikel_id, artikel_name, typ, anzahl):
        #Speichert einen neuen Log-Eintrag in der Excel(CSV)-Datei
        typ_text = "Ausleihe" if typ == "out" else "Rückgabe" #Übersetzung für die Datei
        zeit = datetime.now().strftime("%d.%m.%Y %H:%M:%S") #Aktuelle Zeit stempeln
        
        #Das hier ist die Liste, wie sie als Zeile in die Datei geschrieben wird
        daten = [zeit, name, klasse, str(artikel_id), str(artikel_name), typ_text, str(anzahl)]
        
        try:
            datei_existiert = os.path.isfile(Config.CSV_DATEI) #Prüfen, ob die Datei überhaupt schon existiert
            
            #Öffnen mit "a" (append) bedeutet: Wir schreiben es ans ENDE der Datei dazu
            with open(Config.CSV_DATEI, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                if not datei_existiert:
                    #Wenn die Datei neu ist, müssen wir erst die Überschriften reinschreiben
                    writer.writerow(["Datum/Zeit", "Name", "Klasse", "Artikel ID", "Artikel Name", "Typ", "Menge"])
                writer.writerow(daten) #Unsere Zeile reinschreiben
            return True #Alles super!
            
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")
            return False

    #---------------- Reservierungen ----------------

    def reservierungen_laden(self):
        #Liest uns alle geplanten Reservierungen aus der Datei
        reservierungen = []
        if not os.path.isfile(Config.RESERVIERUNG_DATEI):
            return reservierungen #Datei gibts nicht, also leere Liste zurückgeben
            
        try:
            with open(Config.RESERVIERUNG_DATEI, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader, None) #Überschriften-Zeile überspringen
                
                for row in reader:
                    if len(row) < 6:
                        continue #Defekte Zeile
                    datum, name, klasse, artikel_id, artikel_name, zeit = [x.strip() for x in row[:6]]
                    reservierungen.append({
                        "datum": datum,
                        "name": name,
                        "klasse": klasse,
                        "artikel_id": artikel_id,
                        "artikel_name": artikel_name,
                        "zeit": zeit
                    }) #Als Paket in die Liste legen
            return reservierungen
            
        except Exception as e:
            print(f"Fehler beim Laden der Reservierungen: {e}")
            return reservierungen

    def reservierung_speichern(self, name, klasse, artikel_id, artikel_name, datum):
        #Versucht einen Tag für einen Artikel zu reservieren
        reservierungen = self.reservierungen_laden()
        if self.reservierung_ist_belegt(reservierungen, artikel_id, datum):
            return False #Pech gehabt, ist schon weg!
            
        zeit = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        daten = [datum, name, klasse, str(artikel_id), str(artikel_name), zeit]
        
        try:
            datei_existiert = os.path.isfile(Config.RESERVIERUNG_DATEI)
            with open(Config.RESERVIERUNG_DATEI, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                if not datei_existiert:
                    writer.writerow(["Datum", "Name", "Klasse", "Artikel ID", "Artikel Name", "Reserviert am"])
                writer.writerow(daten)
            return True #Hat geklappt!
            
        except Exception as e:
            print(f"Fehler beim Speichern der Reservierung: {e}")
            return False

    def reservierung_hinweis_anzeigen(self, a):
        #Zeigt ganz oben in der Artikel-Ansicht, wann er wieder da sein muss
        reservierungen = self.reservierungen_laden()
        reservierung = self.naechste_reservierung(reservierungen, a[1]) #Wann ist die nächste?
        
        if reservierung is None:
            text = "Keine Reservierung"
        else:
            text = "Spätestens zurück:\n" + reservierung["datum"]
            
        hinweis = ctk.CTkLabel(self, text=text, font=self.fonts["normal"], fg_color="lightgray", text_color="black", corner_radius=6)
        #Mit sticky="w" (Westen/Links) klebt es links und zieht sich nicht über die ganze Breite
        hinweis.grid(row=0, column=0, sticky="w", padx=20, pady=10)

    def reservierung_uebersicht(self, a):
        #Öffnet unseren 14-Tage-Kalender, um was zu buchen
        self.clear() #Fenster freimachen
        self.back() #Rotes Kreuz oben
        self.grid_zurücksetzen()
        self.grid_columnconfigure(0, weight=1) #Spalte soll wachsen
        
        #Großer Text ganz oben
        titel = ctk.CTkLabel(self, text="Reservierung\n" + a[2], font=self.fonts["gross"])
        titel.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        #Ein Bereich, in dem wir nach unten scrollen können
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        #Wir bereiten die Spalten für unseren Kalender vor (z.B. 4 Stück)
        spalten = max(1, Config.KALENDER_SPALTEN)
        for spalte in range(spalten):
            scroll.grid_columnconfigure(spalte, weight=1)
        self.grid_rowconfigure(1, weight=1) #Zeile mit dem Kalender darf wachsen
        
        reservierungen = self.reservierungen_laden() #Alle Reservierungen holen
        tage = self.naechste_tage(Config.KALENDER_TAGE) #Die Daten der nächsten 14 Tage rechnen
        
        #Jetzt bauen wir für jeden Tag einen eigenen Knopf
        for i, datum in enumerate(tage):
            reservierung = self.reservierung_finden(reservierungen, a[1], datum)
            
            row = i // spalten #In welche Zeile kommt der Knopf?
            column = i % spalten #In welche Spalte kommt der Knopf?
            
            if reservierung is None:
                #Ist frei! Wir machen einen klickbaren Knopf draus
                text = datum + "\nfrei"
                btn = ctk.CTkButton(scroll, text=text, font=self.fonts["normal"], height=100, command=lambda d=datum: self.reservierung_name_eingabe(a, d))
            else:
                #Schon belegt. Wir machen einen grauen, nicht klickbaren Knopf
                text = datum + "\nbelegt:\n" + reservierung["name"] + " (" + reservierung["klasse"] + ")"
                btn = ctk.CTkButton(scroll, text=text, font=self.fonts["normal"], height=100)
                btn.configure(state="disabled", fg_color="lightgray")
            
            btn.grid(row=row, column=column, sticky="nsew", padx=5, pady=5) #Knopf auf den Bildschirm kleben
        
        self.back_nach_vorne() #Wichtig, damit das rote Kreuz drüber liegt!

    def reservierung_name_eingabe(self, a, datum):
        #Das Fenster, wo man seinen Namen und Klasse für die Reservierung einträgt
        self.clear()
        self.back()
        self.grid_zurücksetzen()
        self.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(self, text="Reservieren am\n" + datum, font=self.fonts["gross"])
        label.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        #Ein Kasten (Frame) in der Mitte, der die Eingabefelder hält
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        
        name_label = ctk.CTkLabel(frame, text="Name:", font=self.fonts["normal"])
        name_label.grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ctk.CTkEntry(frame, font=self.fonts["normal"]) #Hier kann der User tippen
        name_entry.grid(row=1, column=0, sticky="ew", pady=5)
        
        klasse_label = ctk.CTkLabel(frame, text="Klasse:", font=self.fonts["normal"])
        klasse_label.grid(row=2, column=0, sticky="w", pady=5)
        klasse_entry = ctk.CTkEntry(frame, font=self.fonts["normal"]) #Hier auch
        klasse_entry.grid(row=3, column=0, sticky="ew", pady=5)
        
        #Die Funktion, wenn man auf OK klickt
        def ok():
            name = name_entry.get().strip() #Leerzeichen wegschneiden
            klasse = klasse_entry.get().strip()
            if not name or not klasse:
                return #Wenn er was vergessen hat einzutippen, passiert einfach gar nichts
                
            erfolgreich = self.reservierung_speichern(name, klasse, a[1], a[2], datum)
            if erfolgreich:
                #Hat geklappt!
                self.zeige_meldung("Reserviert!", "green", 2000, lambda: self.reservierung_uebersicht(a))
            else:
                #War jemand schneller...
                self.zeige_meldung("Schon belegt!", "red", 2000, lambda: self.reservierung_uebersicht(a))
        
        self.grid_rowconfigure(2, weight=1) #Ein Platzhalter-Abstand
        ok_btn = ctk.CTkButton(self, text="Reservieren", font=self.fonts["normal"], command=ok)
        ok_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

    #---------------- Hauptfenster und Menüs ----------------

    def haupt_fenster(self, alle_anzeigen=True):
        #Das ist das Startbild, das man als allererstes sieht
        self.clear()
        self.load_ausgeliehene() #Wir lesen schnell, was aktuell ausgeliehen ist
        
        if alle_anzeigen:
            self.gefiltert = self.artikel #Alles anzeigen
            
        self.grid_zurücksetzen()
        self.grid_columnconfigure(0, weight=1)

        #Der Suchen-Knopf ganz oben
        suche = ctk.CTkButton(self, text="Suchen", font=self.fonts["normal"], command=lambda: self.numpad(self.filter_id))
        suche.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        #Das Drop-Down-Menü für die Kategorien (IT, Media...)
        #set() sorgt dafür, dass jede Kategorie nur einmal in der Liste steht
        kategorien = ["Alle", "Ausgeliehene", "CSV / LOG"] + sorted(set(a[3] for a in self.artikel))
        self.kategorie = ctk.CTkOptionMenu(self, values=kategorien, font=self.fonts["normal"], dropdown_font=self.fonts["normal"], command=self.filter_kat)
        self.kategorie.set("Alle") #Am Anfang immer auf "Alle" stellen
        self.kategorie.grid(row=1, column=0, sticky="ew", padx=20)
        
        #Die große Box, in der wir scrollen können (für die vielen Artikelbilder)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.grid_rowconfigure(2, weight=1) #Die Scroll-Box soll mit dem Fenster mitwachsen
        self.render_artikel() #Jetzt malen wir alle Artikel in die Box rein

        #Der Barcode-Knopf ganz unten
        barcode = ctk.CTkButton(self, text="Barcode", font=self.fonts["normal"], command=self.barcode)
        barcode.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

    def render_artikel(self):
        #Malt alle Artikelbilder aus der Liste 'self.gefiltert' auf den Bildschirm
        for w in self.scroll.winfo_children():
            w.destroy() #Alte Bilder löschen

        for i, a in enumerate(self.gefiltert):
            frame = ctk.CTkFrame(self.scroll) #Ein kleiner Rahmen für 1 Artikel
            #i // 2 und i % 2 bedeutet: Wir machen exakt 2 Spalten! (z.B. links, rechts, nächste Zeile links...)
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="nsew")
            self.scroll.grid_columnconfigure(i % 2, weight=1)

            #Muss ein roter Schatten übers Bild? (Weil ausgeliehen / leer)
            ist_ausgeliehen = self.kategorie.get() == "Alle" and ((a[0] == "G" and a[4] == True) or (a[0] == "K" and a[4] == 0))
            img = self.load_img(a[2], ausgeliehen=ist_ausgeliehen) #Bild aus dem Ordner laden
            
            bild = ctk.CTkLabel(frame, image=img, text="")
            bild.image = img #Sehr wichtig, sonst wirft Python das Bild unbemerkt in den Müll (Garbage Collection)
            bild.pack() #Ab in den Rahmen damit

            #Namen und ID drunterschreiben
            name_label = ctk.CTkLabel(frame, text=a[2], font=self.fonts["normal"])
            name_label.pack()

            typ_label = ctk.CTkLabel(frame, text=f"ID: {a[1]}", font=self.fonts["normal"])
            typ_label.pack()
            
            #Bei schon ausgeliehenen Artikeln (Kategorie "Ausgeliehene") schreiben wir den Namen der Person drunter
            if a[0] == "A":
                person_label = ctk.CTkLabel(frame, text=f"Von: {a[4]['person']}", font=self.fonts["normal"])
                person_label.pack()

            #Klickbar machen - wenn man das Bild berührt, öffnet sich das Detailfenster für diesen Artikel
            bild.bind("<Button-1>", lambda e, x=a: self.detail(x))

    def detail(self, a):
        #Zeigt uns EIN bestimmtes Gerät im Vollbild (mit Knöpfen für Ausleihen etc.)
        self.clear()
        self.back()
        self.grid_columnconfigure(0, weight=1) #Mitte vom Bildschirm
        
        #----- ZEILE 0: Hinweis Reservierung -----
        self.reservierung_hinweis_anzeigen(a) #Klebt den Hinweis jetzt sicher in Zeile 0!

        #----- ZEILE 1: Großes Bild -----
        img = self.load_img(a[2], big=True) #"big=True" holt das Bild in groß
        bild = ctk.CTkLabel(self, image=img, text="")
        bild.image = img
        bild.grid(row=1, column=0, pady=10) #Bild in Zeile 1

        #----- ZEILE 2: Texte (Infos) -----
        info = ctk.CTkFrame(self)
        info.grid(row=2, column=0, sticky="ew", padx=20)
        info.grid_columnconfigure(0, weight=1)
        
        artikelname = ctk.CTkLabel(info, text=a[2], font=self.fonts["normal"])
        artikelname.grid(row=0, column=0, sticky="ew", pady=10)
        
        info_row = 1
        
        #Kategorie (nur anzeigen, wenn es nicht gerade das "Ausgeliehene"-Menü ist)
        if a[0] != "A":
            kategorie = ctk.CTkLabel(info, text="Kategorie: " + a[3], font=self.fonts["normal"])
            kategorie.grid(row=info_row, column=0, sticky="ew", pady=10)
            info_row += 1
        
        id_label = ctk.CTkLabel(info, text="ID: " + a[1], font=self.fonts["normal"])
        id_label.grid(row=info_row, column=0, sticky="ew", pady=10)
        info_row += 1
        
        #Bei Dingen, die schon weg sind, zeigen wir Name und Klasse an
        if a[0] == "A":
            ausgeliehen_info = a[4]
            status = ctk.CTkLabel(info, text="Status: Ausgeliehen", font=self.fonts["normal"])
            status.grid(row=info_row, column=0, sticky="ew", pady=10)
            info_row += 1
            menge = ctk.CTkLabel(info, text=f"Anzahl: {ausgeliehen_info['menge']}", font=self.fonts["normal"])
            menge.grid(row=info_row, column=0, sticky="ew", pady=10)
            info_row += 1
            person = ctk.CTkLabel(info, text=f"Von: {ausgeliehen_info['person']} ({ausgeliehen_info['klasse']})", font=self.fonts["normal"])
            person.grid(row=info_row, column=0, sticky="ew", pady=10)
            info_row += 1
            datum = ctk.CTkLabel(info, text=f"Datum: {ausgeliehen_info['datum']}", font=self.fonts["normal"])
            datum.grid(row=info_row, column=0, sticky="ew", pady=10)
        else:
            #Bei normalen Großgeräten zeigen wir Verfügbar/Ausgeliehen
            if a[0] == "G":
                status_text = "Status: Ausgeliehen" if a[4] else "Status: Verfügbar"
                status = ctk.CTkLabel(info, text=status_text, font=self.fonts["normal"])
                status.grid(row=info_row, column=0, sticky="ew", pady=10)
                info_row += 1
            #Bei Kleinteilen zeigen wir, wie viele noch auf Lager sind
            if a[0] == "K":
                menge_wert = a[4] if a[4] is not None else 0
                menge = ctk.CTkLabel(info, text=f"Menge: {menge_wert}", font=self.fonts["normal"])
                menge.grid(row=info_row, column=0, sticky="ew", pady=10)

        #----- ZEILE 3: PLATZHALTER -----
        #Das ist der Trick, damit die Buttons ganz nach unten rutschen!
        #Wir lassen Zeile 3 einfach leer und sagen ihr "Wachse so groß du kannst" (weight=1).
        #Dadurch schiebt sie alles, was danach kommt (unsere Knöpfe), ganz nach unten an den Rand!
        self.grid_rowconfigure(3, weight=1) 

        #----- ZEILE 4: Buttons -----
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10) #Klebt jetzt ganz unten!
        
        #Jede Spalte einzeln konfigurieren, damit die Buttons garantiert wachsen
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        #Jetzt schauen wir, welche Art von Knöpfen wir zeichnen müssen
        if a[0] == "A":
            #Es ist schon ausgeliehen -> Man kann es nur zurückgeben
            rückgabe = ctk.CTkButton(btn_frame, text="Rückgabe bestätigen", font=self.fonts["normal"], command=lambda: self.name_eingabe(a, "in", int(a[4]["menge"])))
            rückgabe.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
            
        elif a[0] == "G":
            #Ein Großgerät -> Ausleihen, Rückgabe oder Reservieren
            ausleihen = ctk.CTkButton(btn_frame, text="Ausleihen", font=self.fonts["normal"], command=lambda: self.name_eingabe(a, "out", 1))
            if a[4]: #Wenn schon weg, Knopf grau machen
                ausleihen.configure(state="disabled", fg_color="lightgray")
            ausleihen.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            
            rückgabe = ctk.CTkButton(btn_frame, text="Rückgabe", font=self.fonts["normal"], command=lambda: self.name_eingabe(a, "in", 1))
            if not a[4]: #Wenn es noch da ist, kann man es nicht zurückgeben -> Knopf grau
                rückgabe.configure(state="disabled", fg_color="lightgray")
            rückgabe.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            reservieren = ctk.CTkButton(btn_frame, text="Reservieren", font=self.fonts["normal"], command=lambda: self.reservierung_uebersicht(a))
            reservieren.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
            
        else:
            #Ein kleines Teil (z.B. Widerstände)
            ausleihen = ctk.CTkButton(btn_frame, text="Ausleihen", font=self.fonts["normal"], command=lambda: self.menge(a, "out"))
            if a[4] is None or a[4] == 0: #Leer -> Knopf grau
                ausleihen.configure(state="disabled", fg_color="lightgray")
            ausleihen.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            
            rückgabe = ctk.CTkButton(btn_frame, text="Rückgabe", font=self.fonts["normal"], command=lambda: self.menge(a, "in"))
            rückgabe.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            reservieren = ctk.CTkButton(btn_frame, text="Reservieren", font=self.fonts["normal"], command=lambda: self.reservierung_uebersicht(a))
            reservieren.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

    #---------------- Suchen und Filtern ----------------

    def filter_kat(self, k):
        #Das Dropdown Menü ändert unsere Liste
        if k == "Alle":
            self.gefiltert = self.artikel #Alles zeigen
        elif k == "Ausgeliehene":
            self.gefiltert = []
            ausgeliehene_dict = self.get_ausgeliehene_from_csv() #Log auslesen
            
            for (artikel_id, name, klasse, artikel_name), info in ausgeliehene_dict.items():
                self.gefiltert.append(["A", artikel_id, artikel_name, "Ausgeliehene", info])
        elif k == "CSV / LOG":
            self.csv_anzeigen() #Das zeigt den Code Text an
            return
        else:
            self.gefiltert = [a for a in self.artikel if a[3] == k] #Nur Sachen in der gesuchten Kategorie
            
        self.render_artikel() #Bilder neu malen

    def filter_id(self, text):
        #Wenn man eine ID in den Such-Block eintippt
        if text == "":
            self.gefiltert = self.artikel
        else:
            #Sucht in normalen Artikeln
            self.gefiltert = [a for a in self.artikel if a[1] == text]
            
            #Sucht auch in Leuten, die Sachen schon zu Hause haben
            ausgeliehene_dict = self.get_ausgeliehene_from_csv()
            for (artikel_id, name, klasse, artikel_name), info in ausgeliehene_dict.items():
                if artikel_id == text:
                    self.gefiltert.append(["A", artikel_id, artikel_name, "Ausgeliehene", info])
                    
        self.haupt_fenster(False) #Ansicht refreshen (False = Liste nicht überschreiben)

    #---------------- Zahleneingabe und Ausleihe ----------------

    def numpad(self, callback):
        #Ein riesiger Nummernblock auf dem Bildschirm (Touch-freundlich)
        self.clear()
        
        #3 Spalten die gleich breit sind
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.back()

        entry = ctk.CTkEntry(self, font=self.fonts["gross"])
        entry.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=20)

        def add(x):
            entry.insert("end", x) #Ziffer ins Textfeld schreiben

        def delete():
            text = entry.get()
            if text:
                entry.delete(len(text) - 1) #Letztes Zeichen löschen

        def ok():
            callback(entry.get()) #Wirft den Text in die Suche oder Menge zurück

        #Eine Schleife, die uns 9 Knöpfe (1-9) malt, ohne dass wir 9x den Code schreiben müssen
        nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        row = 1
        
        for i in range(0, 9, 3):
            for j in range(3):
                btn = ctk.CTkButton(self, text=nums[i + j], font=self.fonts["normal"], height=80, command=lambda x=nums[i + j]: add(x))
                btn.grid(row=row, column=j, sticky="nsew", padx=5, pady=5)
            row += 1

        #Die unterste Reihe machen wir händisch
        ctk.CTkButton(self, text="DEL", font=self.fonts["normal"], height=80, command=delete).grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkButton(self, text="0", font=self.fonts["normal"], height=80, command=lambda: add("0")).grid(row=row, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkButton(self, text="OK", font=self.fonts["normal"], height=80, command=ok).grid(row=row, column=2, sticky="nsew", padx=5, pady=5)

        for i in range(row + 1):
            self.grid_rowconfigure(i, weight=1) #Alle Zeilen sollen schön den ganzen Platz ausfüllen

    def menge(self, a, typ):
        #Fenster mit Plus/Minus, um z.B. "3 Stück" statt "1 Stück" auszuwählen
        self.clear()
        self.back()
        self.grid_zurücksetzen()
        self.grid_columnconfigure(0, weight=1)

        menge = 0 #Wir starten bei Null
        max_menge = a[4] if typ == "out" else None #Beim Ausleihen("out") dürfen wir nicht mehr als da sind
        
        #Text oben
        label_text = f"Anzahl: 0 / {max_menge}" if typ == "out" else "Anzahl: 0"
        label = ctk.CTkLabel(self, text=label_text, font=self.fonts["gross"])
        label.grid(row=0, column=0, pady=40)

        def plus():
            nonlocal menge #Sagt Python: "Hol dir die Menge-Zahl von etwas weiter oben"
            if typ == "out" and menge < max_menge:
                menge += 1 #Nicht über Maximum gehen
            elif typ == "in":
                menge += 1 #Beim Zurückbringen gibts kein Limit
            label.configure(text=f"Anzahl: {menge} / {max_menge}" if typ == "out" else f"Anzahl: {menge}") #Text anpassen

        def minus():
            nonlocal menge
            if menge > 0:
                menge -= 1 #Niemals unter 0 gehen
            label.configure(text=f"Anzahl: {menge} / {max_menge}" if typ == "out" else f"Anzahl: {menge}") #Text anpassen

        def ok():
            if menge == 0:
                return #Wer nichts leiht, kriegt nichts
            self.name_eingabe(a, typ, menge) #Weiter zum Namen eintragen!

        self.grid_rowconfigure(1, weight=1) #Platzhalter-Abstand in der Mitte

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        #Knöpfe wieder über Spalten sicher wachsen lassen
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        #Die riesigen Plus und Minus Knöpfe
        ctk.CTkButton(btn_frame, text="-", font=self.fonts["normal"], height=100, command=minus).grid(row=0, column=0, sticky="ew", padx=5)
        ctk.CTkButton(btn_frame, text="+", font=self.fonts["normal"], height=100, command=plus).grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkButton(btn_frame, text="Bestätigen", font=self.fonts["normal"], command=ok).grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

    def name_eingabe(self, a, typ, anzahl):
        #Das letzte Fenster, wo man Name und Klasse schreibt, bevor es gespeichert wird
        if anzahl == 0:
            self.haupt_fenster()
            return

        self.clear()
        self.back()
        self.grid_zurücksetzen()
        self.grid_columnconfigure(0, weight=1)

        #Wir schieben die Box etwas runter, damit das rote Kreuz oben nicht im Weg ist
        ctk.CTkLabel(self, text="", height=50).grid(row=0, column=0)
        ctk.CTkLabel(self, text="Name & Klasse\neingeben!", font=self.fonts["gross"]).grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Name:", font=self.fonts["normal"]).grid(row=0, column=0, sticky="w", pady=5)
        name_entry = ctk.CTkEntry(frame, font=self.fonts["normal"])
        name_entry.grid(row=1, column=0, sticky="ew", pady=5)
        
        ctk.CTkLabel(frame, text="Klasse:", font=self.fonts["normal"]).grid(row=2, column=0, sticky="w", pady=5)
        klasse_entry = ctk.CTkEntry(frame, font=self.fonts["normal"])
        klasse_entry.grid(row=3, column=0, sticky="ew", pady=5)
        
        def ok():
            name = name_entry.get().strip()
            klasse = klasse_entry.get().strip()
            if not name or not klasse:
                return #Nichts eingegeben = ignorieren
            
            erfolgreich = self.daten_speichern(name, klasse, a[1], a[2], typ, anzahl) #In die Datei schreiben!
            
            if erfolgreich:
                #Wir aktualisieren unsere interne Liste, damit es sofort für den Nutzer richtig aussieht
                if typ == "out":
                    if a[0] == "G":
                        a[4] = True
                    elif a[0] == "K":
                        a[4] -= anzahl
                elif typ == "in":
                    if a[0] == "G":
                        a[4] = False
                    elif a[0] == "K":
                        a[4] += anzahl
                        
                #Zeigt grünes Fenster an und geht danach ins Hauptmenü zurück
                self.zeige_meldung("Gespeichert!", "green", 2000, self.haupt_fenster)

        self.grid_rowconfigure(3, weight=1)
        ctk.CTkButton(self, text="Bestätigen", font=self.fonts["normal"], command=ok).grid(row=4, column=0, sticky="ew", padx=20, pady=10)

    #---------------- Sonstiges (Meldungen & Utilities) ----------------

    def zeige_meldung(self, text, farbe="green", dauer=2000, danach=None):
        #Das ist unsere Hilfsfunktion, die ein grünes (oder rotes) Bild über alles drüberlegt ("Erfolgreich!")
        meldung = ctk.CTkFrame(self, fg_color=farbe)
        meldung.place(relx=0, rely=0, relwidth=1, relheight=1) #Volle Größe über alles drüber
        label = ctk.CTkLabel(meldung, text=text, font=self.fonts["gross"], text_color="white")
        label.pack(expand=True) #Text in die Mitte drücken
        
        def aufraeumen():
            meldung.destroy() #Grünes Fenster löschen
            if danach: #Falls wir danach eine Funktion aufrufen wollen (z.B. zurück ins Menü)
                danach()
                
        self.after(dauer, aufraeumen) #"dauer" (z.B. 2000ms = 2 Sekunden) warten, dann aufräumen

    def csv_anzeigen(self):
        #Zeigt uns den rohen Daten-Text an (Die Kategorie ganz unten im Dropdown)
        for w in self.scroll.winfo_children():
            w.destroy() #Alte Bilder weg
        
        self.scroll.grid_columnconfigure(0, weight=1) #Spalte soll wachsen
        ctk.CTkLabel(self.scroll, text="CSV / LOG", font=self.fonts["gross"]).grid(row=0, column=0, pady=10)
        
        if not os.path.isfile(Config.CSV_DATEI):
            text = "CSV Datei nicht gefunden"
        else:
            try:
                with open(Config.CSV_DATEI, "r", encoding="utf-8") as f:
                    text = f.read() #Einfach stumpf die ganze Datei lesen
            except Exception as e:
                text = f"Fehler: {e}"
        
        if text.strip() == "":
            text = "CSV Datei ist leer"
        
        log = ctk.CTkTextbox(self.scroll, font=self.fonts["log"])
        #sticky="nsew" ist wichtig, damit sich das Textfenster nach allen Seiten wie Gummi dehnt (responsive)
        log.grid(row=1, column=0, sticky="nsew", pady=10) 
        self.scroll.grid_rowconfigure(1, weight=1) #Diese Zeile (die Textbox) soll wachsen
        
        log.insert("1.0", text) #Text reinkleben
        log.configure(state="disabled") #Sperren, damit der Nutzer ihn hier nicht kaputt-tippen kann

    def barcode(self):
        #Platzhalter für die Barcodescanner-Funktion später
        self.clear()
        self.back()
        info = ctk.CTkLabel(self, text="In Bearbeitung", font=self.fonts["gross"])
        info.pack(expand=True)

    def load_img(self, name, big=False, ausgeliehen=False):
        #Lädt Bilder für die App
        #Größe je nachdem ob Übersicht oder Details aufgerufen wurden
        size = (Config.BILD_GROESSE_GROSS, Config.BILD_GROESSE_GROSS) if big else (Config.BILD_GROESSE_KLEIN, Config.BILD_GROESSE_KLEIN)
        
        #Den genauen Pfad zum Ordner auf dem System
        pfad = os.path.join("GUI/Bilder/" + name + ".png")
        pfad_platzhalter = os.path.join("GUI/Bilder/" + "Platzhalter.png")
        
        try:
            img = Image.open(pfad) #Versuch 1: Das richtige Bild aus dem Ordner laden
        except FileNotFoundError:
            try:
                img = Image.open(pfad_platzhalter) #Versuch 2: Das Platzhalter-Bild laden
            except FileNotFoundError:
                #Versuch 3: Es gibt gar keine Bilder, wir malen einfach eine graue Fläche
                img = Image.new("RGBA", size, "gray") 
        
        if ausgeliehen:
            #Wir malen eine halb-durchsichtige (120) rote Folie über das Bild
            overlay = Image.new("RGBA", img.size, (255, 0, 0, 120))
            if img.mode != "RGBA":
                img = img.convert("RGBA") #Muss RGBA sein (wegen durchsichtig)
            img = Image.alpha_composite(img, overlay) #Beides zusammenkleben
        
        return ctk.CTkImage(img, size=size) #Fertig umgewandelt zurückgeben, damit CustomTkinter es versteht

#Wenn wir das Script starten, soll die App aufgerufen werden
app = App()
app.mainloop() #Hält das Fenster offen