import ujson

class ToDoDao:
    def __init__(self, dbConnectionPool):
        self.dbConnectionPool = dbConnectionPool
    
    async def AddItem(self, clientId, item):
        db = self.dbConnectionPool[clientId]        
        db[item["id"]] = ujson.dumps(item)
        #db.flush()
        return await self.GetItemById(clientId, item["id"])        

    async def UpdateItem(self, clientId, id, item):
        db = self.dbConnectionPool[clientId]                
        db[id] = ujson.dumps(item)
        #db.flush()
        return await self.GetItemById(clientId, id)                

    async def GetItemById(self, clientId, id):
        db = self.dbConnectionPool[clientId]                        
        savedItem = db.get(id)
        return ujson.loads(savedItem)    

    async def GetAllItems(self):
        result = []
        
        for key in self.todoDb:
            item = self.todoDb[key]            
            result.append(ujson.loads(item))
            
        return result

    async def GetItemCount(self, clientId):
        db = self.dbConnectionPool[clientId]                                
        icount = 0
        
        for key in db:
            icount += 1
            
        return icount

    async def DeleteItem(self, id):
        result = "Item not found..."

        if (self.todoDb.get(id) != None):
            del self.todoDb[id]
            self.todoDb.flush()            
            result = "Item deleted..."            
            
        return result                    

    async def DeleteAllItems(self, clientId):
        db = self.dbConnectionPool[clientId]
        
        for key in db:
            if (db.get(key) != None):
                del db[key]

        result = "All Items deleted..."            
        return result                    

    def printDb(self, db):
        print("db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)      