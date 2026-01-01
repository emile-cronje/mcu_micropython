class EntityDaoSqlite:
    def __init__(self, asyncDbConn):
        self.asyncDbConn = asyncDbConn
        self.tableName = None

    async def GetEntityCount(self):
        count = 0        
        with self.asyncDbConn.execute(f"SELECT COUNT(*) FROM {self.tableName}") as cursor:                
            for row in cursor:        
                count = row[0]

        return count

    async def DeleteEntity(self, id):
        self.asyncDbConn.executemany(
            "BEGIN TRANSACTION;"
            f"DELETE FROM {self.tableName} WHERE Id = {id};" +
            "COMMIT;")        

    async def DeleteAllEntities(self):
        self.asyncDbConn.executemany(
            "BEGIN TRANSACTION;"
            f"DELETE FROM {self.tableName};" +
            "COMMIT;")        
        
