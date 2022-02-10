from multiprocessing.connection import Client
from Ex5 import *
import socket, json, os

ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ClientSocket.connect(('localhost' , 8080))

try:

    print("[INIT] Connected to server")
    print("Creating RSA keys...")
    e, d, n = generateKeys()
    publicKey = (e, n)
    privateKey = (d, n)

    ClientSocket.send(str(publicKey).encode())

    print("Generating AES key...")
    key = os.urandom(32)

    print("Sending AES key...")
    ClientSocket.send(pow(int.from_bytes(key, 'big'), d, n).to_bytes(32, 'big'))
    print(f"AES key sent\n{key}")    


    while True:
        msg = input('Enter file name: ')
        if msg == 'exit':
            break

        ClientSocket.send(EncryptCTR(msg.encode(), key))
        resp = RecievePacket(ClientSocket)

        if resp == b"1":
            print("error")
        else:
            DecData = DecryptCTR(resp, key)
            with open("Recieved Msg-" + msg, 'wb') as file:
                file.write(DecData)

except Exception as e:
    # print(e)
    raise e

