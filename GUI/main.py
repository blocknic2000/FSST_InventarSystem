import customtkinter as ctk
import os
from PIL import Image

#Hauptklasse für die GUI
class GUI(ctk.CTk):
    def __init__(self): #Konstruktor der GUI-Klasse
        super().__init__() #Fenster initialisieren

        self.title("Inventarsystem") #Titel vom Fenster
        self.after(0, lambda: self.state("zoomed")) #Vollbild

        self.main_frame = ctk.CTkFrame(self) #Rahmen
        self.main_frame.place(relx = 0.5, rely = 0.5, anchor = "center", relwidth = 0.35, relheight = 0.95) #Rahmen platzieren

        #Grid für responsive Design Unterteilung
        self.main_frame.rowconfigure(0, weight = 0)
        self.main_frame.rowconfigure(1, weight = 1)
        self.main_frame.rowconfigure(2, weight = 0)
        self.main_frame.columnconfigure(0, weight = 1)

        self.label = ctk.CTkLabel(self.main_frame, text = "Inventarsystem", font = ("Arial", 30)) #Überschrift
        self.label.grid(row = 0, column = 0, padx = 10, pady = (15, 8), sticky = "n")

        self.scroll = ctk.CTkScrollableFrame(self.main_frame) #Scrollframe
        self.scroll.grid(row = 1, column = 0, padx = 10, pady = 8, sticky = "nsew")



        # Artikel-Liste
        self.artikel = ["1", "2", "3", "Monitor", "Drucker", "Kamera"]

        # Einstellungen
        spalten = 3
        bild_groesse = (120, 120)

        # Placeholder laden
        script_dir = os.path.dirname(os.path.abspath(__file__))
        placeholder_path = os.path.join(script_dir, "placeholder.jpeg")
        placeholder_img = Image.open(placeholder_path)
        placeholder = ctk.CTkImage(light_image=placeholder_img, dark_image=placeholder_img, size=bild_groesse)

        # Grid konfigurieren (3 Spalten gleich breit)
        for i in range(spalten):
            self.scroll.grid_columnconfigure(i, weight=1)

        # Artikel durchgehen
        for index, name in enumerate(self.artikel):
            row = index // spalten
            col = index % spalten

            frame = ctk.CTkFrame(self.scroll)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="n")

            bild_pfad = os.path.join(script_dir, f"{name}.jpeg")

            # Bild laden oder Placeholder verwenden
            if os.path.exists(bild_pfad):
                img = Image.open(bild_pfad)
                bild = ctk.CTkImage(light_image=img, dark_image=img, size=bild_groesse)
            else:
                bild = placeholder

            # Bild anzeigen
            label_bild = ctk.CTkLabel(frame, image=bild, text="")
            label_bild.image = bild
            label_bild.pack(pady=(5, 2))

            # Name darunter
            label_text = ctk.CTkLabel(frame, text=name, font=("Arial", 16))
            label_text.pack(pady=(0, 5))



        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row = 2, column = 0, pady = (8, 15), sticky = "ew")
        button_frame.columnconfigure((0,1,2), weight = 1)

        self.button1 = ctk.CTkButton(button_frame, text = "Ausleihen")
        self.button1.grid(row = 0, column = 0, padx = 4, sticky = "ew")
        self.button2 = ctk.CTkButton(button_frame, text = "Zurückgeben")
        self.button2.grid(row = 0, column = 1, padx = 4, sticky = "ew")
        self.button3 = ctk.CTkButton(button_frame, text = "Barcode scannen")
        self.button3.grid(row = 0, column = 2, padx = 4, sticky = "ew")

        self.main_frame.bind("<Configure>", self._on_main_frame_resize)

    def _on_main_frame_resize(self, event):
        font_size = max(18, min(40, int(event.width / 10)))
        self.label.configure(font = ("Arial", font_size))



#Programm starten
if __name__ == "__main__":
    gui = GUI() #GUI erstellen
    gui.mainloop() #GUI starten