#Imports
import customtkinter as ctk
from PIL import Image
import csv
from datetime import datetime, timedelta
import os
os.environ["DISPLAY"] = ":0"

#Dark Mode aktivieren
ctk.set_appearance_mode("light")

#CSV Dateinamen konstant
CSV_DATEI = "ausleihen.csv"
RESERVIERUNG_DATEI = "reservierungen.csv"

#Vergrößerung für Schrift und Bilder
VERGROESSERUNG = 1.0 #1.0 = normal, 1.2 = größer, 0.8 = kleiner
FONT_SCALE = VERGROESSERUNG #Schrift mit Vergrößerung
BILD_GROESSE_KLEIN = int(150 * VERGROESSERUNG) #kleine Bilder
BILD_GROESSE_GROSS = int(250 * VERGROESSERUNG) #große Bilder

#Bildschirmschoner
BILDSCHIRMSCHONER_ZEIT = 120000 #Zeit in Millisekunden
BILDSCHIRMSCHONER_TEXT = "Inventarsystem\nTippen zum Weiter"

#Kalender
KALENDER_TAGE = 14 #wie viele Tage angezeigt werden
KALENDER_SPALTEN = 4 #wie viele Spalten der Kalender hat

#Artikel: [Typ, ID, Name, Kategorie, Menge(nur bei K), ausgeliehen(nur bei G)]
#K=kleine Artikel(Menge), G=große Artikel(einzeln, keine Menge)
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

#Nächste Tage für Kalender berechnen
def naechste_tage(anzahl, start = None):
    if start is None:
        start = datetime.now() #heutiger Tag
    
    tage = [] #Liste für Tage
    for i in range(anzahl):
        tag = start + timedelta(days = i) #Tag dazu rechnen
        tage.append(tag.strftime("%d.%m.%Y")) #Datum speichern
    
    return tage

#Prüfen ob Artikel an einem Datum reserviert ist
def reservierung_ist_belegt(reservierungen, artikel_id, datum):
    for r in reservierungen:
        if r["artikel_id"] == str(artikel_id) and r["datum"] == datum:
            return True #Reservierung gefunden
    
    return False

#Reservierung für Artikel und Datum finden
def reservierung_finden(reservierungen, artikel_id, datum):
    for r in reservierungen:
        if r["artikel_id"] == str(artikel_id) and r["datum"] == datum:
            return r #Reservierung zurückgeben
    
    return None

#Datum in richtiges Datum umwandeln
def datum_umwandeln(datum):
    try:
        return datetime.strptime(datum, "%d.%m.%Y") #Text zu Datum
    except:
        return None

#Nächste Reservierung suchen
def naechste_reservierung(reservierungen, artikel_id, start = None):
    if start is None:
        start = datetime.now() #heutiger Tag
    
    start = datetime(start.year, start.month, start.day) #nur Datum vergleichen
    beste_reservierung = None #merkt die nächste Reservierung
    bestes_datum = None #merkt das nächste Datum
    
    for r in reservierungen:
        if r["artikel_id"] != str(artikel_id):
            continue #anderer Artikel
        
        datum = datum_umwandeln(r["datum"]) #Datum umwandeln
        
        if datum is None:
            continue #falsches Datum
        
        if datum >= start and (bestes_datum is None or datum < bestes_datum):
            beste_reservierung = r #Reservierung merken
            bestes_datum = datum #Datum merken
    
    return beste_reservierung

