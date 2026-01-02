import os
import json
from ToDoItem import ToDoItem
from btree_hybrid_disk_cache import BTree
import time

class ToDoDaoBT:
    def __init__(self, treeDepth, dir):
        self.db = BTree(t = treeDepth, cache_dir=dir)                        
       
    async def AddItem(self, item):
        db = self.db
        item["id"] = str(time.time_ns())                
        db.insert((item["id"], item))        
        newItem = await self.GetItemById(item["id"])
        
        return newItem

    async def UpdateItem(self, id, item):
        db = self.db
        db.update_value(id, item)        
        updatedItem = await self.GetItemById(id)
        
        return updatedItem
        
    async def GetItemById(self, id):
        db = self.db
        savedItem = db.find(id)        
        
        return savedItem

    async def GetAllItems(self):
        db = self.db
        result = []
        
        for key in db:
            item = db[key]            
            result.append(json.loads(item))
            
        return result

    async def GetItemCount(self):
        db = self.db
        return db.count_all()

    async def DeleteItem(self, id):
        db = self.db
        result = "Item not found..."

        if (db.find(id) != None):
            db.delete(db.root, (id,))            
            result = "Item deleted..."            
            
        return result                    

    async def DeleteAllItems(self):
        db = self.db
        db.delete_all()        
        
        result = "All Items deleted..."            
        return result                    

    def printDb(self, db):
        print("db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)