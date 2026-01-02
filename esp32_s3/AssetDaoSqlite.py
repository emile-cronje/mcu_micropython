from EntityDaoSqlite import EntityDaoSqlite
import time
import sqlite

class AssetDaoSqlite():
    def __init__(self, doConn):
        #print("ToDoDaoSqlite init..." + dbName)
#        super().__init__(dbName)
        self.asyncDbConn = doConn
        self.tableName = "assets"
        self.assetId = 1

    async def InitDb(self):
        print("InitDb starting...")
        self.asyncDbConn.execute("DROP TABLE IF EXISTS assets;")
        self.asyncDbConn.execute('''CREATE TABLE IF NOT EXISTS assets
                    (ID            INTEGER PRIMARY KEY,
                    VERSION        INTEGER NOT NULL,
                    CLIENT_ID		INTEGER,
                    MESSAGE_ID		INTEGER,
                    GUID           TEXT    NOT NULL,                    
                    CODE           TEXT    NOT NULL,
                    DESCRIPTION    TEXT    NOT NULL,         
                    IS_MSI    BOOL     NOT NULL);''')
        self.asyncDbConn.execute('''CREATE UNIQUE INDEX index_code ON assets(code);''')

        print("Asset table initialised...")        

    async def AddAsset(self, asset):
        sql = "INSERT INTO assets VALUES (?, 0, ?, ?, ?, ?, ?, False);"
        
        self.asyncDbConn.execute(sql, (self.assetId, asset["clientId"], asset["messageId"], asset["guid"], asset["code"], asset["description"]))
        print("Asset created...")
        savedAsset = await self.GetAssetById(self.assetId)

        self.assetId += 1
        return savedAsset

    async def UpdateAsset(self, id, asset):
        sql = f"UPDATE {self.tableName} SET version = ?, code = ?, description = ?, is_msi = ?, message_id = ? WHERE id = ?;"
        self.asyncDbConn.execute(sql, (asset["version"], asset["code"], asset["description"], asset["isMsi"], asset["messageId"], id))        

        print("Asset updated...")                
        updatedAsset = await self.GetAssetById(id)
        
        return updatedAsset

    async def GetAssetById(self, id):
        assetExists = await self.AssetExists(id)
        
        if (assetExists == False):
            return None
        
        with self.asyncDbConn.execute(f"SELECT id, version, code, description, is_msi, client_id, message_id, guid FROM {self.tableName} WHERE Id = {id}") as cursor:        
            asset = {}

            if cursor:
                for row in cursor:
                    asset["id"] = row[0]            
                    asset["version"] = row[1]                        
                    asset["code"] = row[2]
                    asset["description"] = row[3]
                    asset["isMsi"] = bool(row[4])
                    asset["clientId"] = row[5]
                    asset["messageId"] = row[6]
                    asset["guid"] = row[7]                                                                

        return asset

    async def AssetExists(self, id):
        count = 0
        sql = f"SELECT COUNT(id) FROM {self.tableName} WHERE id = {id};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count > 0

    async def GetAssetCount(self):
        count = 0
        sql = f"SELECT COUNT(*) FROM {self.tableName};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count

    async def DeleteAsset(self, id):
        sql = f"DELETE FROM {self.tableName} WHERE Id = ?;"            
        self.asyncDbConn.execute(sql, (id))
        
    async def GetLastRowId(self):
        lastId = 0
        sql = "SELECT last_insert_rowid();"
        
        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                lastId = row[0]

        return lastId

    async def DeleteAllAssets(self):
        self.asyncDbConn.execute(f"DELETE FROM {self.tableName};")
        