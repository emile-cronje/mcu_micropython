import os
import json
from AssetTask import AssetTask
from btree_hybrid_disk_cache import BTree
import time

class AssetTaskDaoBT:
    def __init__(self, treeDepth, dir):
        self.db = BTree(t = treeDepth, cache_dir=dir)                        
       
    async def AddAssetTask(self, assetTask):
        db = self.db
        assetTask["id"] = str(time.time_ns())                
        db.insert((assetTask["id"], assetTask))
        newAssetTask = await self.GetAssetTaskById(assetTask["id"])
        
        return newAssetTask

    async def UpdateAssetTask(self, id, assetTask):
        db = self.db
        db.update_value(id, assetTask)
        
        updatedAssetTask = await self.GetAssetTaskById(id)
        return updatedAssetTask

    async def GetAssetTaskById(self, id):
        db = self.db
        assetTask = None
        savedAssetTask = db.find(id)
        
        return savedAssetTask

    async def GetAllAssetTasks(self):
        db = self.db
        result = []
        
        for key in self.assetTaskDb:
            assetTask = self.assetTaskDb[key]            
            result.append(json.loads(assetTask))
            
        return result

    async def GetTasksForAsset(self, assetId):
        db = self.db
        filter_func = lambda task: str(task["assetId"]) == str(assetId)
        tasks = db.traverse_func(filter_func)
        
        return tasks

    async def GetAssetTaskCount(self):
        db = self.db
        return db.count_all()
        
    async def DeleteAssetTask(self, id):
        db = self.db
        result = "Asset Task not found..."

        if (db.find(id) != None):
            db.delete(db.root, (id,))            
            result = "Asset deleted..."            

        return result                    

    async def DeleteAllAssetTasks(self):
        db = self.db
        db.delete_all()
        
        result = "All Asset Tasks deleted..."            
        return result                    

    def printDb(self, db):
        print("asset db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)
                
    async def GetTaskIdsForAsset(self, assetId):
        taskCount = await self.GetTaskCountForAsset(assetId)
        
        if (taskCount <= 0):
            return None
        
        tasks = await self.GetTasksForAsset(assetId)        
        taskIds = []

        for task in tasks:
            taskIds.append(task["id"])

        return taskIds
    
    async def GetTaskCountForAsset(self, assetId):
        db = self.db
        filter_func = lambda task: str(task["assetId"]) == str(assetId)
        tasks = db.traverse_func(filter_func)
        
        return len(tasks)
    