import json
from Meter import Meter
import time

class MeterDaoBT:
    def __init__(self, btree):
        self.db = btree
       
    async def AddMeter(self, meter):
        db = self.db
        meter["id"] = str(time.time_ns())                
        db.insert((meter["id"], meter))
        newMeter = await self.GetMeterById(meter["id"])
        
        return newMeter

    async def UpdateMeter(self, id, meter):
        db = self.db
        db.update_value(id, meter)
        
        updatedMeter = await self.GetMeterById(id)
        return updatedMeter

    async def GetMeterById(self, id):
        db = self.db
        savedMeter = db.find(id)
        return savedMeter

    async def GetAllMeters(self):
        db = self.db
        result = []
        
        for key in db:
            meter = db.get_value(key)
            result.append(json.loads(meter))
            
        return result

    async def GetMeterCount(self):
        db = self.db
        return db.count_all()
        
    async def DeleteMeter(self, id):
        db = self.db
        result = "Meter not found..."

        if (db.find(id) != None):
            db.delete(id)                
            result = "Meter deleted..."            
            
        return result                    

    async def DeleteAllMeters(self):
        db = self.db
        db.delete_all()
        
        result = "All Meters deleted..."            
        return result                    

    def printDb(self, db):
        print("meter db content...")
        for key in db:
            print(key)
            for word in db.values(key):
                print(key)                
                print(word)
                
