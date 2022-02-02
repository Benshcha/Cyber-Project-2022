import socket, threading
from pprint import pprint, pformat
import modules as HTTP
from os.path import join
import os
import json
import traceback

# import global variables
from config import logger, silentLog

# Load SQL
import SQLModule as SQL
SQL.initMainSQL()
from SQLModule import cursor, mydb, DataQuery

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

logger.info(f"[INIT] Server running on {local_ip, hostname = }")


def exitFunc(*args):
    SQL.exitHandler()
    os._exit(0)

def removeUser(username):
    SQL.Remove('users', username)

def removeNotebook(notebookID):
    SQL.Remove('notebooks', notebookID)

def Remove(*args):
    if len(args) == 0:
        logger.warning("Did not recieve arguments!")
    elif len(args) == 1:
        removeUser(args[0])
    elif args[0] == "ID":
        removeNotebook(args[1])
    else:
        logger.warning("No such command: ")

def toggleSilentHeaderLog():
    global silentLog
    silentLog = not silentLog

actions = {"exit": exitFunc, "remove": Remove, "save": SQL.saveDBToJson, "silent": toggleSilentHeaderLog}

# Start console:
def console():
    while True:
        try:
            cmdtxt = input()
        except EOFError as e:
            exitFunc()
            
        cmd, *args = cmdtxt.split()
        logger.info(f"Executing Server Command: {cmd}")
        try:
            actions[cmd](*args)
        except KeyError as e:
            logger.warning(f"No Such Command: {cmd}")
    
consoleThread = threading.Thread(target=console)
consoleThread.start()

