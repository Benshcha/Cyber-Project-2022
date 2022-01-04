import socket, threading
from pprint import pprint
import modules as HTML
from os.path import join
import json

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"[INIT] Server running on {local_ip, hostname = }")

# Define all actions:

class client(socket.socket):
    def __init__(self, clientSocket, addr):
        self.socket = clientSocket
        self.addr = addr
        self.thread = threading.Thread(target=self.manage)

    def postResponse(self, msg, file):
        print(f"=================================", end='\n\n')
        pprint([file, msg])
        print("\n\n=================================")

    def getResponse(self, msg, file):
        try:
            if file == '/':
                file = "index.html"
            filePath = "public/" + file
            self.socket.send(HTML.FileResponse(filePath))
            print(f"Sent {filePath} to {self.addr}")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                print(f"404:\n{e}")
                self.socket.send(HTML.FileNotFoundMsg(str(e).split()[-1][1:-1]))
            else:
                print(e)
        
    def manage(self):
        actions = {"GET": self.getResponse, "POST": self.postResponse}
        
        while True:
            try:
                msgHeaderPayloadList = self.socket.recv(2040).decode().split("\r\n\r\n")
                msgHeaderString = msgHeaderPayloadList[0].split("\r\n")
                
                if len(msgHeaderPayloadList) > 1:
                    msgPayload = msgHeaderPayloadList[1].split("\r\n")
                
                commandLine = msgHeaderString[0]
                
                HeaderNamesAndAttr = [Header.split(": ") for Header in msgHeaderString[1:]]
                msgHeader = {h[0]: h[1] for h in HeaderNamesAndAttr[1:]}
                
                resp =  commandLine.split()
                if len(resp) >= 1:
                    command = resp[0]
                    if len(resp) >= 2:
                        file = resp[1]
                        ow = resp[2]
                        
                msg = [msgHeader, msgPayload]
                actions[command](msg, file)
            except Exception as e:
                if isinstance(e, KeyError):
                    print(f"Command {command} not built in to server")
                else:
                    print(e)
                print(f"=================================", end='\n\n')
                pprint([file, msg])
                print("\n\n=================================")
            
        
    def start(self):
        self.thread.start()
        
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()