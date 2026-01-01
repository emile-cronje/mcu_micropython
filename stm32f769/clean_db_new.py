import os
import pyb

def dir_exists(path):
    try:
        f = os.listdir(path)
        
        if f != []:
            return True
        else:
            return False
    except OSError:
        return False

def remove_test_database_files(dbName, tableName):
    try:
        if (dir_exists(dbName) == True):
            print('db exists, try to remove...')
       
            print("Removing db:" + dbName)
            for file_name in os.listdir(dbName + '/' + tableName):
                print("Removing file:" + file_name)                    
                os.remove(dbName + '/' + tableName + '/' + file_name)
                
            os.rmdir(dbName + '/' + tableName)
            
            for file_name in os.listdir(dbName):
                print("file exists, try to remove..." + file_name)                        
                os.remove(dbName + '/' + file_name)
            
            os.rmdir(dbName)
            
        print("Removed db:" + dbName)
    except Exception:
        return 'Failed to delete test data.'

os.mount(pyb.SDCard(), "/sd")

dbNames = []
dbNames.append('websrv_db')
dbNames.append('/sd/testdb1')
dbNames.append('/sd/websrv_db')
dbNames.append('/sd/backups')
dbNames.append('/sd/backups_new')
tableName = 'toDoItems'

for dbName in dbNames:
    remove_test_database_files(dbName, tableName)

tableName = 'assets'

for dbName in dbNames:
    remove_test_database_files(dbName, tableName)

print(os.listdir('/sd/'))
#print(os.listdir())    
for file_name in os.listdir('/sd/'):
    print("Removing file:" + '/sd/' + file_name)                    
    os.remove('/sd/' + file_name)
    
print(os.listdir())