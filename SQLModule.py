import mysql.connector as connector
import json

from config import logger, jsonFiles

def __init__():
    logger.info("Initializing Database...")
    global cursor, mydb

    # init sql connection and read existing data from local values
    mydb = connector.connect(
        host="localhost",
        username="Benshcha",
        password="XunxuoTable70705",
        database="CyberProject2022"
    )
    
    cursor = mydb.cursor()
    
def initMainSQL():
    __init__()
    createusersQuery = """CREATE TABLE IF NOT EXISTS users(id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,username CHAR(30) NOT NULL UNIQUE, pass CHAR(30) NOT NULL);"""
    cursor.execute(createusersQuery)
    mydb.commit()
    
    createNotebookQuery = """CREATE TABLE IF NOT EXISTS notebooks (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,ownerID INT NOT NULL, NotebookPath CHAR UNIQUE NOT NULL, title CHAR(30) NOT NULL, discription TEXT, FOREIGN KEY (ownerID) REFERENCES users(id));
    """
    cursor.execute(createNotebookQuery)
    mydb.commit()
    
    truncateQuery = (
    "SET FOREIGN_KEY_CHECKS = 0",
    "TRUNCATE notebooks",
    "TRUNCATE users",
    "SET FOREIGN_KEY_CHECKS = 1"
    )
    for q in truncateQuery:
        cursor.execute(q)
    mydb.commit()
    
    for k, path in jsonFiles.items():
        loadTableFromJson(k, path)

def loadTableFromJson(table, filename):
    logger.info(f"Uploading {table} to database...")
    with open(filename) as FILE:
        jsonData = json.load(FILE)
        
    if len(jsonData) == 0:
        return 1
    try:
        cmd = f"INSERT INTO {table} VALUES "
        for row in jsonData:
            cmd += str(tuple(row.values())) + ", "
        cmd = cmd[: -2]
        cursor.execute(cmd)
        mydb.commit()
    except Exception as e:
        logger.error(f"Failed to load {table}:\n{e}")
        raise e
    else:
        logger.info(f"Successfully uploaded {table} to database!")
        return 0

def saveDBToJson():
    for table, filename in jsonFiles.items():    
        logger.info(f"Saving {table} to {filename}...")
        cursor.execute(f"SELECT * FROM {table}")
        data=cursor.fetchall()
        fieldNames = [i[0] for i in cursor.description]
        
        datadict = [{name: val for name, val in zip(fieldNames, obj)} for obj in data]
        
        with open(filename, "w") as UsersFILE:
            json.dump(datadict, UsersFILE, indent=4)
        logger.info(f"Table: {table} saved to {filename}!")
    
    
def exitHandler():
    __init__()
    saveDBToJson()
    logger.info(f"Goodbye :)")

