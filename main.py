import socket, threading
from pprint import pprint
import modules as HTML

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ADDR = ('', 80)
serverSocket.bind(ADDR)
serverSocket.listen()
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"[INIT] Server running on {local_ip, hostname = }")

class client(socket.socket):
    def __init__(self, clientSocket, addr):
        self.socket = clientSocket
        self.addr = addr
        self.thread = threading.Thread(target=self.manage)

    
    def manage(self):
        while True:
            try:
                msg = self.socket.recv(2040).decode().split("\r\n")
                if msg[0].startswith('GET'):
                    FirstLine = msg[0].split()
                    if FirstLine[1] == '/':
                        self.socket.send(HTML.FileResponse("public/index.html"))
                        print(f"Sent html file to {self.addr}")
                    else:
                        filePath = FirstLine[1][1:]
                        self.socket.send(HTML.FileResponse(filePath))
                        print(f"Sent {filePath} to {self.addr}")
                # pprint(msg)
            except Exception as e:
                if isinstance(e, FileNotFoundError):
                    print(f"404:\n{e}")
                    self.socket.send(HTML.FileNotFoundMsg(str(e).split()[-1][1:-1]))
                else:
                    print(e)
        
    def start(self):
        self.thread.start()
        
        
clients = []
while True:
    clientSocket, addr = serverSocket.accept()
    myClient = client(clientSocket, addr)
    clients.append(myClient)
    myClient.start()