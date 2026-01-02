from EntityDaoSqlite import EntityDaoSqlite
import time
import sqlite
import urandom

class ToDoDaoSqlite():
    def __init__(self, doConn):
        #print("ToDoDaoSqlite init..." + dbName)
#        super().__init__(dbName)
        self.asyncDbConn = doConn
        self.tableName = "items"
        self.itemId = 1        

    async def InitDb(self):
        print("InitDb starting...")
        self.asyncDbConn.execute("DROP TABLE IF EXISTS items;")
        self.asyncDbConn.execute('''CREATE TABLE IF NOT EXISTS items
                    (ID            INTEGER PRIMARY KEY,
                    VERSION        INTEGER NOT NULL,
                    CLIENT_ID		INTEGER,
                    MESSAGE_ID		INTEGER,                                        
                    NAME           TEXT    NOT NULL,
                    DESCRIPTION    TEXT    NOT NULL,         
                    IS_COMPLETE    BOOL     NOT NULL);''')
        self.asyncDbConn.execute('''CREATE UNIQUE INDEX index_name ON items(name);''')

        print("Todo table initialised...")        

    async def AddItem(self, item):
        sql = "INSERT INTO items VALUES (?, 0, ?, ?, ?, ?, False);"
        
        self.asyncDbConn.execute(sql, (self.itemId, item["clientId"], item["messageId"], item["name"], item["description"]))
        savedItem = await self.GetItemById(self.itemId)

        self.itemId += 1
        return savedItem

    async def UpdateItem(self, id, item):
        sql = f"UPDATE {self.tableName} SET version = ?, name = ?, description = ?, is_complete = ?, message_id = ? WHERE id = ?;"
        self.asyncDbConn.execute(sql, (item["version"], item["name"], item["description"], item["isComplete"], item["messageId"], id))        

        print("Item updated...")                
        updatedItem = await self.GetItemById(id)
        
        return updatedItem

    async def GetItemById(self, id):
        itemExists = await self.ItemExists(id)
        
        if (itemExists == False):
            return None
        
        with self.asyncDbConn.execute(f"SELECT id, version, name, description, is_complete, client_id, message_id FROM {self.tableName} WHERE Id = {id}") as cursor:        
            item = {}

            if cursor:
                for row in cursor:
                    item["id"] = row[0]            
                    item["version"] = row[1]                        
                    item["name"] = row[2]
                    item["description"] = row[3]
                    item["isComplete"] = bool(row[4])
                    item["clientId"] = row[5]
                    item["messageId"] = row[6]                                            

        return item

    async def GetItemCount(self):
        count = 0
        sql = f"SELECT COUNT(*) FROM {self.tableName};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count

    async def ItemExists(self, id):
        count = 0
        sql = f"SELECT COUNT(id) FROM {self.tableName} WHERE id = {id};"
        cur = None

        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count > 0

    async def DeleteItem(self, id):
        sql = f"DELETE FROM {self.tableName} WHERE Id = ?;"            
        self.asyncDbConn.execute(sql, (id))
        
#        await super().DeleteEntity(id)        

    async def DeleteAllItems(self):
        self.asyncDbConn.execute(f"DELETE FROM {self.tableName};")        
        #await super().DeleteAllEntities()
        
    async def GetEntityCount(self):
        count = 0
        print("GetEntityCount from: " + self.tableName)
        print("conn type: " + str(type(self.asyncDbConn)))        
        
        sql = f"SELECT COUNT(*) FROM {self.tableName};"
        
        print("sql: " + sql)                
        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                count = row[0]

        return count

    async def GetLastRowId(self):
        lastId = 0
        sql = "SELECT last_insert_rowid();"
        
        with self.asyncDbConn.execute(sql) as cursor:                
            for row in cursor:        
                lastId = row[0]

        return lastId

    async def DeleteEntity(self, id):
        sql = f"DELETE FROM {self.tableName} WHERE Id = ?;"            
        self.asyncDbConn.execute(sql, (id))

    async def DeleteAllEntities(self):
        self.asyncDbConn.execute(f"DELETE FROM {self.tableName};")
        
    async def GetAllItems(self):
        with self.asyncDbConn.execute(f"SELECT * from {self.tableName}") as cur:
            for row in cur:
                print("item:\r\n", row)
        
