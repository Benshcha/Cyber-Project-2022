from Ex5 import *
import socket, threading, os
import numpy as np

def manageFileRequest(ClientSocket, filename, key):
    if not os.path.exists(filename):
        ClientSocket.send(EncryptCTR('1'.encode(), key))
        return
    
    with open(filename, 'rb') as file:
        data = file.read()
    
    encData = EncryptCTR(data, key)
    ClientSocket.send(encData)


def manageClient(ClientSocket, clientAddress):
    print('Client connected: ', clientAddress)
    try:
        print("Awaiting public key...")
        e, n = (int(x) for x in ClientSocket.recv(4096).decode()[1:-1].split(','))
        print("Received public key")

        print("Awaiting AES key...")
        key = pow(int.from_bytes(ClientSocket.recv(4096), 'big'), e, n).to_bytes(32, 'big')
        print(f"Received AES key:\n{key}")

        print("Awaiting file request...")
        while True:
            C = RecievePacket(ClientSocket)
            data = DecryptCTR(C, key).decode()
            

            if data == b'exit':
                break

            print('Received: ', data)
            manageFileRequest(ClientSocket, data, key)

        ClientSocket.close()
        print('Client disconnected: ', clientAddress)
    except Exception as e:
        print(e)

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.bind(('', 8080))
ServerSocket.listen()
print("[INIT] Server running on port 8080")

while True:
    ClientSocket, addr = ServerSocket.accept()
    manageThread = threading.Thread(target=manageClient, args=(ClientSocket, addr))
    manageThread.start()