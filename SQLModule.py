import mysql.connector as connector
import mysql.connector.pooling as pooling
import json
from typing import Any

from numpy import insert
from config import logger, jsonFiles

class SQLException(Exception):
    def __init__(self, e: Exception, query: str):
        self.message = f"Error from:\n{query}\n{e}"

def SQLFunction(instance, func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, connector.errors.Error):
                raise SQLException(e, instance.cursor.statement)
            else:
                raise e
    return wrapper

class SQLClass:
    """
    ## SQL Method wrapper class
    """
    
    with open('dbconfig.json') as FILE:
        dbconfig = json.load(FILE)

    if dbconfig['autocommit'] == "True":
        dbconfig['autocommit'] = True

    pool = pooling.MySQLConnectionPool(pool_size=2, **dbconfig)

    def __init__(self):
        # init sql connection and read existing data from local values
        self.mydb = SQLClass.pool.get_connection()
        
        self.cursor = self.mydb.cursor()

        for attr in self.__class__.__dict__:
            func = getattr(self, attr)
            if callable(func):
                setattr(self, attr, SQLFunction(self, func))

      
    def initMainSQL(self):
        createusersQuery = """CREATE TABLE IF NOT EXISTS users(id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,username CHAR(30) NOT NULL UNIQUE, pass CHAR(30) NOT NULL);"""
        self.cursor.execute(createusersQuery)
        # self.mydb.commit()
        
        createNotebookQuery = """CREATE TABLE IF NOT EXISTS notebooks (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, ownerID INT NOT NULL, NotebookPath CHAR(255), title CHAR(30) NOT NULL, description TEXT, FOREIGN KEY (ownerID) REFERENCES users(id), currentGroupID INT, code TEXT);
        """
        self.cursor.execute(createNotebookQuery)
        # self.mydb.commit()

        truncateQuery = (
        "SET FOREIGN_KEY_CHECKS = 0",
        "TRUNCATE notebooks",
        "TRUNCATE users",
        "SET FOREIGN_KEY_CHECKS = 1"
        )
        for q in truncateQuery:
            self.cursor.execute(q)
        # self.mydb.commit()
        
        for k, data in jsonFiles.items():
            if "without" in data:
                without = data["without"]
            else:
                without = None
            self.loadTableFromJson(k, data['path'], without)

    
    def loadTableFromJson(self, table, filename, without: str | None =None):
        logger.info(f"Uploading {table} to database...")
        with open(filename) as FILE:
            jsonData = json.load(FILE)
            
        if len(jsonData) == 0:
            return 1
        try:
            if without is None:
                cmd = f"INSERT INTO {table} VALUES "
            else:
                getColumnsQuery = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' ORDER BY ORDINAL_POSITION"
                self.cursor.execute(getColumnsQuery)
                columns = self.cursor.fetchall()
                columns = [c[0] for c in columns]

                if without in columns:
                    columns.remove(without) 
                    for nb in jsonData:
                        nb.pop(without)

                cmd = f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
            for row in jsonData:
                cmd += str(tuple(row.values())) + ", "
            cmd = cmd[: -2]
            self.cursor.execute(cmd)
            # self.mydb.commit()
        except connector.ProgrammingError as e:
            logger.error()
            raise SQLException(f"Failed to load {table}:\n{e}", self.cursor.statement)
        else:
            logger.info(f"Successfully uploaded {table} to database!")
            return 0

    
    def saveDBToJson(self):
        for table, data in jsonFiles.items():  
            filename = data['path']  
            logger.info(f"Saving {table} to {filename}...")
            self.cursor.execute(f"SELECT * FROM {table}")
            data=self.cursor.fetchall()
            fieldNames = [i[0] for i in self.cursor.description]
            
            datadict = [{name: val for name, val in zip(fieldNames, obj)} for obj in data]
            
            with open(filename, "w") as UsersFILE:
                json.dump(datadict, UsersFILE, indent=4)
            logger.info(f"Table: {table} saved to {filename}!")

    
    def CheckAuth(self, Username: str, Password: str):
        try:
            condition = "username='%s' AND pass='%s'" % (Username, Password)
            attemptRes = self.Request('id', table='users', where=condition, singleton=True)
            return attemptRes['id'] if attemptRes is not None else None
        except connector.ProgrammingError as e:
            raise SQLException(e, self.cursor.statement)

    
    def Request(self, *attr, table: str, where: str = "", singleton: bool=False) -> list[dict[str: str] | dict[str: Any]]:
        """
        ### Send a query request (SELECT) to the database.

        Args:
            table (str): the table for the request
            where (str, optional): the where command. Defaults to "".
            singleton (bool, optional): whether to return a singleton or not. Defaults to False.
        Returns:
            (list): the result of the request
        """
        dataReq = ', '.join(attr)
        whereCMD = "WHERE %s" % where if where != "" else ""
        dataQuery = "SELECT %s FROM %s %s" % (dataReq, table, whereCMD)
        self.cursor.execute(dataQuery)
        vals = self.cursor.fetchall()
        cols = self.cursor.description

        data = []
        for val in vals:
            data.append({col[0]: val[i] for i, col in enumerate(cols)})

        # TODO: fix singleton reciving empty list
        if singleton:
            if len(data) == 0:
                return None
            data = data[0]
        return data

    
    def DataQuery(self, Username: str, Password: str, *attr: tuple[str], table:str ="", userIDString: str="id", where=None, **kwargs) -> dict[int, Any]:
        """
        ## Request data from database using the client's username and password for authentication

        ### Args:
            Username (str): user's username for authentication
            Password (str): user's password for authentication
            *args (tuple[str]): the requested data.
            table (str, optional): the name of the table containing the data. Defaults to "".
            UserIDString (str, optional): the name of the user id as stated in the referenced table
            where (str): WHERE command

        ### Raises:
            Exception: If no attributes were given but the table was

        ### Returns:
            dict[int, Any]: dictionary conatining the error code and the data requested
        """
        UserID = self.CheckAuth(Username, Password)
        
        if UserID == None:
            return {'code': 1, 'data': 'Authentication denied!'}
        
        additionalCMD = ""
        if where != None:
            additionalCMD = f"AND ({where})"
        
        dataRes = []
        if table != "":
            if len(attr) == 0:
                raise Exception("No attributes were given but table was")

            whereCommand = "%s=%s %s" % (userIDString, UserID, additionalCMD)

            singleton = False
            if 'singleton' in kwargs and kwargs['singleton']:
                singleton = True
            dataRes = self.Request(*attr, table=table, where=whereCommand, singleton=singleton)
            
            if dataRes is None or len(dataRes) == 0:
                return {'code': 1, 'data': 'No such notebook in your list!'}
                
            ans = {'code': 0, 'data': dataRes}
            if 'returnUserID' in kwargs and kwargs['returnUserID']:
                ans['UserID'] = UserID
        return ans

    @staticmethod
    def exitHandler():
        sql = SQLClass()
        sql.saveDBToJson()
        logger.info(f"Goodbye :)")

    
    def Insert(self, table:str, **datadict):  
        if len(datadict) != 0:
            try:
                keys = ', '.join(datadict.keys())
                vals = tuple(datadict.values())
                insertQuery = "INSERT INTO %s (%s) VALUES %s" % (table, keys, vals)
                
                self.cursor.execute(insertQuery)
                # self.mydb.commit()
                
                idQuery = 'SELECT LAST_INSERT_ID()'
                self.cursor.execute(idQuery)
                
                id = self.cursor.fetchall()
                logger.debug(f"Inserted into {table} values {datadict}")
                return {'code': 0, 'inserted_id': id[0][0]}
                
            except Exception as e:
                logger.error(e, exc_info=True)
                return {'code': 1, 'data': e}
            
        return {'code': 1, 'data': ""}

    
    def Update(self, table: str, where: str, **datadict):
        if len(datadict) != 0:
            try:
                items = [(str(k), '\'' + str(v) + '\'') for k, v in datadict.items()]
                itemsList = ', '.join('='.join(item) for item in items)
                updateQuery = "UPDATE %s SET %s WHERE %s" % (table, itemsList, where)
                self.cursor.execute(updateQuery)
                # self.mydb.commit()
                logger.info(f"Updated {table} where {where} by {datadict}")
                
                return {'code': 0}
            except Exception as e:
                return {'code': 1, 'data': e}

          
    def Remove(self, table, id):
        logger.info(f"Removing {id} from {table}...")
        try:
            self.cursor.execute("DELETE FROM %s WHERE id='%s'") % (table, id)
            # self.mydb.commit()
        except Exception as e:
            logger.warning(f"Could not remove {id} from {table}")
            logger.warning(e)
        
        logger.info(f"Successfully Removed {id} from {table}")