class client(HTTP.GeneralClient):
    def __init__(self, clientSocket, addr):
        super().__init__(clientSocket, addr)
        self.thread = threading.Thread(target=self.manage)
    
    def getUserAuth(self, packet):
        cookiesStr = [i.split("=") for i in packet.Headers['Cookie'].split(";")]
        cookies = {cookieStr[0]: cookieStr[1] for cookieStr in cookiesStr}
        return tuple(json.loads(cookies['user_auth']).values())
    
    def postResponse(self, packet: HTTP.Packet):
        file = packet.filename
        resp = None
        if file == "/SIGNUP":
            resp = self.SignUp(packet.Payload)
        elif file.startswith('/SAVENEWNB'):
            resp = self.NewNotebook(packet)
        elif file.startswith('/SAVE/'):
            resp = self.SaveNotebook(packet)
        else:
            # TODO Add error response
            ...
        
        resp = json.dumps(resp)
        respPacket = HTTP.Packet()
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.setPayload(resp)
        self.SendPacket(respPacket)
        logger.debug(f"Sent response packet: {resp}") 

    def SaveNotebook(self, packet: HTTP.Packet):
        
        notebookID = packet.filename[6:]
        
        user_auth = self.getUserAuth(packet)
        resp = SQL.DataQuery(*user_auth, "id", 'NotebookPath', table="notebooks", userIDString='ownerID', where=f"id={notebookID}", singleton=True, returnUserID=True)
        
        id = resp['UserID']
        logger.info(f"User {id} is saving notebook {notebookID}...")
        
        if resp['code'] == 1:
            errMsg = f"User {id} doesn't own notebook {notebookID}"
            logger.error(errMsg)
            return {'code': 1, 'data': errMsg}
        elif resp['code'] == 0:
            with open(resp['data']['NotebookPath'], 'a') as FILE:
                FILE.write(packet.Payload)
                
            logger.info(f"Succesfully saved user {id}'s notebook {notebookID}")
        return resp
    
    def NewNotebook(self, packet: HTTP.Packet):
        user_auth = self.getUserAuth(packet)
        id = SQL.CheckAuth(*user_auth)
        
        if id != None:
            payloadDict = json.loads(packet.Payload)
            svgData = payloadDict['svgData']
            payloadDict.pop('svgData', None)
            payloadDict['ownerID'] = id
            
            try:
                insertResp = SQL.Insert('notebooks', **payloadDict)
                
                if insertResp['code'] != 0:
                    return insertResp
                
            except KeyError as e:
                logger.error("User request doesn't have enough data:")
                logger.error(e)
                return {'code': 1, 'data': f'Missing key: {e}'}
                
            notebookID = insertResp['inserted_id']
            
            # Create svg file:
            newPath = f'Protected/Notebooks/{notebookID}.svg'
            with open(newPath, 'w') as FILE:
                FILE.write(svgData)
            
            # Update file path to DB
            updateResp = SQL.Update(table="notebooks", where=f'id={notebookID}', NotebookPath=newPath)

            if updateResp['code'] == 0:
                return SQL.DataQuery(*user_auth, "id", table="notebooks", userIDString="ownerID", singleton=True)
            else:
                return updateResp
        else:
            return {'code': 1, 'data': 'Authorization denied!'}
    
    def SignUp(self, payload: str):
        payloadDict = json.loads(payload)
        attemptUsername = payloadDict['username']
        attemptPassword = payloadDict['password']
        
        cursor.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE username='{attemptUsername}')")
        resp = cursor.fetchall()
        
        if resp[0][0] == 1:
            return {"code": 1, "description": "Username already exists!"}
        
        
        cursor.execute(f"INSERT INTO users (username, pass) VALUES ('{attemptUsername}', '{attemptPassword}')")
        mydb.commit()
        
        return {"code": 0, "description": "Signed Up successfuly"}
    
    def RequestData(self, packet: HTTP.Packet, *attr: tuple[str], table="", userIDString="id", where=None, **kwargs):
        try:
            user_auth = self.getUserAuth(packet)
            resp = DataQuery(*user_auth,  *attr, table=table, userIDString=userIDString, where=where, **kwargs)
        except KeyError as e:
            resp = {'code': 1, 'data': "No cookie was sent"}

        return resp
    
    def LoginAttempt(self, packet, includePayload=True):
        # TODO: Make use of the "id" request
        resp = self.RequestData(packet, "id", table="users", userIDString="id")
        resp = json.dumps(resp)
        respPacket = HTTP.Packet()
        respPacket.Headers['Content-Type'] = "text/json"
        
        if includePayload:
            respPacket.setPayload(resp)
        else:
            respPacket.Headers['Content-Length'] = len(resp)
            
        self.SendPacket(respPacket)
        logger.debug(f"Sent login response packet: {resp}")
        
    def PublicResponse(self, file, includePayload=True):
        if file == '/':
            file = "index.html"
        filePath = "public/" + file
        fileRespPacket = self.FileResponsePacket(filePath, includePayload=includePayload)
        sentBytes = self.SendPacket(fileRespPacket)
        
        msg = f"Sent {filePath} to {self.addr}"
        
        if not includePayload:
            if silentLog:
                return
            else:
                msg += " without payload"
        logger.info(msg)

    def SendNotebookList(self, packet, includePayload=True):
        notebookList = self.RequestData(packet, "id", "ownerID", "title", "description", table="notebooks", userIDString="ownerID")
                
        nbListPacket = HTTP.Packet(json.dumps(notebookList, indent=4), includePayload=includePayload)
        
        self.SendPacket(nbListPacket)
    
    def SendNotebook(self, packet, includePayload=True):
        notebookID = packet.filename[10:]
                
        nbdatadict = self.RequestData(packet, "NotebookPath", "title", table="notebooks", userIDString="ownerID", where=f"id={notebookID}", singleton=True)
        
        if not nbdatadict['code']:
            filePath = nbdatadict['data']["NotebookPath"]
            with open(filePath) as FILE:
                nbdatadict['data']["NotebookData"] = FILE.read()
            nbdatadict['data'].pop('NotebookPath', None)
            
        nbdataPacket = HTTP.Packet(nbdatadict, includePayload=includePayload)
        self.SendPacket(nbdataPacket)
        logger.info(f'Sent notebook {notebookID} to {self.addr}')
    
    def getResponseManage(self, packet, includePayload=True):
        try:
            file = packet.filename
            if file == "/LOGIN":
                self.LoginAttempt(packet, includePayload=includePayload)
            elif file.startswith("/NotebookList"):
                self.SendNotebookList(packet, includePayload=includePayload)
            elif file.startswith("/Notebook"):
                self.SendNotebook(packet, includePayload=includePayload)
            else: # If file is public
                self.PublicResponse(file, includePayload=includePayload)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"404:\n{e}")
                errorPacket = self.FileNotFoundMsgPacket(str(e).split()[-1][1:-1])
                self.SendPacket(errorPacket)
            elif isinstance(e, ConnectionAbortedError):
                logger.debug(f"{self.addr} Aborted Connection")
            else:
                logger.error(e, traceback.format_exc())  
    
    def getResponse(self, packet):
        self.getResponseManage(packet)
        
    def headResponse(self, packet):
        self.getResponseManage(packet, includePayload=False)
    
    def RecieveHTTPPacket(self):
        packetStr = self.Recieve().decode()
        packet = HTTP.extractDataFromPacket(packetStr)
        if packet.command == "POST":
            while len(packet.Payload) < int(packet.Headers['Content-Length']):
                # Since the length is already set there is no need to use .setPayload
                packet.Payload += self.Recieve().decode()
            
        return packet
    
    def manage(self):
        # Define all actions
        Actions = {"GET": self.getResponse, "POST": self.postResponse, "HEAD": self.headResponse}
        
        while True:
            try:
                packet = self.RecieveHTTPPacket()
                command = packet.command
                if command != None:
                    Actions[command](packet)
                    if packet.getHeader('Connection') != 'keep-alive':
                        self.socket.close()
                else:
                    # print(packetStr)
                    ...
            except Exception as e:
                if isinstance(e, KeyError):
                    logger.error(f"Command {command} not built in to server")
                else:
                    # logger.error(e, traceback.format_stack())
                    logger.error(e)
                # logger.debug("\n" + pformat([packet.filename, packet.Headers, packet.Payload]))
            
        
    def start(self):
        self.thread.start()
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    clientSocket.settimeout(10*60)
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()