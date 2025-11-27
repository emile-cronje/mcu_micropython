import sqlite
import os
import gc

DB_FILE = "data.db"
DB_FILE = ":memory:"
clearDb = True

if clearDb:
    if DB_FILE in os.listdir("."):
        os.remove(DB_FILE)

def log_mem(label):
    return
    print(f"[mem] {label}: {gc.mem_free()}")

print("Creating connection...")
conn = sqlite.connect(DB_FILE)
log_mem("mem_free after connect: ")

entityCount = 100
itemCount = entityCount
assetCount = entityCount

doInsert = True
doUpdate = True

if clearDb:
    conn.execute("DROP TABLE IF EXISTS assets")
    conn.execute("DROP TABLE IF EXISTS items")

    conn.execute('''CREATE TABLE IF NOT EXISTS assets
            (ID            INTEGER,
            VERSION        INTEGER NOT NULL,
            CODE           TEXT    NOT NULL,
            DESCRIPTION    TEXT    NOT NULL,         
            IS_MSI         BOOL     NOT NULL);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS items
                    (ID            INTEGER,
                    VERSION        INTEGER NOT NULL,
                    NAME           TEXT    NOT NULL,
                    DESCRIPTION    TEXT    NOT NULL,         
                    IS_COMPLETE    BOOL     NOT NULL);''')

    conn.execute('''CREATE UNIQUE INDEX index_item_name ON items(name, description)''')
    conn.execute('''CREATE UNIQUE INDEX index_asset_code ON assets(code, description)''')
    print("tables created...")    

    log_mem("mem_free after tables created: ")

# items
totalCount = 0

if (doInsert == True) & (itemCount > 0):
    sql = "INSERT INTO items VALUES (?, 0, ?, ?, False);"    
    
    for itemId in range(itemCount):
        conn.execute(sql, (itemId, 'ITEM_Name_' + str(itemId), 'ITEM_Desc_' + str(itemId)))        
        totalCount += 1    
        print("item count: ", totalCount)    

    log_mem("mem_free after items inserted: ")

if (doUpdate == True):
    itemIds = []

    print("get item record...")
    
    with conn.execute("SELECT id FROM items") as cur:
        for row in cur:
            itemIds.append(row[0])
            print(row[0])        

    sql = "UPDATE items SET name = ?, description = ? WHERE id = ?;"    

    for itemId in itemIds:
        conn.execute(sql, ('ITEM_Name_Updated_' + str(itemId), 'ITEM_Desc_Updated_' + str(itemId), itemId))        
        print("updated item id: ", itemId)                

    log_mem("mem_free after items updated: ")

totalCount = 0

if (doInsert == True) & (assetCount > 0):
    # assets
    sql = "INSERT INTO assets VALUES (?, 0, ?, ?, False);"    

    for assetId in range(assetCount):
        conn.execute(sql, (assetId, 'ASSET_Name_' + str(assetId), 'ASSET_Desc_' + str(assetId)))                
        totalCount += 1        
        print("asset count: ", totalCount)        

    log_mem("mem_free after assets inserted: ")

print("Update assets..." + str(doUpdate))

if (doUpdate == True) & (assetCount > 0):
    print("Update assets...")
    assetIds = []

    with conn.execute("SELECT id FROM assets") as cur:
        for row in cur:
            assetIds.append(row[0])
            print(row[0])        

    sql = "UPDATE assets SET code = ?, description = ? WHERE id = ?;"    

    for assetId in assetIds:
        conn.execute(sql, ('ASSET_Code_Updated_' + str(assetId), 'ASSET_Desc_Updated_' + str(assetId), assetId))        
        print("updated asset id: ", assetId)                    

    log_mem("mem_free after assets updated: ")

dbItemCount = 0
dbAssetCount = 0

if (itemCount > 0):
    with conn.execute("SELECT * from items") as cur:
        for row in cur:
            print("item:", row)
    
    with conn.execute("SELECT COUNT(*) from items") as cur:
        for row in cur:
            dbItemCount = row[0]
            print("items count:", dbItemCount)

if (assetCount > 0):
    with conn.execute("SELECT * from assets") as cur:
        for row in cur:
            print("asset:", row)

    with conn.execute("SELECT COUNT(*) from assets") as cur:
        for row in cur:
            dbAssetCount = row[0]                        
            print("assets count:", dbAssetCount)

if (dbItemCount != itemCount):
    print("Item count error...")
else:    
    print("Item count OK...")    

if (dbAssetCount != assetCount):
    print("Asset count error...")
else:    
    print("Asset count OK...")    

print(f"Connection object: {conn}")
# At this point, is conn valid? Is DB_FILE created and a valid empty SQLite DB?
# (A new SQLite DB is not 0 bytes)
print("Closing connection...")
conn.close()
print("Connection closed.")
log_mem("mem_free after gc collect: ")
print("All OK")
# Add gc.collect() here and print memory    