#Haupt-Klasse der App
class App(ctk.CTk):
    #Initialisierung
    def __init__(self):
        super().__init__()
        self.title("Inventarsystem") #Fenster-Titel
        self.attributes('-fullscreen', True) #Vollbild
        self.artikel = [a.copy() for a in ARTIKEL] #alle Artikel(Kopie)
        self.ausgeliehene = [] #ausgeliehene Artikel(aus CSV)
        self.gefiltert = self.artikel #aktuelle Filterung
        self.schrift_klein = ctk.CTkFont("Arial", int(16 * FONT_SCALE)) #kleine Schrift
        self.schrift = ctk.CTkFont("Arial", int(24 * FONT_SCALE)) #Standard-Schrift
        self.schrift_groß = ctk.CTkFont("Arial", int(40 * FONT_SCALE)) #große Schrift
        self.schrift_log = ctk.CTkFont("Courier New", int(16 * FONT_SCALE)) #Schrift für CSV Log
        self.bildschirmschoner_frame = None #Frame für Bildschirmschoner
        self.bildschirmschoner_job = None #Timer für Bildschirmschoner
        self.bildschirmschoner_aktiv = False #merkt ob Bildschirmschoner an ist
        self.back_button = None #merkt den Zurück-Button
        self.bind_all("<Button>", self.bildschirmschoner_reset) #Klick setzt Timer zurück
        self.bind_all("<Key>", self.bildschirmschoner_reset) #Taste setzt Timer zurück
        self.bind_all("<Motion>", self.bildschirmschoner_reset) #Maus setzt Timer zurück
        self.load_ausgeliehene() #ausgeliehene Artikel laden
        self.haupt_fenster() #Hauptfenster 
        self.bildschirmschoner_starten() #Timer starten
    
    #Grid-Layout zurücksetzen
    def grid_zurücksetzen(self):
        for i in range(10): #alle Zeilen/Spalten
            self.grid_rowconfigure(i, weight = 0) #weight=0 --> bleibt bei Mindestgröße, wächst NICHT mit Fenster
            self.grid_columnconfigure(i, weight = 0) #weight=0 --> bleibt bei Mindestgröße, wächst NICHT mit Fenster
    
    #Bildschirmschoner Timer starten
    def bildschirmschoner_starten(self):
        if self.bildschirmschoner_job is not None:
            try:
                self.after_cancel(self.bildschirmschoner_job) #alten Timer stoppen
            except:
                pass
        
        self.bildschirmschoner_job = self.after(BILDSCHIRMSCHONER_ZEIT, self.bildschirmschoner_anzeigen) #neuen Timer starten
    
    #Bildschirmschoner zurücksetzen
    def bildschirmschoner_reset(self, event = None):
        if self.bildschirmschoner_aktiv:
            self.bildschirmschoner_aus() #Bildschirmschoner ausblenden
        
        self.bildschirmschoner_starten() #Timer neu starten
    
    #Bildschirmschoner anzeigen
    def bildschirmschoner_anzeigen(self):
        if self.bildschirmschoner_aktiv:
            return
        
        self.bildschirmschoner_job = None #Timer ist fertig
        self.bildschirmschoner_aktiv = True #Status setzen
        self.bildschirmschoner_frame = ctk.CTkFrame(self, fg_color = "black") #schwarzer Bildschirm
        self.bildschirmschoner_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
        
        uhr = datetime.now().strftime("%H:%M") #Uhrzeit anzeigen
        uhr_label = ctk.CTkLabel(self.bildschirmschoner_frame, text = uhr, font = self.schrift_groß, text_color = "white")
        uhr_label.pack(expand = True)
        
        text = ctk.CTkLabel(self.bildschirmschoner_frame, text = BILDSCHIRMSCHONER_TEXT, font = self.schrift, text_color = "white")
        text.pack(pady = 40)
        self.bildschirmschoner_frame.lift() #nach vorne bringen
    
    #Bildschirmschoner ausblenden
    def bildschirmschoner_aus(self):
        if self.bildschirmschoner_frame is not None:
            self.bildschirmschoner_frame.destroy() #Frame löschen
        
        self.bildschirmschoner_frame = None #Variable leeren
        self.bildschirmschoner_aktiv = False #Status zurücksetzen
    
    #Ausgeliehene Artikel aus CSV laden
    def load_ausgeliehene(self):
        self.ausgeliehene = [] #Liste zurücksetzen
        
        #Setze K-Artikel auf Original-Menge (aus ARTIKEL)
        for a in self.artikel:
            if a[0] == "K":
                #Finde Original-Menge aus ARTIKEL
                original = next((art for art in ARTIKEL if art[1] == a[1]), None)
                if original:
                    a[4] = original[4]
            elif a[0] == "G":
                a[4] = False
        
        if not os.path.isfile(CSV_DATEI):
            return #Datei existiert nicht
        
        try:
            #Transaktionen pro Person und Artikel speichern
            transaktionen = {} #{(artikel_id, name, klasse, artikel_name): {"ausleihen": menge, "rückgaben": menge, "datum": ...}}
            k_artikel_netto = {} #{artikel_id: netto_ausgeliehen}
            
            with open(CSV_DATEI, "r", encoding = "utf-8") as f:
                reader = csv.reader(f, delimiter = ";")
                next(reader, None) #Header überspringen
                
                for row in reader:
                    if len(row) < 7:
                        continue #ungültige Zeile
                    
                    zeit, name, klasse, artikel_id, artikel_name, typ, menge = row[:7]
                    
                    try:
                        menge_int = int(menge.strip())
                    except:
                        menge_int = 1
                    
                    key = (artikel_id.strip(), name.strip(), klasse.strip(), artikel_name.strip())
                    
                    if key not in transaktionen:
                        transaktionen[key] = {"ausleihen": 0, "rückgaben": 0, "datum": zeit.strip()}
                    
                    if typ.strip() == "Ausleihe":
                        transaktionen[key]["ausleihen"] += menge_int
                        transaktionen[key]["datum"] = zeit.strip() #Aktualisiere zu neuestes Datum
                    elif typ.strip() == "Rückgabe":
                        transaktionen[key]["rückgaben"] += menge_int
                    
                    #Berechne netto für K-Artikel (artikel_id basiert)
                    if artikel_id.strip() not in k_artikel_netto:
                        k_artikel_netto[artikel_id.strip()] = 0
                    
                    if typ.strip() == "Ausleihe":
                        k_artikel_netto[artikel_id.strip()] -= menge_int
                    elif typ.strip() == "Rückgabe":
                        k_artikel_netto[artikel_id.strip()] += menge_int
            
            #Aktualisiere Status der G-Artikel basierend auf ausgeliehenen
            for (artikel_id, name, klasse, artikel_name), trans in transaktionen.items():
                ausgeliehene_menge = trans["ausleihen"] - trans["rückgaben"]
                if ausgeliehene_menge > 0:
                    ausgeliehen_artikel = {
                        "id": artikel_id,
                        "name": artikel_name,
                        "person": name,
                        "klasse": klasse,
                        "menge": str(ausgeliehene_menge),
                        "datum": trans["datum"]
                    }
                    self.ausgeliehene.append(ausgeliehen_artikel)
                    
                    #Markiere G-Artikel als ausgeliehen
                    for a in self.artikel:
                        if a[0] == "G" and a[1] == artikel_id:
                            a[4] = True
            
            #Aktualisiere Menge der K-Artikel
            for a in self.artikel:
                if a[0] == "K" and a[1] in k_artikel_netto:
                    original = next((art for art in ARTIKEL if art[1] == a[1]), None)
                    if original:
                        a[4] = original[4] + k_artikel_netto[a[1]]
            
            #Status nochmal mit genauer Log-Auswertung setzen
            aktuelle_ausleihen = self.get_ausgeliehene_from_csv() #offene Ausleihen holen
            self.ausgeliehene = [] #Liste neu machen
            
            for a in self.artikel:
                if a[0] == "G":
                    a[4] = False #erst alles frei setzen
            
            for (artikel_id, name, klasse, artikel_name), info in aktuelle_ausleihen.items():
                ausgeliehen_artikel = {
                    "id": artikel_id,
                    "name": artikel_name,
                    "person": info["person"],
                    "klasse": info["klasse"],
                    "menge": info["menge"],
                    "datum": info["datum"]
                }
                self.ausgeliehene.append(ausgeliehen_artikel) #offene Ausleihe speichern
                
                for a in self.artikel:
                    if a[0] == "G" and a[1] == artikel_id:
                        a[4] = True #großer Artikel ist ausgeliehen
        
        except Exception as e:
            print(f"Fehler beim Laden ausgeliehener Artikel: {e}")
    
    #Hauptfenster
    def haupt_fenster(self, alle_anzeigen = True):
        self.clear() #Fenster leeren
        self.load_ausgeliehene() #ausgeliehene Artikel neuladen
        if alle_anzeigen:
            self.gefiltert = self.artikel #wieder alles anzeigen
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wächst mit Fenster mit

        #Suchfeld
        suche = ctk.CTkButton(self, text = "Suchen", font = self.schrift, command = lambda: self.numpad(self.filter_id)) #Suche
        suche.grid(row = 0, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren

        #Kategorie-Filter
        kategorien = ["Alle", "Ausgeliehene", "CSV / LOG"] + sorted(set(a[3] for a in self.artikel)) #alle Kategorien + Log
        self.kategorie = ctk.CTkOptionMenu(self, values = kategorien, font = self.schrift,
                                           dropdown_font = self.schrift, command = self.filter_kat)
        self.kategorie.set("Alle") #Standard-Wert
        self.kategorie.grid(row = 1, column = 0, sticky = "ew", padx = 20) #in Grid platzieren
        
        #Artikel
        self.scroll = ctk.CTkScrollableFrame(self) #scrollbares Frame
        self.scroll.grid(row = 2, column = 0, sticky = "nsew", padx = 20, pady = 10) #in Grid platzieren
        self.grid_rowconfigure(2, weight = 1) #Row 2 wächst mit
        self.render_artikel() #Artikel anzeigen

        #Barcode Button
        barcode = ctk.CTkButton(self, text = "Barcode", font = self.schrift, command = self.barcode) #Barcode
        barcode.grid(row = 3, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren

    #Artikel anzeigen
    def render_artikel(self):
        for w in self.scroll.winfo_children(): #alte Artikel löschen
            w.destroy()

        for i, a in enumerate(self.gefiltert): #für jeden Artikel
            frame = ctk.CTkFrame(self.scroll) #Container für Artikel erstellen
            frame.grid(row = i // 2, column = i % 2, padx = 10, pady = 10, sticky = "nsew") #2-spaltig anordnen
            self.scroll.grid_columnconfigure(i % 2, weight = 1) #Spalte dehnt sich

            #Rotes Overlay nur in "Alle" Kategorie für ausgeliehene G-Artikel
            ist_ausgeliehen = self.kategorie.get() == "Alle" and a[0] == "G" and a[4] == True
            img = self.load_img(a[2], ausgeliehen = ist_ausgeliehen) #Bild laden mit Overlay wenn nötig
            bild = ctk.CTkLabel(frame, image = img, text = "") #Label mit Bild erstellen
            bild.image = img #Image speichern(verhindert Garbage Collection)
            bild.pack() #Label packen

            name_label = ctk.CTkLabel(frame, text = a[2], font = self.schrift) #Namen anzeigen
            name_label.pack()

            #ID anzeigen
            typ_label = ctk.CTkLabel(frame, text = f"ID: {a[1]}", font = self.schrift)
            typ_label.pack()
            
            #Bei ausgeliehenen Artikeln: Person und Klasse anzeigen
            if a[0] == "A":
                person_label = ctk.CTkLabel(frame, text = f"Von: {a[4]['person']}", font = self.schrift)
                person_label.pack()

            #nur Bild klickbar machen
            bild.bind("<Button-1>", lambda e, x = a: self.detail(x)) #öffnet Details

    #Filter Kategorie
    def filter_kat(self, k):
        if k == "Alle":
            self.gefiltert = self.artikel
        elif k == "Ausgeliehene":
            #Lese CSV direkt durch und zeige aktuelle ausgeliehene Artikel
            self.gefiltert = []
            ausgeliehene_dict = self.get_ausgeliehene_from_csv()
            
            for (artikel_id, name, klasse, artikel_name), info in ausgeliehene_dict.items():
                #Format: [Typ, ID, Name, Kategorie, Info-Dict]
                artikel_eintrag = [
                    "A", #Typ = Ausgeliehen
                    artikel_id,
                    artikel_name,
                    "Ausgeliehene",
                    info #Dictionary mit Person, Klasse, Menge, Datum
                ]
                self.gefiltert.append(artikel_eintrag)
        elif k == "CSV / LOG":
            self.csv_anzeigen() #CSV roh anzeigen
            return
        else:
            self.gefiltert = [a for a in self.artikel if a[3] == k]
        self.render_artikel() #aktualisieren
    
    #Lese ausgeliehene Artikel direkt aus CSV
    def get_ausgeliehene_from_csv(self):
        ausgeliehene_dict = {}
        
        if not os.path.isfile(CSV_DATEI):
            return ausgeliehene_dict
        
        try:
            offene_ausleihen = [] #offene Ausleihen aus dem Log
            
            with open(CSV_DATEI, "r", encoding = "utf-8") as f:
                reader = csv.reader(f, delimiter = ";")
                next(reader, None) #Header überspringen
                
                for row in reader:
                    if len(row) < 7:
                        continue #ungültige Zeile
                    
                    zeit, name, klasse, artikel_id, artikel_name, typ, menge = row[:7]
                    
                    try:
                        menge_int = int(menge.strip())
                    except:
                        menge_int = 1
                    
                    if typ.strip() == "Ausleihe":
                        offene_ausleihen.append({
                            "id": artikel_id.strip(),
                            "name": artikel_name.strip(),
                            "person": name.strip(),
                            "klasse": klasse.strip(),
                            "menge": menge_int,
                            "datum": zeit.strip()
                        }) #Ausleihe merken
                    elif typ.strip() == "Rückgabe":
                        rest = menge_int #Menge die zurückgegeben wird
                        
                        passende = [] #passt genau mit Name und Klasse
                        for eintrag in offene_ausleihen:
                            if eintrag["id"] == artikel_id.strip() and eintrag["name"] == artikel_name.strip() and eintrag["person"] == name.strip() and eintrag["klasse"] == klasse.strip() and eintrag["menge"] > 0:
                                passende.append(eintrag)
                        
                        if not passende:
                            for eintrag in offene_ausleihen:
                                if eintrag["id"] == artikel_id.strip() and eintrag["name"] == artikel_name.strip() and eintrag["menge"] > 0:
                                    passende.append(eintrag) #zur Not nur mit Artikel suchen
                        
                        for eintrag in passende:
                            if rest <= 0:
                                break
                            
                            weg = min(eintrag["menge"], rest) #nicht mehr abziehen als vorhanden
                            eintrag["menge"] -= weg #Menge abziehen
                            rest -= weg #Rest verringern
            
            #Filtere nur noch ausgeliehene (Ausleihe > Rückgabe)
            result = {} #fertige Liste
            for eintrag in offene_ausleihen:
                if eintrag["menge"] <= 0:
                    continue #ist zurückgegeben
                
                key = (eintrag["id"], eintrag["person"], eintrag["klasse"], eintrag["name"])
                
                if key not in result:
                    result[key] = {"person": eintrag["person"], "klasse": eintrag["klasse"], "menge": "0", "datum": eintrag["datum"]}
                
                neue_menge = int(result[key]["menge"]) + eintrag["menge"] #Mengen zusammenzählen
                result[key]["menge"] = str(neue_menge)
                result[key]["datum"] = eintrag["datum"] #letztes Datum anzeigen
            
            return result
        
        except Exception as e:
            print(f"Fehler beim Lesen der CSV: {e}")
            return ausgeliehene_dict
    
    #CSV Datei anzeigen
    def csv_anzeigen(self):
        for w in self.scroll.winfo_children(): #alte Artikel löschen
            w.destroy()
        
        self.scroll.grid_columnconfigure(0, weight = 1) #Spalte wächst mit
        
        titel = ctk.CTkLabel(self.scroll, text = "CSV / LOG", font = self.schrift_groß)
        titel.grid(row = 0, column = 0, sticky = "ew", padx = 20, pady = 10)
        
        if not os.path.isfile(CSV_DATEI):
            text = "CSV Datei nicht gefunden" #wenn Datei fehlt
        else:
            with open(CSV_DATEI, "r", encoding = "utf-8") as f:
                text = f.read() #CSV roh lesen
        
        if text.strip() == "":
            text = "CSV Datei ist leer" #wenn keine Daten drin sind
        
        log = ctk.CTkTextbox(self.scroll, font = self.schrift_log, height = 600) #Textfeld für Log
        log.grid(row = 1, column = 0, sticky = "nsew", padx = 20, pady = 10)
        log.insert("1.0", text) #CSV einfügen
        log.configure(state = "disabled") #nicht bearbeiten

    #Filter ID
    def filter_id(self, text):
        if text == "":
            self.gefiltert = self.artikel
        else:
            #Suche in normalen Artikeln
            self.gefiltert = [a for a in self.artikel if a[1] == text]
            
            #Suche auch in ausgeliehenen Artikeln
            ausgeliehene_dict = self.get_ausgeliehene_from_csv()
            for (artikel_id, name, klasse, artikel_name), info in ausgeliehene_dict.items():
                if artikel_id == text:
                    artikel_eintrag = [
                        "A",
                        artikel_id,
                        artikel_name,
                        "Ausgeliehene",
                        info
                    ]
                    self.gefiltert.append(artikel_eintrag)
        
        self.haupt_fenster(False) #Hauptfenster mit Suchergebnis laden

    #Numpad
    def numpad(self, callback):
        self.clear() #Fenster leeren
        self.grid_columnconfigure((0, 1, 2), weight = 1) #3x3 Grid
        self.back() #Zurück-Button

        entry = ctk.CTkEntry(self, font = self.schrift_groß) #Eingabefeld
        entry.grid(row = 0, column = 0, columnspan = 3, sticky = "ew", padx = 20, pady = 20)

        def add(x): #Ziffer hinzufügen
            entry.insert("end", x) #Hinten anfügen

        def delete(): #Ziffer löschen
            text = entry.get() #Text auslesen
            if text: #wenn nicht leer
                entry.delete(len(text) - 1) #Letzte Ziffer entfernen

        def ok(): #OK drücken
            callback(entry.get()) #Wert zurückgeben

        #Zahlenbuttons
        nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"] #Ziffern 1-9
        row = 1 #erste Zeile
        for i in range(0, 9, 3): #Gruppen von 3
            for j in range(3): #pro Reihe 3 Buttons
                ctk.CTkButton(self, text = nums[i + j], font = self.schrift, height = 80,
                              command = lambda x = nums[i + j]: add(x)).grid(row = row, column = j, sticky = "nsew", padx = 5, pady = 5)
            row += 1 #nächste Reihe

        #unterste Reihe
        löschen = ctk.CTkButton(self, text = "DEL", font = self.schrift, height = 80, command = delete)
        löschen.grid(row = row, column = 0, sticky = "nsew", padx = 5, pady = 5)
        zero = ctk.CTkButton(self, text = "0", font = self.schrift, height = 80, command = lambda: add("0"))
        zero.grid(row = row, column = 1, sticky = "nsew", padx = 5, pady = 5)
        bestätigen = ctk.CTkButton(self, text = "OK", font = self.schrift, height = 80, command = ok)
        bestätigen.grid(row = row, column = 2, sticky = "nsew", padx = 5, pady = 5)

        for i in range(row + 1): #alle Reihen
            self.grid_rowconfigure(i, weight = 1) #Reihen wachsen mit

    #Artikel-Details
    def detail(self, a):
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        self.reservierung_hinweis_anzeigen(a) #nächste Reservierung anzeigen
        self.grid_columnconfigure(0, weight = 1) #Spalte wachst mit Fenster mit

        img = self.load_img(a[2], True) #großes Bild laden(Name ist a[2])
        bild = ctk.CTkLabel(self, image = img, text = "") #Label mit Bild erstellen
        bild.image = img #Image speichern
        bild.grid(row = 0, column = 0, pady = 20) #anzeigen

        #Informationen
        info = ctk.CTkFrame(self) #Frame für Info erstellen
        info.grid(row = 1, column = 0, sticky = "ew", padx = 20) #in Grid platzieren
        info.grid_columnconfigure(0, weight = 1) #Spalte wachst mit
        artikelname = ctk.CTkLabel(info, text = a[2], font = self.schrift)
        artikelname.grid(row = 0, column = 0, sticky = "ew", pady = 10)
        
        info_row = 1
        
        #Kategorie nicht anzeigen für ausgeliehene Artikel
        if a[0] != "A":
            kategorie = ctk.CTkLabel(info, text = "Kategorie: " + a[3], font = self.schrift)
            kategorie.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
            info_row += 1
        
        id = ctk.CTkLabel(info, text = "ID: " + a[1], font = self.schrift)
        id.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
        info_row += 1
        
        #Bei ausgeliehenen Artikeln
        if a[0] == "A":
            ausgeliehen_info = a[4]
            status = ctk.CTkLabel(info, text = "Status: Ausgeliehen", font = self.schrift)
            status.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
            info_row += 1
            menge = ctk.CTkLabel(info, text = f"Anzahl: {ausgeliehen_info['menge']}", font = self.schrift)
            menge.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
            info_row += 1
            person = ctk.CTkLabel(info, text = f"Von: {ausgeliehen_info['person']} ({ausgeliehen_info['klasse']})", font = self.schrift)
            person.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
            info_row += 1
            datum = ctk.CTkLabel(info, text = f"Datum: {ausgeliehen_info['datum']}", font = self.schrift)
            datum.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
        else:
            #zeige Status nur bei großen Artikeln
            if a[0] == "G":
                status_text = "Status: Ausgeliehen" if a[4] else "Status: Verfügbar"
                status = ctk.CTkLabel(info, text = status_text, font = self.schrift)
                status.grid(row = info_row, column = 0, sticky = "ew", pady = 10)
                info_row += 1
            
            #zeige Menge nur bei kleinen Artikeln
            if a[0] == "K":
                menge = ctk.CTkLabel(info, text = f"Menge: {a[4] if a[4] is not None else 0}", font = self.schrift)
                menge.grid(row = info_row, column = 0, sticky = "ew", pady = 10)

        #Abstand
        if a[0] == "A":
            self.grid_rowconfigure(2, weight = 1) #Row 2 wachst mit
            btn_row = 3 #Buttons in Zeile 3 für ausgeliehene Artikel
        else:
            self.grid_rowconfigure(2, weight = 1) #Row 2 wachst mit
            btn_row = 2 #Buttons in Zeile 2 für normale Artikel

        #Buttons
        btn_frame = ctk.CTkFrame(self) #Button-Frame
        btn_frame.grid(row = btn_row, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren
        btn_frame.grid_columnconfigure((0, 1, 2), weight = 1) #Spalten dehnen sich mit

        #Bei ausgeliehenen Artikeln: nur Rückgabe möglich
        if a[0] == "A":
            rückgabe = ctk.CTkButton(btn_frame, text = "Rückgabe bestätigen", font = self.schrift, 
                                    command = lambda: self.rückgabe_ausgeliehen(a))
            rückgabe.grid(row = 0, column = 0, columnspan = 3, sticky = "ew", padx = 5, pady = 5)
        elif a[0] == "G": #wenn großer Artikel
            ausleihen = ctk.CTkButton(btn_frame, text = "Ausleihen", font = self.schrift, command = lambda: self.name_eingabe(a, "out", 1))
            if a[4]: #wenn ausgeliehen
                ausleihen.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            ausleihen.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)
            rückgabe = ctk.CTkButton(btn_frame, text = "Rückgabe", font = self.schrift, command = lambda: self.rückgabe_g_artikel(a))
            if not a[4]: #wenn nicht ausgeliehen
                rückgabe.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            rückgabe.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)
            reservieren = ctk.CTkButton(btn_frame, text = "Reservieren", font = self.schrift, command = lambda: self.reservierung_uebersicht(a))
            reservieren.grid(row = 0, column = 2, sticky = "ew", padx = 5, pady = 5)
        else: #wenn kleiner Artikel
            ausleihen = ctk.CTkButton(btn_frame, text = "Ausleihen", font = self.schrift, command = lambda: self.menge(a, "out"))
            if a[4] is None or a[4] == 0: #wenn keine Menge verfügbar
                ausleihen.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            ausleihen.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)
            rückgabe = ctk.CTkButton(btn_frame, text = "Rückgabe", font = self.schrift, command = lambda: self.menge(a, "in"))
            if a[4] is None or a[4] == 0: #wenn keine Menge ausgeliehen
                rückgabe.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            rückgabe.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)
            reservieren = ctk.CTkButton(btn_frame, text = "Reservieren", font = self.schrift, command = lambda: self.reservierung_uebersicht(a))
            reservieren.grid(row = 0, column = 2, sticky = "ew", padx = 5, pady = 5)

    #Rückgabe von ausgeliehenen Artikel bestätigen
    def rückgabe_ausgeliehen(self, a):
        ausgeliehen_info = a[4]
        typ = "in"
        anzahl = ausgeliehen_info["menge"]
        artikel_id = a[1]
        artikel_name = a[2]
        name = ausgeliehen_info["person"]
        klasse = ausgeliehen_info["klasse"]
        
        #Rückgabe speichern
        erfolgreich = self.daten_speichern(name, klasse, artikel_id, artikel_name, typ, anzahl)
        
        if erfolgreich:
            erfolgreich_frame = ctk.CTkFrame(self, fg_color = "green")
            erfolgreich_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
            text = ctk.CTkLabel(erfolgreich_frame, text = "Rückgabe gespeichert!", font = self.schrift_groß, text_color = "white")
            text.pack(expand = True)
            self.after(2000, lambda: [erfolgreich_frame.destroy(), self.haupt_fenster()])
    
    #Rückgabe für großen Artikel aus Detail-Fenster
    def rückgabe_g_artikel(self, a):
        ausgeliehene_dict = self.get_ausgeliehene_from_csv() #offene Ausleihen suchen
        passende_ausleihe = None #merkt die passende Ausleihe
        
        for (artikel_id, name, klasse, artikel_name), info in ausgeliehene_dict.items():
            if artikel_id == a[1]:
                passende_ausleihe = info #Ausleihe gefunden
                break
        
        if passende_ausleihe is None:
            a[4] = False #wenn nichts offen ist, lokal frei setzen
            self.haupt_fenster() #zurück ins Hauptmenü
            return
        
        erfolgreich = self.daten_speichern(passende_ausleihe["person"], passende_ausleihe["klasse"], a[1], a[2], "in", 1)
        
        if erfolgreich:
            a[4] = False #Status sofort frei setzen
            erfolgreich_frame = ctk.CTkFrame(self, fg_color = "green")
            erfolgreich_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
            text = ctk.CTkLabel(erfolgreich_frame, text = "Rückgabe gespeichert!", font = self.schrift_groß, text_color = "white")
            text.pack(expand = True)
            self.after(2000, lambda: [erfolgreich_frame.destroy(), self.haupt_fenster()])
    
    #Reservierungen laden
    def reservierungen_laden(self):
        reservierungen = [] #Liste für Reservierungen
        
        if not os.path.isfile(RESERVIERUNG_DATEI):
            return reservierungen #Datei gibt es noch nicht
        
        try:
            with open(RESERVIERUNG_DATEI, "r", encoding = "utf-8") as f:
                reader = csv.reader(f, delimiter = ";")
                next(reader, None) #Header überspringen
                
                for row in reader:
                    if len(row) < 6:
                        continue #ungültige Zeile
                    
                    datum, name, klasse, artikel_id, artikel_name, zeit = row[:6]
                    reservierungen.append({
                        "datum": datum.strip(),
                        "name": name.strip(),
                        "klasse": klasse.strip(),
                        "artikel_id": artikel_id.strip(),
                        "artikel_name": artikel_name.strip(),
                        "zeit": zeit.strip()
                    })
            
            return reservierungen
        
        except Exception as e:
            print(f"Fehler beim Laden der Reservierungen: {e}")
            return reservierungen
    
    #Hinweis für nächste Reservierung anzeigen
    def reservierung_hinweis_anzeigen(self, a):
        reservierungen = self.reservierungen_laden() #Reservierungen laden
        reservierung = naechste_reservierung(reservierungen, a[1]) #nächste Reservierung suchen
        
        if reservierung is None:
            text = "Keine Reservierung" #nichts geplant
        else:
            text = "Spätestens zurück:\n" + reservierung["datum"] #Rückgabe-Hinweis
        
        hinweis = ctk.CTkLabel(self, text = text, font = self.schrift_groß, fg_color = "lightgray",
                              text_color = "black", corner_radius = 6)
        hinweis.place(x = 10, y = 10, anchor = "nw") #oben links anzeigen
    
    #Kalender Übersicht für Reservierung
    def reservierung_uebersicht(self, a):
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wächst mit
        
        titel = ctk.CTkLabel(self, text = "Reservierung\n" + a[2], font = self.schrift_groß)
        titel.grid(row = 0, column = 0, sticky = "ew", padx = 20, pady = 20)
        
        scroll = ctk.CTkScrollableFrame(self) #Kalender Raster
        scroll.grid(row = 1, column = 0, sticky = "nsew", padx = 20, pady = 10)
        spalten = max(1, KALENDER_SPALTEN) #mindestens eine Spalte
        for spalte in range(spalten):
            scroll.grid_columnconfigure(spalte, weight = 1) #Spalten wachsen mit
        self.grid_rowconfigure(1, weight = 1)
        
        reservierungen = self.reservierungen_laden() #Reservierungen aus Datei
        tage = naechste_tage(KALENDER_TAGE) #Tage für Kalender
        
        for i, datum in enumerate(tage):
            reservierung = reservierung_finden(reservierungen, a[1], datum) #Reservierung suchen
            row = i // spalten #Kalender Zeile
            column = i % spalten #Kalender Spalte
            
            if reservierung is None:
                text = datum + "\nfrei" #Tag ist frei
                btn = ctk.CTkButton(scroll, text = text, font = self.schrift, height = 100,
                                    command = lambda d = datum: self.reservierung_name_eingabe(a, d))
            else:
                text = datum + "\nbelegt:\n" + reservierung["name"] + " (" + reservierung["klasse"] + ")"
                btn = ctk.CTkButton(scroll, text = text, font = self.schrift, height = 100)
                btn.configure(state = "disabled", fg_color = "lightgray") #nicht auswählbar
            
            btn.grid(row = row, column = column, sticky = "nsew", padx = 5, pady = 5)
        
        self.back_nach_vorne() #X-Button nach vorne
    
    #Name und Klasse für Reservierung
    def reservierung_name_eingabe(self, a, datum):
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wächst mit
        
        label = ctk.CTkLabel(self, text = "Reservieren am\n" + datum, font = self.schrift_groß)
        label.grid(row = 0, column = 0, sticky = "ew", padx = 20, pady = 20)
        
        frame = ctk.CTkFrame(self) #Eingabe Frame
        frame.grid(row = 1, column = 0, sticky = "ew", padx = 20, pady = 10)
        frame.grid_columnconfigure(0, weight = 1)
        
        name_label = ctk.CTkLabel(frame, text = "Name:", font = self.schrift)
        name_label.grid(row = 0, column = 0, sticky = "w", pady = 5)
        name_entry = ctk.CTkEntry(frame, font = self.schrift)
        name_entry.grid(row = 1, column = 0, sticky = "ew", pady = 5)
        
        klasse_label = ctk.CTkLabel(frame, text = "Klasse:", font = self.schrift)
        klasse_label.grid(row = 2, column = 0, sticky = "w", pady = 5)
        klasse_entry = ctk.CTkEntry(frame, font = self.schrift)
        klasse_entry.grid(row = 3, column = 0, sticky = "ew", pady = 5)
        
        def ok():
            name = name_entry.get().strip()
            klasse = klasse_entry.get().strip()
            
            if not name or not klasse:
                return #nichts speichern wenn leer
            
            erfolgreich = self.reservierung_speichern(name, klasse, a[1], a[2], datum) #Reservierung speichern
            
            if erfolgreich:
                meldung = ctk.CTkFrame(self, fg_color = "green")
                meldung.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
                text = ctk.CTkLabel(meldung, text = "Reserviert!", font = self.schrift_groß, text_color = "white")
                text.pack(expand = True)
                self.after(2000, lambda: [meldung.destroy(), self.reservierung_uebersicht(a)])
            else:
                meldung = ctk.CTkFrame(self, fg_color = "red")
                meldung.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
                text = ctk.CTkLabel(meldung, text = "Schon belegt!", font = self.schrift_groß, text_color = "white")
                text.pack(expand = True)
                self.after(2000, lambda: [meldung.destroy(), self.reservierung_uebersicht(a)])
        
        self.grid_rowconfigure(2, weight = 1) #Abstand
        ok_btn = ctk.CTkButton(self, text = "Reservieren", font = self.schrift, command = ok)
        ok_btn.grid(row = 3, column = 0, sticky = "ew", padx = 20, pady = 10)
    
    #Reservierung speichern
    def reservierung_speichern(self, name, klasse, artikel_id, artikel_name, datum):
        reservierungen = self.reservierungen_laden() #alte Reservierungen laden
        
        if reservierung_ist_belegt(reservierungen, artikel_id, datum):
            return False #Datum ist schon belegt
        
        zeit = datetime.now().strftime("%d.%m.%Y %H:%M:%S") #jetzt
        daten = [datum, name, klasse, str(artikel_id), str(artikel_name), zeit]
        
        try:
            datei_existiert = os.path.isfile(RESERVIERUNG_DATEI) #checken ob Datei existiert
            
            with open(RESERVIERUNG_DATEI, "a", newline = "", encoding = "utf-8") as f:
                writer = csv.writer(f, delimiter = ";")
                
                if not datei_existiert:
                    writer.writerow(["Datum", "Name", "Klasse", "Artikel ID", "Artikel Name", "Reserviert am"])
                
                writer.writerow(daten)
            
            return True
        
        except Exception as e:
            print(f"Fehler beim Speichern der Reservierung: {e}")
            return False

    #Menge-Eingabe
    def menge(self, a, typ):
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wachst mit Fenster mit

        menge = 0 #Zähler
        max_menge = a[4] if typ == "out" else None #Max verfügbar
        
        #Ausleihen mit Limit oder Rückgabe ohne Limit
        if typ == "out":
            label_text = f"Anzahl: 0 / {max_menge}" #mit Maximum
        else:
            label_text = "Anzahl: 0" #ohne Maximum
        
        label = ctk.CTkLabel(self, text = label_text, font = self.schrift_groß) #Anzeige
        label.grid(row = 0, column = 0, pady = 40)

        def plus(): #Plus-Button
            nonlocal menge #Menge aus äußerer Funktion
            if typ == "out" and menge < max_menge: #Ausleihen mit Limit
                menge += 1 #erhöhen
            elif typ == "in": #Rückgabe ohne Limit
                menge += 1 #erhöhen
            
            if typ == "out": #wenn Ausleihen
                label.configure(text = f"Anzahl: {menge} / {max_menge}") #mit Maximum
            else: #wenn Rückgabe
                label.configure(text = f"Anzahl: {menge}") #ohne Maximum

        def minus(): #Minus-Button
            nonlocal menge #Menge aus äußerer Funktion
            if menge > 0: #nur wenn > 0
                menge -= 1 #verringern
            
            if typ == "out": #wenn Ausleihen
                label.configure(text = f"Anzahl: {menge} / {max_menge}") #mit Maximum
            else: #wenn Rückgabe
                label.configure(text = f"Anzahl: {menge}") #ohne Maximum

        def ok(): #Bestätigung
            if menge == 0:
                return
            #Name und Klasse eingeben
            self.name_eingabe(a, typ, menge)

        #Abstand
        self.grid_rowconfigure(1, weight = 1) #Zeile 1 wachst mit

        #Buttons
        btn_frame = ctk.CTkFrame(self) #Button-Frame
        btn_frame.grid(row = 2, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren
        btn_frame.grid_columnconfigure((0, 1), weight = 1) #beide Spalten dehnen
        minuss = ctk.CTkButton(btn_frame, text = "-", font = self.schrift, height = 100, command = minus)
        minuss.grid(row = 0, column = 0, sticky = "ew", padx = 5)
        pluss = ctk.CTkButton(btn_frame, text = "+", font = self.schrift, height = 100, command = plus)
        pluss.grid(row = 0, column = 1, sticky = "ew", padx = 5)
        okk = ctk.CTkButton(btn_frame, text = "Bestätigen", font = self.schrift, command = ok)
        okk.grid(row = 1, column = 0, columnspan = 2, sticky = "ew", padx = 5, pady = 10)

    #Name und Klasse Eingabe
    def name_eingabe(self, a, typ, anzahl):
        artikel_id = a[1]
        artikel_name = a[2]
        
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wachst mit

        if anzahl == 0: #wenn keine Menge ausgewählt
            self.haupt_fenster() #zurück zum Hauptfenster
            return

        #Abstand oben um X-Button zu vermeiden
        spacer = ctk.CTkLabel(self, text = "", height = 50)
        spacer.grid(row = 0, column = 0)
        
        #Label oben
        label = ctk.CTkLabel(self, text = "Name & Klasse\neingeben!", font = self.schrift_groß)
        label.grid(row = 1, column = 0, sticky = "ew", padx = 20, pady = 20)
        
        #Frame für Eingaben - weiter unten
        frame = ctk.CTkFrame(self)
        frame.grid(row = 2, column = 0, sticky = "ew", padx = 20, pady = 10)
        frame.grid_columnconfigure(0, weight = 1)

        #Name Label und Entry
        name_label = ctk.CTkLabel(frame, text = "Name:", font = self.schrift)
        name_label.grid(row = 0, column = 0, sticky = "w", pady = 5)
        name_entry = ctk.CTkEntry(frame, font = self.schrift)
        name_entry.grid(row = 1, column = 0, sticky = "ew", pady = 5)
        
        #Klasse Label und Entry
        klasse_label = ctk.CTkLabel(frame, text = "Klasse:", font = self.schrift)
        klasse_label.grid(row = 2, column = 0, sticky = "w", pady = 5)
        klasse_entry = ctk.CTkEntry(frame, font = self.schrift)
        klasse_entry.grid(row = 3, column = 0, sticky = "ew", pady = 5)
        
        #Bestätigen Button
        def ok():
            name = name_entry.get()
            klasse = klasse_entry.get()
            
            if not name or not klasse: #wenn leer
                return
            
            #Daten speichern
            erfolgreich = self.daten_speichern(name, klasse, artikel_id, artikel_name, typ, anzahl)
            
            if erfolgreich:
                #Aktualisiere die Artikel-Liste
                if typ == "out": #wenn Ausleihe
                    if a[0] == "G":
                        a[4] = True #Status: ausgeliehen
                    else: #Kleine Artikel
                        a[4] -= anzahl #Menge reduzieren
                elif typ == "in": #wenn Rückgabe
                    if a[0] == "G":
                        a[4] = False #Status: verfügbar
                    else: #Kleine Artikel
                        a[4] += anzahl #Menge erhöhen
                
                erfolgreich = ctk.CTkFrame(self, fg_color = "green")
                erfolgreich.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
                text = ctk.CTkLabel(erfolgreich, text = "Gespeichert!", font = self.schrift_groß, text_color = "white")
                text.pack(expand = True)
                self.after(2000, lambda: [erfolgreich.destroy(), self.haupt_fenster()])

        #Abstand
        self.grid_rowconfigure(3, weight = 1) #Zeile 3 wachst mit

        ok_btn = ctk.CTkButton(self, text = "Bestätigen", font = self.schrift, command = ok)
        ok_btn.grid(row = 4, column = 0, sticky = "ew", padx = 20, pady = 10)

    #Daten speichern
    def daten_speichern(self, name, klasse, artikel_id, artikel_name, typ, anzahl):
        typ_text = "Ausleihe" if typ == "out" else "Rückgabe"
        
        #Daten vorbereiten
        zeit = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        daten = [zeit, name, klasse, str(artikel_id), str(artikel_name), typ_text, str(anzahl)]
        
        try:
            #checken ob Datei existiert
            datei_existiert = os.path.isfile(CSV_DATEI)
            
            with open(CSV_DATEI, "a", newline = "", encoding = "utf-8") as f:
                writer = csv.writer(f, delimiter = ";")
                
                #Wenn neu, Header schreiben
                if not datei_existiert:
                    writer.writerow(["Datum/Zeit", "Name", "Klasse", "Artikel ID", "Artikel Name", "Typ", "Menge"])
                
                writer.writerow(daten)
            
            return True
        
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")
            return False

    #Barcode-Scanner
    def barcode(self):
        self.clear() #Fenster leeren
        self.back() #Zurück-Button
        info = ctk.CTkLabel(self, text = "In Bearbeitung", font = self.schrift_groß)
        info.pack(expand = True)

    #Bild laden
    def load_img(self, name, big = False, ausgeliehen = False):
        size = (BILD_GROESSE_GROSS, BILD_GROESSE_GROSS) if big else (BILD_GROESSE_KLEIN, BILD_GROESSE_KLEIN) #Größe je nach Fenster
        try:
            img = Image.open(name + ".png") #versuchen zu laden
        except:
            img = Image.open("Platzhalter.png")
        
        #Wenn ausgeliehen, rotes Overlay
        if ausgeliehen:
            overlay = Image.new("RGBA", img.size, (255, 0, 0, 120)) #rotes Overlay (semi-transparent)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
        
        return ctk.CTkImage(img, size = size) #als CTk-Image zurückgeben

    #Zurück-Button oben rechts
    def back(self):
        self.back_button = ctk.CTkButton(self, text = "X", fg_color = "red", hover_color = "darkred",
                                         font = self.schrift, width = 50, command = self.haupt_fenster)
        self.back_button.place(relx = 1, x = -10, y = 10, anchor = "ne")
        self.back_nach_vorne() #sofort nach vorne
        self.after(50, self.back_nach_vorne) #nach Aufbau nochmal nach vorne
    
    #Zurück-Button nach vorne holen
    def back_nach_vorne(self):
        try:
            if self.back_button is not None:
                self.back_button.lift() #über andere Widgets legen
        except:
            pass

    #alles löschen
    def clear(self):
        for i in self.winfo_children(): #alles durchgehen
            i.destroy() #löschen
        self.back_button = None #alter Button ist gelöscht

#starten
if __name__ == "__main__":
    app = App()
    app.mainloop()
