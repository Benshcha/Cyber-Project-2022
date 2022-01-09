import socket, threading
from pprint import pprint, pformat
from modules import myLogger
import modules as HTML
from os.path import join
import json
import traceback

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
logger = myLogger("mainLogger")

logger.info(f"[INIT] Server running on {local_ip, hostname = }")
class client(HTML.GeneralClient):
    def __init__(self, clientSocket, addr):
        super().__init__(clientSocket, addr)
        self.thread = threading.Thread(target=self.manage)
        self.POSTActions = {"/LOGIN": self.LoginAttempt, "/SIGNUP": self.SignUp}
        
    def postResponse(self, packet):
        # logger.debug(f"=================================\n")
        # logger.debug("\n" + pformat([f"{packet.command} {packet.filename}", packet.Headers, packet.Payload]))
        # logger.debug("\n\n=================================")
        
        resp = self.POSTActions[packet.filename](packet.Payload)
        resp = json.dumps([resp])
        respPacket = HTML.Packet()
        respPacket.Headers['Content-Length'] = len(resp)
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.Payload = resp
        self.SendPacket(respPacket)
        logger.debug(f"Sent login response packet: {resp}")
    
    def SignUp(self, payload):
        payloadDict = json.loads(payload)
        Username = payloadDict['Username']
        Password = payloadDict['Password']
        logger.debug(f"{Username, Password = }")
    
    
    def LoginAttempt(self, loginData):
        payloadDict = json.loads(loginData)
        Username = payloadDict['username']
        Password = payloadDict['password']
        
        with open("Protected/UsersLoginData.json", "r") as FILE:
            UsersData = json.load(FILE)
        
        resp = 1
        for key in UsersData:
            if key == Username and UsersData[key] == Password:
                resp = 0
                self.username = Username
                self.isLoggedIn = True
        
        return resp
        
    def PublicResponse(self, file):
        if file == '/':
            file = "index.html"
        filePath = "public/" + file
        fileRespPacket = self.FileResponsePacket(filePath)
        sentBytes = self.SendPacket(fileRespPacket)
        logger.info(f"Sent {filePath} to {self.addr}")

    def PrivateResponse(self, packet):
        ...

    def getResponse(self, packet):
        try:
            file = packet.filename
            if file.startswith("/Protected"):
                self.PrivateResponse(packet)
            else: # If file is public
                self.PublicResponse(file)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"404:\n{e}")
                errorPacket = self.FileNotFoundMsgPacket(str(e).split()[-1][1:-1])
                self.SendPacket(errorPacket)
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