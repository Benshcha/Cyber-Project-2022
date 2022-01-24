import socket, threading
from pprint import pprint, pformat
import modules as HTML
from os.path import join
import os
import json
import traceback

# import global variables
from config import logger

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

logger.info(f"[INIT] Server running on {local_ip, hostname = }")

# Load SQL
import SQLModule as SQL
usersFile = "Protected/UsersLoginData.json"
SQL.__init__(usersFile)
from SQLModule import cursor, mydb

# TODO (optional) make it that if closed by hand it will save
def exitFunc(*args):
    SQL.exitHandler(usersFile)
    os._exit(1)

def removeUser(username, *args):
    logger.info(f"Removing User: {username}...")
    try:
        cursor.execute(f"DELETE FROM users WHERE username='{username}'")
        mydb.commit()
    except Exception as e:
        logger.warning(f"Could not remove user: {username}:")
        logger.warning(e)
    
    logger.info(f"Successfully Removed {username}")

actions = {"exit": exitFunc, "remove": removeUser}

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

class client(HTML.GeneralClient):
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
        respPacket = HTML.Packet()
        respPacket.Headers['Content-Length'] = len(resp)
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.Payload = resp
        self.SendPacket(respPacket)
        logger.debug(f"Sent response packet: {resp}")
    
    def SignUp(self, payload):
        payloadDict = json.loads(payload)
        attemptUsername = payloadDict['username']
        attemptPassword = payloadDict['password']
        
        cursor.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE username='{attemptUsername}')")
        resp = cursor.fetchall()
        
        if resp[0][0] == "1":
            return {"errCode": 1, "discription": "Username already exists!"}
        
        
        cursor.execute(f"INSERT INTO users (username, pass) VALUES ('{attemptUsername}', '{attemptPassword}')")
        mydb.commit()
        
        return {"errCode": 0, "discription": "Signed Up successfuly"}
    
    def RequestData(self, Username, Password, table="", *attr):
        condition = f"username='{Username}' AND pass='{Password}'"
        checkQuery = f"SELECT id FROM users WHERE {condition}"
        cursor.execute(checkQuery)
        attemptRes = cursor.fetchall()
        
        if attemptRes == []:
            return {'code': 1}
        else:
            id = attemptRes[0][0]
        
        if table != "":
            if len(attr) == 0:
                raise Exception("No attributes were given but table was")
            dataQuery = f"SELECT {', '.join(attr)} FROM {table} WHERE id={id}"
            cursor.execute(dataQuery)
        
        dataRes = cursor.fetchall()
        return {'code': 0, 'data': dataRes}
    
    def LoginAttempt(self, packet):
        resp = self.RequestData(packet.attr["username"], packet.attr["password"], 'users', 'id')
        resp = json.dumps(resp)
        respPacket = HTML.Packet()
        respPacket.Headers['Content-Length'] = len(resp)
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.Payload = resp
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
                packet = HTML.extractDataFromPacket(packetStr)
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
                    logger.error(e, traceback.format_exc())
                logger.debug(f"\n=================================\n\n")
                logger.debug("\n" + pformat([packet.filename, packet.Headers, packet.Payload]))
                logger.debug("\n\n=================================")
            
        
    def start(self):
        self.thread.start()
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    clientSocket.settimeout(10*60)
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()