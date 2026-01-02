import os
import json
from Asset import Asset
from btree_hybrid_disk_cache import BTree
import time

class AssetDaoBT:
    def __init__(self, treeDepth, dir):
        self.db = BTree(t = treeDepth, cache_dir=dir)                        
       
    async def AddAsset(self, asset):
        db = self.db
        asset["id"] = str(time.time_ns())                        
        db.insert((asset["id"], asset))                
        newAsset = await self.GetAssetById(asset["id"])
        
        return newAsset

    async def UpdateAsset(self, id, asset):
        db = self.db
        db.update_value(id, asset)
        
        updatedAsset = await self.GetAssetById(id)
        return updatedAsset

    async def GetAssetById(self, id):
        db = self.db
        asset = None
        savedAsset = db.find(id)
        
        return savedAsset

    async def GetAllAssets(self):
        db = self.db
        result = []
        
        for key in db:
            asset = db.get_value(key)
            result.append(json.loads(asset))
            
        return result

    async def GetAssetCount(self):
        db = self.db
        return db.count_all()
        
    async def DeleteAsset(self, id):
        db = self.db
        result = "Asset not found..."

        if (db.find(id) != None):
            db.delete(db.root, (id,))            
            result = "Asset deleted..."            

        return result                    

    async def DeleteAllAssets(self):
        db = self.db
        db.delete_all()
        
        result = "All Assets deleted..."            
        return result                    

    def printDb(self, db):
        print("asset db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)