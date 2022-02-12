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

    print("Sending public key...")
    ClientSocket.send(str(publicKey).encode())

    print("Generating AES key...")
    key = np.random.bytes(16)

    print("Sending AES key...")
    EncKey = RSAEncrypt(key, *privateKey)
    ClientSocket.send(EncKey)
    DecKey = RSADecrypt(EncKey, *publicKey)
    print(f"AES key sent")    

    while True:
        msg = input('Enter file name: ')
        if msg == 'exit':
            break

        ClientSocket.send(EncryptCTR(msg.encode(), key))
        resp = RecievePacket(ClientSocket)
        Data = DecryptCTR(resp, key)

        if Data == b"1":
            print("Error!")
        else:
            with open("Recieved Msg-" + msg, 'wb') as file:
                file.write(Data)

except Exception as e:
    # print(e)
    raise e

