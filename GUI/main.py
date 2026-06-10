#Imports
import customtkinter as ctk
from PIL import Image
import csv
from datetime import datetime
import os
os.environ["DISPLAY"] = ":0" #für Linux-Umgebungen ohne DISPLAY-Variable

#Dark Mode aktivieren
ctk.set_appearance_mode("light")

#Artikel: [Typ, ID, Name, Kategorie, Menge (nur bei K), ausgeliehen (nur bei G)]
#K = kleine Artikel (Menge), G = große Artikel (einzeln, keine Menge)
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

#Haupt-Klasse der App
class App(ctk.CTk):
    #Initialisierung
    def __init__(self):
        super().__init__()
        self.title("Sortieranlage") #Fenster-Titel
        self.attributes('-fullscreen', True) #Vollbild
        self.artikel = ARTIKEL #alle Artikel
        self.gefiltert = self.artikel #aktuelle Filterung
        self.schrift = ctk.CTkFont("Arial", 24) #Standard-Schrift
        self.schrift_groß = ctk.CTkFont("Arial", 40) #große Schrift
        self.haupt_fenster() #Hauptfenster 
    
    #Grid-Layout zurücksetzen
    def grid_zurücksetzen(self):
        for i in range(10): #alle Zeilen/Spalten
            self.grid_rowconfigure(i, weight = 0) #weight=0 --> bleibt bei Mindestgröße, wächst NICHT mit Fenster
            self.grid_columnconfigure(i, weight = 0) #weight=0 --> bleibt bei Mindestgröße, wächst NICHT mit Fenster
    
    #Hauptfenster
    def haupt_fenster(self):
        self.clear() #Fenster leeren
        self.grid_zurücksetzen() #Layout zurücksetzen
        self.grid_columnconfigure(0, weight = 1) #Spalte wächst mit Fenster mit

        #Suchfeld
        suche = ctk.CTkButton(self, text = "Suchen", font = self.schrift, command = lambda: self.numpad(self.filter_id)) #Suche
        suche.grid(row = 0, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren

        #Kategorie-Filter
        kategorien = ["Alle"] + sorted(set(a[3] for a in self.artikel)) #alle Kategorien
        self.kategorie = ctk.CTkOptionMenu(self, values = kategorien, font = self.schrift,
                                           dropdown_font = self.schrift, command = self.filter_kat)
        self.kategorie.set("Alle") #Standard-Wert
        self.kategorie.grid(row = 1, column = 0, sticky="ew", padx=20) #in Grid platzieren
        
        #Artikel
        self.scroll = ctk.CTkScrollableFrame(self) #scrollbares Frame
        self.scroll.grid(row = 2, column = 0, sticky = "nsew", padx = 20, pady = 10) #in Grid platzieren
        self.grid_rowconfigure(2, weight = 1) #Row 2 wächst mit
        self.render_artikel() #Artikel anzeigen

        #Barcode Button
        barcode = ctk.CTkButton(self, text = "Barcode", font = self.schrift, command = self.barcode) #Barcode
        barcode.grid(row = 3, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren

    #Artikel anzeigen (KI)
    def render_artikel(self):
        for w in self.scroll.winfo_children(): #alte Artikel löschen
            w.destroy()

        for i, a in enumerate(self.gefiltert): #für jeden Artikel
            frame = ctk.CTkFrame(self.scroll) #Container für Artikel erstellen
            frame.grid(row = i//2, column = i%2, padx = 10, pady = 10, sticky = "nsew") #2-spaltig anordnen
            self.scroll.grid_columnconfigure(i%2, weight = 1) #Spalte dehnt sich

            img = self.load_img(a[2]) #Bild laden
            bild = ctk.CTkLabel(frame, image = img, text = "") #Label mit Bild erstellen
            bild.image = img #Image speichern (verhindert Garbage Collection)
            bild.pack() #Label packen

            ctk.CTkLabel(frame, text = a[2], font = self.schrift).pack() #Namen anzeigen

            #ID anzeigen
            typ_label = ctk.CTkLabel(frame, text = f"ID: {a[1]}", font = self.schrift)
            typ_label.pack()

            #Click-Event
            frame.bind("<Button-1>", lambda e, x = a: self.detail(x)) #Frame klickbar
            bild.bind("<Button-1>", lambda e, x = a: self.detail(x)) #Label klickbar

    #Filter Kategorie
    def filter_kat(self, k):
        self.gefiltert = self.artikel if k == "Alle" else [a for a in self.artikel if a[3] == k]
        self.render_artikel() #aktualisieren

    #Filter ID
    def filter_id(self, text):
        self.gefiltert = self.artikel if text == "" else [a for a in self.artikel if a[1] == text]
        self.haupt_fenster() #Hauptfenster neu laden

    #Numpad
    def numpad(self, callback):
        self.clear() #Fenster leeren
        self.grid_columnconfigure((0,1,2), weight = 1) #3x3 Grid
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
        self.grid_columnconfigure(0, weight=1) #Spalte wachst mit Fenster mit

        #Bild laden und anzeigen
        img = self.load_img(a[2], True) #großes Bild laden (Name ist a[2])
        bild = ctk.CTkLabel(self, image = img, text = "") #Label mit Bild erstellen
        bild.image = img #Image speichern
        bild.grid(row = 0, column = 0, pady = 20) #anzeigen

        #Informationen
        info = ctk.CTkFrame(self) #Frame für Info erstellen
        info.grid(row = 1, column = 0, sticky = "ew", padx = 20) #in Grid platzieren
        info.grid_columnconfigure(0, weight = 1) #Spalte wachst mit
        artikelname = ctk.CTkLabel(info, text = a[2], font = self.schrift)
        artikelname.grid(row = 0, column = 0, sticky = "ew", pady = 10)
        kategorie = ctk.CTkLabel(info, text = "Kategorie: " + a[3], font = self.schrift)
        kategorie.grid(row = 1, column = 0, sticky = "ew", pady = 10)
        id = ctk.CTkLabel(info, text = "ID: " + a[1], font = self.schrift)
        id.grid(row = 2, column = 0, sticky = "ew", pady = 10)
        
        #zeige Status nur bei großen Artikeln
        if a[0] == "G":
            status_text = "Status: Ausgeliehen" if a[4] else "Status: Verfügbar"
            status = ctk.CTkLabel(info, text = status_text, font = self.schrift)
            status.grid(row = 3, column = 0, sticky = "ew", pady = 10)
        
        #zeige Menge nur bei kleinen Artikeln
        if a[0] == "K":
            menge = ctk.CTkLabel(info, text = f"Menge: {a[4] if a[4] is not None else 0}", font = self.schrift)
            menge.grid(row = 3, column = 0, sticky = "ew", pady = 10)

        #Abstand
        self.grid_rowconfigure(2, weight = 1) #Row 2 wachst mit

        #Buttons
        btn_frame = ctk.CTkFrame(self) #Button-Frame
        btn_frame.grid(row = 3, column = 0, sticky = "ew", padx = 20, pady = 10) #in Grid platzieren
        btn_frame.grid_columnconfigure((0, 1), weight = 1) #beide Spalten dehnen sich mit

        if a[0] == "G": #wenn großer Artikel
            ausleihen = ctk.CTkButton(btn_frame, text = "Ausleihen", font = self.schrift, command = lambda: self.name_eingabe(a[1], a[2], "out", "-"))
            if a[4]: #wenn ausgeliehen
                ausleihen.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            ausleihen.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)
            rückgabe = ctk.CTkButton(btn_frame, text = "Rückgabe", font = self.schrift, command = lambda: self.name_eingabe(a[1], a[2], "in", "-"))
            rückgabe.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)
        else: #wenn kleiner Artikel
            ausleihen = ctk.CTkButton(btn_frame, text = "Ausleihen", font = self.schrift, command = lambda: self.menge(a, "out"))
            if a[4] is None or a[4] == 0: #wenn keine Menge verfügbar
                ausleihen.configure(state = "disabled", fg_color = "lightgray") #Button deaktivieren
            ausleihen.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)
            rückgabe = ctk.CTkButton(btn_frame, text = "Rückgabe", font = self.schrift, command = lambda: self.menge(a, "in"))
            rückgabe.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)

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
            #Anzahl ändern
            a[4] += menge if typ == "in" else -menge #Menge addieren/subtrahieren
            
            #Name und Klasse eingeben
            self.name_eingabe(a[1], a[2], typ, menge)

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
    def name_eingabe(self, artikel_id, artikel_name, typ, anzahl):
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
                if typ == "out": #wenn Ausleihe
                    for a in self.artikel: #Artikel suchen
                        if a[1] == artikel_id:
                            a[4] = True if a[0] == "G" else None #Status ändern
                            break
                if typ == "in": #wenn Rückgabe
                    for a in self.artikel: #Artikel suchen
                        if a[1] == artikel_id:
                            a[4] = False if a[0] == "G" else None #Status ändern
                            break
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
        dateiname = "GUI/ausleihen.csv"
        typ_text = "Ausleihe" if typ == "out" else "Rückgabe"
        
        #Daten vorbereiten
        zeit = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        daten = [zeit, name, klasse, str(artikel_id), str(artikel_name), typ_text, str(anzahl)]
        
        try:
            #checken ob Datei existiert
            datei_existiert = os.path.isfile(dateiname)
            
            with open(dateiname, "a", newline = "", encoding = "utf-8") as f:
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
        import socket

        hostname = socket.gethostname()
        lokale_ip = socket.gethostbyname(hostname)
        
        ip_info = ctk.CTkLabel(self,text=lokale_ip,font=self.schrift_groß)
        ip_info.pack(expand = True)

    #Bild laden
    def load_img(self, name, big = False):
        size = (250, 250) if big else (150, 150) #Größe je nach Fenster
        try:
            img = Image.open("GUI/" + name + ".png") #versuchen zu laden
        except:
            img = Image.open("GUI/Platzhalter.png")
        return ctk.CTkImage(img, size = size) #als CTk-Image zurückgeben

    #Zurück-Button oben rechts
    def back(self):
        back = ctk.CTkButton(self, text = "X", fg_color = "red", font = ("Arial", 20), width = 50,
                      command = self.haupt_fenster)
        back.place(relx = 1, x = -10, y = 10, anchor = "ne")

    #alles löschen
    def clear(self):
        for i in self.winfo_children(): #alles durchgehen
            i.destroy() #löschen

#starten
app = App()
app.mainloop()
