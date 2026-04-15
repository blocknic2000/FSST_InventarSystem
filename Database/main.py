import mysql.connector as mysql
import config
def _connect():
    connection = mysql.connect(
        host=config.Database.HOST,
        user=config.Database.USER,
        password=config.Database.PASSWORD,
        database=config.Database.DATABASE
    )
    return connection.cursor()
class Item:
    def __init__(self, id, itemID, name, group, ammount):
        self.id:int = id
        self.itemID:int = itemID
        self.name:str = name
        self.group:str = group
        self.ammount:int = ammount
class Database:
    def __init__(self):
        self.cursor = _connect()
    def getAllFreeItems(self):
        self.cursor.execute("SELECT id,itemID,name,group,ammount FROM items WHERE deleted = 0 AND borrowed = 0")
        result = self.cursor.fetchall()
        items = []
        for row in result:
            item = Item(row[0], row[1], row[2], row[3], row[4])
            items.append(item)
        return items
    
    def getAllBorrowedItems(self):
        self.cursor.execute("SELECT id,itemID,name,group,ammount FROM items WHERE deleted = 0 AND borrowed = 1")
        result = self.cursor.fetchall()
        items = []
        for row in result:
            item = Item(row[0], row[1], row[2], row[3], row[4])
            items.append(item)
        return items
    def getAllItems(self):
        self.cursor.execute("SELECT id,itemID,name,group,ammount FROM items WHERE deleted = 0")
        result = self.cursor.fetchall()
        items = []
        for row in result:
            item = Item(row[0], row[1], row[2], row[3], row[4])
            items.append(item)
        return items
    def getItem(self, itemID=None, name=None):
        if itemID is not None:
            self.cursor.execute("SELECT id,itemID,name,group,ammount FROM items WHERE deleted = 0 AND itemID = %s", (itemID,))
        elif name is not None:
            self.cursor.execute("SELECT id,itemID,name,group,ammount FROM items WHERE deleted = 0 AND name = %s", (name,))
        else:
            return None
        result = self.cursor.fetchone()
        if result is not None:
            item = Item(result[0], result[1], result[2], result[3], result[4])
            return item
        else:
            return None
    def addItem(self, itemID, name, group, ammount):
        if self.getItem(itemID=itemID) is not None:
            return False


        self.cursor.execute("INSERT INTO items (itemID, name, group, ammount) VALUES (%s, %s, %s, %s)", (itemID, name, group, ammount))
        self.cursor.connection.commit()
    def deleteItem(self, id):
        self.cursor.execute("UPDATE items SET deleted = 1 WHERE id = %s", (id,))
        self.cursor.connection.commit()
    

    
if __name__ == "__main__":
    items = Database().getAllItems()
    for item in items:
        print(item)
        print(item.id, item.itemID, item.name, item.group, item.ammount)
    items = Database().getAllBorrowedItems()
    for item in items:
        print(item)
        print(item.id, item.itemID, item.name, item.group, item.ammount)
    items = Database().getAllFreeItems()
    for item in items:
        print(item)
        print(item.id, item.itemID, item.name, item.group, item.ammount)
    item = Database().getItem(itemID="12345")
    print(item)


    