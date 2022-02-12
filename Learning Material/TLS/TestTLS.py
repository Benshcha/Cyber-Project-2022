import socket, ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

bindsocket = socket.socket()
bindsocket.bind(('', 443))
bindsocket.listen(5)
print("Server is running...")

def deal_with_client(connstream):
    data = connstream.recv(1024)
    # empty data means the client is finished with us
    while data:
        print(data)
        data = connstream.recv(1024)

while True:
    try:
        newsocket, fromaddr = bindsocket.accept()
        connstream = context.wrap_socket(newsocket, server_side=True)
        print("Connection from: ", fromaddr)
        deal_with_client(connstream)
    except Exception as e:
        print(e)
