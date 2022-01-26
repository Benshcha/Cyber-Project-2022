import socket, threading
from pprint import pprint, pformat
import modules as HTTP
from os.path import join
import os
import json
import traceback

# import global variables
from config import logger

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

def removeUser(username, *args):
    logger.info(f"Removing User: {username}...")
    try:
        cursor.execute(f"DELETE FROM users WHERE username='{username}'")
        mydb.commit()
    except Exception as e:
        logger.warning(f"Could not remove user: {username}:")
        logger.warning(e)
    
    logger.info(f"Successfully Removed {username}")

actions = {"exit": exitFunc, "remove": removeUser, "save": SQL.saveDBToJson}

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
        self.POSTActions = {"/SIGNUP": self.SignUp}
        
    def postResponse(self, packet):
        # logger.debug(f"=================================\n")
        # logger.debug("\n" + pformat([f"{packet.command} {packet.filename}", packet.Headers, packet.Payload]))
        # logger.debug("\n\n=================================")
        
        resp = self.POSTActions[packet.filename](packet.Payload)
        resp = json.dumps(resp)
        respPacket = HTTP.Packet()
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.setPayload(resp)
        self.SendPacket(respPacket)
        logger.debug(f"Sent response packet: {resp}")
    
    def SignUp(self, payload):
        payloadDict = json.loads(payload)
        attemptUsername = payloadDict['username']
        attemptPassword = payloadDict['password']
        
        cursor.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE username='{attemptUsername}')")
        resp = cursor.fetchall()
        
        if resp[0][0] == 1:
            return {"errCode": 1, "description": "Username already exists!"}
        
        
        cursor.execute(f"INSERT INTO users (username, pass) VALUES ('{attemptUsername}', '{attemptPassword}')")
        mydb.commit()
        
        return {"errCode": 0, "discription": "Signed Up successfuly"}
    
    def RequestData(self, packet, *attr, table="", userIDString="id", where=None, **kwargs):
        try:
            cookiesStr = [i.split("=") for i in packet.Headers['Cookie'].split(";")]
            cookies = {cookieStr[0]: cookieStr[1] for cookieStr in cookiesStr}
            user_auth = json.loads(cookies['user_auth'])
            resp = DataQuery(user_auth['username'], user_auth['password'],  *attr, table=table, userIDString=userIDString, where=where, **kwargs)
        except KeyError as e:
            resp = {'code': 1, 'data': "No cookie was sent"}

        return resp
    
    def LoginAttempt(self, packet):
        # TODO: Make use of the "id" request
        resp = self.RequestData(packet, "id", table="users", userIDString="id")
        resp = json.dumps(resp)
        respPacket = HTTP.Packet()
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.setPayload(resp)
        self.SendPacket(respPacket)
        logger.debug(f"Sent login response packet: {resp}")
        
    def PublicResponse(self, file):
        if file == '/':
            file = "index.html"
        filePath = "public/" + file
        fileRespPacket = self.FileResponsePacket(filePath)
        sentBytes = self.SendPacket(fileRespPacket)
        logger.info(f"Sent {filePath} to {self.addr}")


    def getResponse(self, packet):
        try:
            file = packet.filename
            if file == "/LOGIN":
                self.LoginAttempt(packet)
            elif file.startswith("/NotebookList"):
                notebookList = self.RequestData(packet, "id", "ownerID", "title", "description", table="notebooks", userIDString="ownerID")
                
                nbListPacket = HTTP.Packet(json.dumps(notebookList, indent=4))
                
                self.SendPacket(nbListPacket)
            elif file.startswith("/Notebook"):
                notebookID = file[10:]
                
                nbdatadict = self.RequestData(packet, "NotebookPath", "title", table="notebooks", userIDString="ownerID", where=f"id={notebookID}", singleton=True)
                
                if not nbdatadict['code']:
                    filePath = nbdatadict['data']["NotebookPath"]
                    with open(filePath) as FILE:
                        nbdatadict['data']["NotebookData"] = FILE.read()
                    nbdatadict['data'].pop('NotebookPath', None)
                    
                nbdataPacket = HTTP.Packet(nbdatadict)
                self.SendPacket(nbdataPacket)
                logger.info(f'Sent notebook {notebookID} to {self.addr}')
            else: # If file is public
                self.PublicResponse(file)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"404:\n{e}")
                errorPacket = self.FileNotFoundMsgPacket(str(e).split()[-1][1:-1])
                self.SendPacket(errorPacket)
            elif isinstance(e, ConnectionAbortedError):
                logger.debug(f"{self.addr} Aborted Connection")
            else:
                logger.error(e, traceback.format_exc())
        
    def manage(self):
        # Define all actions
        Actions = {"GET": self.getResponse, "POST": self.postResponse}
        
        while True:
            try:
                packetStr = self.socket.recv(2040).decode()
                packet = HTTP.extractDataFromPacket(packetStr)
                command = packet.command
                if command != None:
                    Actions[command](packet)
                else:
                    # print(packetStr)
                    ...
            except Exception as e:
                if isinstance(e, KeyError):
                    logger.error(f"Command {command} not built in to server")
                else:
                    logger.error(e, traceback.format_stack())
                logger.debug("\n" + pformat([packet.filename, packet.Headers, packet.Payload]))
            
        
    def start(self):
        self.thread.start()
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    clientSocket.settimeout(10*60)
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()