import sqlite

class EntityDaoSqlite:
    def __init__(self, dbName):
        print("EntityDaoSqlite init..." + dbName)        
        self.asyncDbConn = sqlite.connect(dbName)
        self.tableName = None

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

    async def DeleteEntity(self, id):
        sql = f"DELETE FROM {self.tableName} WHERE Id = ?;"            
        self.asyncDbConn.execute(sql, (id))

    async def DeleteAllEntities(self):
        self.asyncDbConn.execute(f"DELETE FROM {self.tableName};")
        
