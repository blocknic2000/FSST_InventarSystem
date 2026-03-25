import os
from PIP import Image, ImageOps

class InventoryLoader:
    def __init__(self, text_file, image_folder, size=(128, 128)):
        self.text_file = text_file
        self.image_folder = image_folder
        self.size = size

    def load_image(self, image_number):
        # Sucht passende Bilddatei über die Nummer
        possible_extensions = [".png", ".jpg", ".jpeg", ".webp"]

        for ext in possible_extensions:
            path = os.path.join(self.image_folder, f"{image_number}{ext}")
            if os.path.exists(path):
                with Image.open(path) as img:
                    img = img.convert("RGBA")
                    img = ImageOps.contain(img, self.size)  # proportional skalieren
                    return img

        return None  # falls kein Bild gefunden wurde

    def load_items(self):
        items = []

        with open(self.text_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue  # leere Zeilen überspringen

                parts = line.split(";")
                if len(parts) != 3:
                    continue  # falsches Format überspringen

                item_id = int(parts[0])
                name = parts[1]
                image_number = parts[2]

                image = self.load_image(image_number)

                item = {
                    "id": item_id,
                    "name": name,
                    "image_number": image_number,
                    "image": image
                }

                items.append(item)

        # alphabetisch nach Name sortieren
        items.sort(key=lambda x: x["name"].lower())

        return items


# Beispiel-Verwendung
loader = InventoryLoader(
    text_file="Daten.txt",
    image_folder="GIT",
    size=(128, 128)
)

items = loader.load_items()

for item in items:
    print("ID:", item["id"], "| Name:", item["name"], "| Bildnummer:", item["image_number"])
    if item["image"] is not None:
        print("Bildgröße:", item["image"].size)
    else:
        print("Bild nicht gefunden")