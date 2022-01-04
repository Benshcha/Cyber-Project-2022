import socket, threading
from pprint import pprint, pformat
from modules import myLogger
import modules as HTML
from os.path import join
import json

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
logger = myLogger("mainLogger")

logger.info(f"[INIT] Server running on {local_ip, hostname = }")

class client(socket.socket):
    def __init__(self, clientSocket, addr):
        self.socket = clientSocket
        self.addr = addr
        self.thread = threading.Thread(target=self.manage)

    def postResponse(self, packet):
        logger.debug(f"=================================\n")
        logger.debug("\n" + pformat([f"{packet.command} {packet.filename}", packet.Headers, packet.Payload]))
        logger.debug("\n\n=================================")

    def getResponse(self, packet):
        try:
            file = packet.filename
            if file == '/':
                file = "index.html"
            filePath = "public/" + file
            self.socket.send(HTML.FileResponse(filePath))
            logger.info(f"Sent {filePath} to {self.addr}")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"404:\n{e}")
                self.socket.send(HTML.FileNotFoundMsg(str(e).split()[-1][1:-1]))
            else:
                logger.error(e)
        
    def manage(self):
        # Define all actions
        actions = {"GET": self.getResponse, "POST": self.postResponse}
        
        while True:
            try:
                packetStr = self.socket.recv(2040).decode()
                packet = HTML.extractDataFromPacket(packetStr)
                command = packet.command
                if command:
                    actions[command](packet)
            except Exception as e:
                if isinstance(e, KeyError):
                    logger.error(f"Command {command} not built in to server")
                else:
                    logger.error(e)
                logger.debug(f"\n=================================\n\n")
                logger.debug("\n" + pformat([packet.filename, packet.Headers, packet.Payload]))
                logger.debug("\n\n=================================")
            
        
    def start(self):
        self.thread.start()
        
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()