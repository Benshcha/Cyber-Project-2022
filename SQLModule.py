import mysql.connector as connector
import json

from config import logger

def __init__(usersfile, nbfile=""):
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
    cursor.execute("TRUNCATE `users`")
    mydb.commit()
    
    with open(usersfile) as UsersFILE:
        usersData = json.load(UsersFILE)
    
    logger.info("Uploading users to database...")
    try:
        cmd = "INSERT INTO users VALUES "
        for user in usersData:
            try:
                id = user['id']
                username = user['username']
                password = user['pass']
            except KeyError as e:
                logger.error(f"Invalid File!:\n{e}")
            cmd += f"({id}, '{username}', '{password}'), "
        cmd = cmd[:-2]
        cursor.execute(cmd)
        mydb.commit()
    except Exception as e:
        logger.error(f"Failed to load users:\n{e}")
        raise e
    
    logger.info("Successfully uploaded users to database!")

def exitHandler(usersfile):
    logger.info(f"Saving Database to {usersfile}...")
    cursor.execute("SELECT * FROM users")
    data=cursor.fetchall()
    datadict = [{"id": id, "username": username, "pass": password} for id, username, password in data]
    
    with open(usersfile, "w") as UsersFILE:
        json.dump(datadict, UsersFILE, indent=4)
    logger.info(f"Database saved to {usersfile}!")
    logger.info(f"Goodbye")
