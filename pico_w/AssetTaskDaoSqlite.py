from EntityDaoSqlite import EntityDaoSqlite
import time
import sqlite

class AssetTaskDaoSqlite():
    def __init__(self, doConn):
        #print("ToDoDaoSqlite init..." + dbName)
#        super().__init__(dbName)
        self.asyncDbConn = doConn
        self.tableName = "asset_tasks"
        self.assetTaskId = 1        

    async def InitDb(self):
        print("InitDb starting...")
        self.asyncDbConn.execute("DROP TABLE IF EXISTS asset_tasks;")
        self.asyncDbConn.execute('''CREATE TABLE IF NOT EXISTS asset_tasks
                    (ID            INTEGER PRIMARY KEY,
                    VERSION        INTEGER NOT NULL,
                    CLIENT_ID		INTEGER,
                    MESSAGE_ID		INTEGER,
                    ASSET_ID		INTEGER,                    
                    CODE           TEXT    NOT NULL,
                    DESCRIPTION    TEXT    NOT NULL,         
                    IS_RFS    BOOL     NOT NULL);''')
        self.asyncDbConn.execute('''CREATE UNIQUE INDEX index_task_code ON asset_tasks(code);''')

        print("Asset task table initialised...")        

    async def AddAssetTask(self, assetTask):
        print("Asset task create start...")        
        sql = "INSERT INTO asset_tasks VALUES (?, 0, ?, ?, ?, ?, ?, False);"
        
        self.asyncDbConn.execute(sql, (self.assetTaskId, assetTask["clientId"], assetTask["messageId"], assetTask["assetId"], assetTask["code"], assetTask["description"]))
        savedAssetTask = await self.GetAssetTaskById(self.assetTaskId)

        self.assetTaskId += 1
        return savedAssetTask
    
    async def UpdateAssetTask(self, id, assetTask):
        sql = f"UPDATE {self.tableName} SET version = ?, code = ?, description = ?, is_rfs = ?, message_id = ? WHERE id = ?;"
        self.asyncDbConn.execute(sql, (assetTask["version"], assetTask["code"], assetTask["description"], assetTask["isRfs"], assetTask["messageId"], id))        

        print("Asset task updated...")                
        updatedAssetTask = await self.GetAssetTaskById(id)
        
        return updatedAssetTask

    async def GetAssetTaskById(self, id):
        assetTaskExists = await self.AssetTaskExists(id)
        
        if (assetTaskExists == False):
            return None
        
        with self.asyncDbConn.execute(f"SELECT id, version, code, description, is_rfs, client_id, message_id, asset_id FROM {self.tableName} WHERE Id = {id}") as cursor:        
            assetTask = {}

            if cursor:
                for row in cursor:
                    assetTask["id"] = row[0]            
                    assetTask["version"] = row[1]                        
                    assetTask["code"] = row[2]
                    assetTask["description"] = row[3]
                    assetTask["isRfs"] = bool(row[4])
                    assetTask["clientId"] = row[5]
                    assetTask["messageId"] = row[6]
                    assetTask["assetId"] = row[7]                                                                

        return assetTask

    async def AssetTaskExists(self, id):
        count = 0
        sql = f"SELECT COUNT(id) FROM {self.tableName} WHERE id = {id};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count > 0

    async def GetAssetTaskCount(self):
        count = 0
        sql = f"SELECT COUNT(*) FROM {self.tableName};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count

    async def DeleteAssetTask(self, id):
        sql = f"DELETE FROM {self.tableName} WHERE Id = ?;"            
        self.asyncDbConn.execute(sql, (id))
        
    async def GetLastRowId(self):
        lastId = 0
        sql = "SELECT last_insert_rowid();"
        
        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                lastId = row[0]

        return lastId

    async def DeleteAllAssetTasks(self):
        self.asyncDbConn.execute(f"DELETE FROM {self.tableName};")
        