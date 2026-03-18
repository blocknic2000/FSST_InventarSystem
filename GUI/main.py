import customtkinter as ctk

#Hauptklasse für die GUI
class GUI(ctk.CTk):
    def __init__(self): #Konstruktor der GUI-Klasse
        super().__init__() #Fenster initialisieren

        self.title("Inventarsystem") #Titel vom Fenster
        self.after(0, lambda: self.state("zoomed")) #Vollbild

        self.main_frame = ctk.CTkFrame(self) #Rahmen
        self.main_frame.place(relx = 0.5, rely = 0.5, anchor = "center", relwidth = 0.35, relheight = 0.95) #Rahmen platzieren

        self.label = ctk.CTkLabel(self.main_frame, text = "Inventarsystem", font = ("Arial", 30)) #Überschrift
        self.label.pack(pady = 20) #Überschrift platzieren

        self.scroll = ctk.CTkScrollableFrame(self.main_frame) #Scrollframe
        self.scroll.pack(fill = "both", expand = True, padx = 20, pady = 15) #Scrollframe platzieren

#Programm starten
if __name__ == "__main__":
    gui = GUI() #GUI erstellen
    gui.mainloop() #GUI starten