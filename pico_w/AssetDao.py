import ujson

class AssetDao:
    def __init__(self, dbConnectionPool):
        self.dbConnectionPool = dbConnectionPool
       
    async def AddAsset(self, clientId, asset):
        db = self.dbConnectionPool[clientId]
        db[asset["id"]] = ujson.dumps(asset)
        #db.flush()
        return await self.GetAssetById(clientId, asset["id"])

    async def UpdateAsset(self, clientId, id, asset):
        db = self.dbConnectionPool[clientId]
        db[id] = ujson.dumps(asset)        
        updatedAsset = await self.GetAssetById(clientId, id)
        return updatedAsset

    async def GetAssetById(self, clientId, id):
        db = self.dbConnectionPool[clientId]                
        savedAsset = db.get(id)
        return ujson.loads(savedAsset)            

    async def GetAllAssets(self, clientId):
        db = self.dbConnectionPool[clientId]                
        result = []
        
        for key in db:
            asset = db.get_value(key)
            result.append(json.loads(asset))
            
        return result

    async def GetAssetCount(self, clientId):
        db = self.dbConnectionPool[clientId]
        icount = 0
        
        for key in db:
            icount += 1
            
        return icount
        
    async def DeleteAsset(self, clientId, id):
        db = self.dbConnectionPool[clientId]                
        result = "Asset not found..."

        if (db.get(id) != None):
            del db[id]
            db.flush()            
            result = "Asset deleted..."            
            
        return result                    

    async def DeleteAllAssets(self, clientId):
        db = self.dbConnectionPool[clientId]
        
        for key in db:
            if (db.get(key) != None):
                del db[key]

        result = "All Assets deleted..."            
        return result                    

    def printDb(self, db):
        print("asset db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)